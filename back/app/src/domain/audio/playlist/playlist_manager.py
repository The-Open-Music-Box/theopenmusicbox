# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Consolidated playlist manager implementation."""

import asyncio
import time
import threading
from typing import Optional, Dict, Any
from pathlib import Path

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track

from ..protocols.audio_backend_protocol import AudioBackendProtocol
from ..protocols.playlist_manager_protocol import PlaylistManagerProtocol
from ..protocols.event_bus_protocol import EventBusProtocol

logger = get_logger(__name__)


class PlaylistManager(PlaylistManagerProtocol):
    """Consolidated playlist manager combining all previous implementations.

    This manager handles:
    - Playlist loading and playback control
    - Track sequencing and auto-advance
    - State management and position tracking
    - Event notifications
    """

    def __init__(self, backend: AudioBackendProtocol, event_bus: Optional[EventBusProtocol] = None):
        """Initialize the playlist manager.

        Args:
            backend: Audio backend for playback operations
            event_bus: Optional event bus for notifications
        """
        self._backend = backend
        self._event_bus = event_bus

        # Playlist state
        self._current_playlist: Optional[Playlist] = None
        self._current_track: Optional[Track] = None
        self._current_track_index = 0

        # Playback state
        self._is_playing = False
        self._is_paused = False
        self._position_seconds = 0.0
        self._track_start_time: Optional[float] = None

        # Auto-advance monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_stop_event = threading.Event()
        self._last_backend_busy = False
        self._auto_advance_enabled = True

        # Thread safety
        self._state_lock = threading.RLock()

        logger.log(LogLevel.INFO, f"PlaylistManager initialized with {type(backend).__name__}")

    # === Playlist Operations ===

    @handle_errors("set_playlist")
    def set_playlist(self, playlist: Playlist) -> bool:
        """Load and start playing a playlist."""
        with self._state_lock:
            # Stop any current playback
            self._stop_monitoring()
            self._backend.stop()
            # Validate playlist
            if not playlist or not playlist.tracks:
                logger.log(LogLevel.WARNING, "Cannot set empty playlist")
                return False
            # Set new playlist
            self._current_playlist = playlist
            self._current_track_index = 0
            self._is_playing = False
            self._is_paused = False
            # Start playing first track
            success = self._play_track_by_index(0)
            if success:
                self._start_monitoring()
                logger.log(
                    LogLevel.INFO,
                    f"✅ Playlist loaded: {playlist.title} ({len(playlist.tracks)} tracks)",
                )
            else:
                logger.log(LogLevel.ERROR, f"Failed to start playlist: {playlist.title}")
            return success

    def play_track_by_number(self, track_number: int) -> bool:
        """Play a specific track by number (1-based)."""
        with self._state_lock:
            if not self._current_playlist:
                logger.log(LogLevel.WARNING, "No playlist loaded")
                return False

            # Convert to 0-based index
            track_index = track_number - 1
            if track_index < 0 or track_index >= len(self._current_playlist.tracks):
                logger.log(LogLevel.WARNING, f"Invalid track number: {track_number}")
                return False

            return self._play_track_by_index(track_index)

    def next_track(self) -> bool:
        """Advance to next track."""
        with self._state_lock:
            if not self._current_playlist:
                logger.log(LogLevel.WARNING, "No playlist loaded")
                return False

            next_index = self._current_track_index + 1
            if next_index >= len(self._current_playlist.tracks):
                logger.log(LogLevel.INFO, "🔚 End of playlist reached (manual next)")
                self.stop()
                return False

            success = self._play_track_by_index(next_index)
            if success:
                logger.log(LogLevel.INFO, f"⏭️ Manually advanced to track {next_index + 1}")

            return success

    def previous_track(self) -> bool:
        """Go to previous track."""
        with self._state_lock:
            if not self._current_playlist:
                logger.log(LogLevel.WARNING, "No playlist loaded")
                return False

            prev_index = self._current_track_index - 1
            if prev_index < 0:
                logger.log(LogLevel.INFO, "Already at first track")
                return False

            success = self._play_track_by_index(prev_index)
            if success:
                logger.log(LogLevel.INFO, f"⏮️ Went back to track {prev_index + 1}")

            return success

    # === Playback Control ===

    def pause(self) -> bool:
        """Pause current playback."""
        with self._state_lock:
            if not self._is_playing:
                return False

            success = self._backend.pause()
            if success:
                self._is_playing = False
                self._is_paused = True
                # Capture current position
                if self._track_start_time:
                    self._position_seconds = time.time() - self._track_start_time
                logger.log(LogLevel.INFO, "⏸️ Playback paused")

            return success

    def resume(self) -> bool:
        """Resume paused playback."""
        with self._state_lock:
            if not self._is_paused:
                return False

            success = self._backend.resume()
            if success:
                self._is_playing = True
                self._is_paused = False
                # Adjust start time for position tracking
                if self._position_seconds > 0:
                    self._track_start_time = time.time() - self._position_seconds
                else:
                    self._track_start_time = time.time()
                logger.log(LogLevel.INFO, "▶️ Playback resumed")

            return success

    def stop(self) -> bool:
        """Stop playback."""
        with self._state_lock:
            self._stop_monitoring()
            success = self._backend.stop()

            if success:
                self._is_playing = False
                self._is_paused = False
                self._position_seconds = 0.0
                self._track_start_time = None
                logger.log(LogLevel.INFO, "⏹️ Playback stopped")

            return success

    # === State Access ===

    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        with self._state_lock:
            return self._is_playing

    @property
    def is_paused(self) -> bool:
        """Check if currently paused."""
        with self._state_lock:
            return self._is_paused

    @property
    def current_playlist(self) -> Optional[Playlist]:
        """Get current playlist."""
        with self._state_lock:
            return self._current_playlist

    @property
    def current_track(self) -> Optional[Track]:
        """Get current track."""
        with self._state_lock:
            return self._current_track

    @property
    def current_track_index(self) -> int:
        """Get current track index (0-based)."""
        with self._state_lock:
            return self._current_track_index

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        with self._state_lock:
            if self._is_playing and self._track_start_time:
                # Calculate real-time position
                elapsed = time.time() - self._track_start_time
                # Try to get backend position for accuracy
                try:
                    backend_pos = self._backend.get_position()
                    if backend_pos > 0 and abs(backend_pos - elapsed) < 2.0:
                        return backend_pos
                except:
                    pass
                return elapsed
            elif self._is_paused:
                return self._position_seconds
            else:
                return 0.0

    def get_playlist_info(self) -> Dict[str, Any]:
        """Get current playlist information."""
        with self._state_lock:
            if not self._current_playlist:
                return {}

            return {
                "playlist_id": getattr(self._current_playlist, "id", None),
                "title": self._current_playlist.title,
                "track_count": len(self._current_playlist.tracks),
                "current_track_index": self._current_track_index,
                "can_next": self._current_track_index < len(self._current_playlist.tracks) - 1,
                "can_prev": self._current_track_index > 0,
            }

    def get_track_info(self) -> Dict[str, Any]:
        """Get current track information."""
        with self._state_lock:
            if not self._current_track:
                return {}

            return {
                "track_id": getattr(self._current_track, "id", None),
                "track_number": getattr(
                    self._current_track, "track_number", self._current_track_index + 1
                ),
                "title": self._current_track.title,
                "filename": self._current_track.filename,
                "duration_sec": (
                    getattr(self._current_track, "duration_ms", 0) / 1000.0
                    if getattr(self._current_track, "duration_ms", 0)
                    else 0.0
                ),
                "artist": getattr(self._current_track, "artist", None),
                "album": getattr(self._current_track, "album", None),
            }

    # === Internal Implementation ===

    @handle_errors("_play_track_by_index")
    def _play_track_by_index(self, track_index: int) -> bool:
        """Play a specific track by index (internal method)."""
        if not self._current_playlist or track_index >= len(self._current_playlist.tracks):
            return False

        track = self._current_playlist.tracks[track_index]

        # Stop current playback
        self._backend.stop()
        # Get track file path
        file_path = self._get_track_file_path(track)
        if not file_path or not Path(file_path).exists():
            logger.log(LogLevel.ERROR, f"Track file not found: {file_path}")
            return False
        # Start new track
        success = self._backend.play_file(file_path)
        if success:
            self._current_track_index = track_index
            self._current_track = track
            self._is_playing = True
            self._is_paused = False
            self._track_start_time = time.time()
            self._position_seconds = 0.0
            logger.log(LogLevel.INFO, f"🎵 Playing track {track_index + 1}: {track.title}")
            # Fire event if event bus available
            if self._event_bus:
                from ..events.audio_events import TrackStartedEvent

                try:
                    # Try to create async task if event loop exists
                    asyncio.create_task(
                        self._event_bus.publish(TrackStartedEvent("PlaylistManager", file_path))
                    )
                except RuntimeError:
                    # No event loop, skip async event
                    logger.log(LogLevel.DEBUG, "Skipping async event - no event loop")

        return success

    def _get_track_file_path(self, track: Track) -> str:
        """Get the file path for a track."""
        # Try various path attributes
        if hasattr(track, "file_path") and track.file_path:
            file_path = str(track.file_path)
            # If already absolute path, use it directly
            if Path(file_path).is_absolute():
                return file_path
            # Otherwise, make it absolute using config.upload_folder
            from app.src.config import config

            return str(Path(config.upload_folder) / file_path)
        elif hasattr(track, "path") and track.path:
            path = str(track.path)
            if Path(path).is_absolute():
                return path
            from app.src.config import config

            return str(Path(config.upload_folder) / path)
        elif hasattr(track, "filename") and track.filename:
            # If filename is a full path, use it directly
            if "/" in track.filename or "\\" in track.filename:
                if Path(track.filename).is_absolute():
                    return track.filename
                from app.src.config import config

                return str(Path(config.upload_folder) / track.filename)
            # Otherwise, assume it's in uploads directory
            from app.src.config import config

            return str(Path(config.upload_folder) / track.filename)
        else:
            logger.log(LogLevel.ERROR, f"No valid file path found for track: {track.title}")
            return ""

    def _start_monitoring(self):
        """Start auto-advance monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._monitor_stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.log(LogLevel.DEBUG, "Auto-advance monitoring started")

    def _stop_monitoring(self):
        """Stop auto-advance monitoring thread."""
        self._monitor_stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        logger.log(LogLevel.DEBUG, "Auto-advance monitoring stopped")

    @handle_errors("_monitor_loop")
    def _monitor_loop(self):
        """Monitor loop for auto-advance detection."""
        while not self._monitor_stop_event.is_set():
            with self._state_lock:
                # Only monitor for auto-advance when actually playing (not paused)
                if self._is_playing and not self._is_paused and self._auto_advance_enabled:
                    backend_busy = self._backend.is_busy
                    # Detect transition from busy to not busy (track ended)
                    # But only when we're still supposed to be playing (not paused)
                    if self._last_backend_busy and not backend_busy and not self._is_paused:
                        logger.log(LogLevel.INFO, "🔚 Track end detected, triggering auto-advance")
                        self._auto_advance_to_next()
                    self._last_backend_busy = backend_busy
                elif self._is_paused:
                    # When paused, reset the busy state tracking to avoid false triggers
                    self._last_backend_busy = False
            # Check every 100ms for responsive auto-advance
            self._monitor_stop_event.wait(0.1)

    @handle_errors("_auto_advance_to_next")
    def _auto_advance_to_next(self):
        """Automatically advance to next track (internal method)."""
        if not self._current_playlist:
            return

        next_index = self._current_track_index + 1
        if next_index >= len(self._current_playlist.tracks):
            logger.log(LogLevel.INFO, "🔚 End of playlist reached (auto-advance)")
            self.stop()

            # Fire playlist finished event
            if self._event_bus:
                from ..events.audio_events import PlaylistFinishedEvent

                try:
                    # Try to create async task if event loop exists
                    asyncio.create_task(
                        self._event_bus.publish(
                            PlaylistFinishedEvent(
                                "PlaylistManager",
                                playlist_id=getattr(self._current_playlist, "id", None),
                                playlist_title=self._current_playlist.title,
                                tracks_played=self._current_track_index + 1,
                            )
                        )
                    )
                except RuntimeError:
                    # No event loop, skip async event
                    logger.log(
                        LogLevel.DEBUG, "Skipping async playlist finished event - no event loop"
                    )
            return

        success = self._play_track_by_index(next_index)
        if success:
            logger.log(LogLevel.INFO, f"🔄 Auto-advanced to track {next_index + 1}")

    def cleanup(self):
        """Clean up resources."""
        logger.log(LogLevel.INFO, "PlaylistManager cleanup started")
        self._stop_monitoring()
        logger.log(LogLevel.INFO, "PlaylistManager cleanup completed")
