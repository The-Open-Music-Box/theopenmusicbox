# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Audio Controller for TheOpenMusicBox.

This module provides the AudioController class that manages audio playback operations,
volume control, and coordinates with the underlying audio service. It serves as the
main interface for all audio-related operations in the application.
"""

import time
from pathlib import Path
from typing import Dict, Any

from app.src.config import config
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors
from app.src.services.file_path_resolver import FilePathResolver

logger = get_logger(__name__)


class AudioController:
    """Controller for audio playback operations and volume management.

    This class provides a high-level interface for audio control operations,
    including playback control (play, pause, stop, next, previous), volume management,
    and state synchronization with the underlying audio service.
    """

    def __init__(self, audio_service=None, config=None, state_manager=None):
        """Initialize the AudioController.

        Args:
            audio_service: The underlying audio service for hardware operations
            config: Configuration object with audio settings
            state_manager: StateManager for broadcasting state changes
        """
        self._audio_service = audio_service
        self._config = config or {}
        self._state_manager = state_manager
        self._current_volume = 50  # Default volume
        self._last_volume_change = 0  # For debouncing
        self._debounce_interval = 0.2  # 200ms debounce

        # Simplified state tracking - single source of truth
        self._paused_position = 0.0  # Store position when paused
        self._last_action = "stopped"  # Track last action: "playing", "paused", "stopped"

        # Handle AudioEngine by extracting the underlying backend for direct access
        self._backend = None
        self._playlist_manager = None
        if audio_service:
            # Check if this is an AudioEngine with a backend and playlist manager
            if hasattr(audio_service, "_backend") and audio_service._backend:
                self._backend = audio_service._backend
                # Also get the playlist manager for proper state management
                if hasattr(audio_service, "_playlist_manager"):
                    self._playlist_manager = audio_service._playlist_manager
                    logger.log(
                        LogLevel.INFO,
                        f"AudioController using playlist manager: {type(self._playlist_manager).__name__}",
                    )
                logger.log(
                    LogLevel.INFO,
                    f"AudioController using underlying backend: {type(self._backend).__name__}",
                )
            else:
                self._backend = audio_service

        logger.log(
            LogLevel.INFO,
            f"AudioController initialized with audio_service: {type(audio_service).__name__ if audio_service else 'None'}",
        )

        # Debug audio service availability
        if self._backend:
            logger.log(
                LogLevel.DEBUG, f"Backend has pause method: {hasattr(self._backend, 'pause')}"
            )
            logger.log(
                LogLevel.DEBUG,
                f"Backend is_available: {getattr(self._backend, 'is_available', lambda: 'method not found')()}",
            )
        else:
            logger.log(LogLevel.WARNING, "AudioController initialized with no backend")

        # Set up state manager reference in audio service if possible
        if audio_service and hasattr(audio_service, "_state_manager"):
            audio_service._state_manager = state_manager

    @property
    def audio_service(self):
        """Get the underlying audio service.

        Returns:
            The audio service instance or None if not available
        """
        return self._audio_service

    def is_available(self) -> bool:
        """Check if audio service is available."""
        return self._backend is not None and getattr(self._backend, "is_available", lambda: True)()

    @handle_errors("play")
    def play(self, track=None) -> bool:
        """Start audio playback.

        Args:
            track: Track to play (optional for compatibility)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.log(
                LogLevel.WARNING,
                "Audio service not available for play operation - simulating success",
            )
            return True  # Simulate success for development

        if hasattr(self._audio_service, "play"):
            # Try different signatures for compatibility
            if track is not None:
                self._audio_service.play(track)
            else:
                self._audio_service.play()

    @handle_errors("pause")
    def pause(self) -> bool:
        """Pause audio playback.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for pause operation")
            return False

        # Use PlaylistManager if available for proper state management
        if self._playlist_manager and hasattr(self._playlist_manager, "pause"):
            result = self._playlist_manager.pause()
            if result is not False:
                logger.log(LogLevel.INFO, "Audio playback paused (via PlaylistManager)")
                self._last_action = "paused"
                return True
        # Fallback to backend directly
        elif hasattr(self._backend, "pause"):
            result = self._backend.pause()
            # Some backends return bool, others don't - assume success if no exception
            if result is not False:
                # Capture paused position if available
                if hasattr(self._backend, "get_position"):
                    self._paused_position = float(self._backend.get_position())

    @handle_errors("resume")
    def resume(self) -> bool:
        """Resume audio playback from paused state if supported."""
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for resume operation")
            return False
        # Use PlaylistManager if available for proper state management
        if self._playlist_manager and hasattr(self._playlist_manager, "resume"):
            result = self._playlist_manager.resume()
            if result is not False:
                logger.log(LogLevel.INFO, "Audio playback resumed (via PlaylistManager)")
                self._last_action = "playing"
                return True
        # Fallback to backend directly
        elif hasattr(self._backend, "resume"):
            result = self._backend.resume()
            if result is not False:
                logger.log(LogLevel.INFO, "Audio playback resumed (direct backend)")
                self._last_action = "playing"
                return True
        else:
            # Fallback: call play on current track or restart playlist
            if hasattr(self, "_current_playlist") and self._current_playlist:
                return self.start_current_playlist()
            logger.log(LogLevel.WARNING, "Audio backend does not support resume operation")
            return False

    @handle_errors("stop")
    def stop(self) -> bool:
        """Stop audio playback.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for stop operation")
            return False

        if hasattr(self._backend, "stop"):
            result = self._backend.stop()
            if result is not False:
                logger.log(LogLevel.INFO, "Audio playback stopped")
                self._last_action = "stopped"
                return True
        else:
            logger.log(LogLevel.WARNING, "Audio backend does not support stop operation")
            return False

    @handle_errors("toggle_play_pause")
    def toggle_play_pause(self) -> bool:
        """Toggle between play and pause states.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for toggle operation")
            return False

        if self.is_playing():
            return self.pause()
        else:
            # Prefer resume if paused, otherwise restart current playlist
            ok = self.resume()
            if not ok:
                ok = self.start_current_playlist()
            return ok

    @handle_errors("next_track")
    def next_track(self) -> bool:
        """Skip to next track.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for next track operation")
            return False

        # Use PlaylistManager for proper track sequencing
        if self._playlist_manager and hasattr(self._playlist_manager, "next_track"):
            result = self._playlist_manager.next_track()
            if result is not False:
                logger.log(LogLevel.INFO, "Skipped to next track (via PlaylistManager)")
                return True
            else:
                logger.log(
                    LogLevel.INFO, "Cannot skip to next track (end of playlist or not available)"
                )
                return False
        # Fallback to backend directly (limited functionality)
        elif hasattr(self._backend, "next_track"):
            result = self._backend.next_track()
            # Some backends return None/void, assume success if no exception
            logger.log(LogLevel.INFO, "Skipped to next track (direct backend)")
            return True
        else:
            logger.log(LogLevel.WARNING, "Audio backend does not support next track operation")
            return False

    @handle_errors("previous_track")
    def previous_track(self) -> bool:
        """Skip to previous track.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for previous track operation")
            return False

        # Use PlaylistManager for proper track sequencing
        if self._playlist_manager and hasattr(self._playlist_manager, "previous_track"):
            result = self._playlist_manager.previous_track()
            if result is not False:
                logger.log(LogLevel.INFO, "Skipped to previous track (via PlaylistManager)")
                return True
            else:
                logger.log(
                    LogLevel.INFO,
                    "Cannot skip to previous track (beginning of playlist or not available)",
                )
                return False
        # Fallback to backend directly (limited functionality)
        elif hasattr(self._backend, "previous_track"):
            result = self._backend.previous_track()
            # Some backends return None/void, assume success if no exception
            logger.log(LogLevel.INFO, "Skipped to previous track (direct backend)")
            return True
        else:
            logger.log(LogLevel.WARNING, "Audio backend does not support previous track operation")
            return False

    @handle_errors("auto_advance_to_next")
    def auto_advance_to_next(self) -> bool:
        """Automatically advance to next track (end-of-track detection).

        This method is called by TrackProgressService when a track ends naturally,
        distinct from manual next_track() calls by users.

        Returns:
            bool: True if advanced successfully, False if end of playlist
        """
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for auto-advance")
            return False

        # Use the underlying audio service's auto-advance method
        if hasattr(self._audio_service, "auto_advance_to_next"):
            success = self._audio_service.auto_advance_to_next()
            # HARMONISATION: No need to sync _current_track_index anymore
            # AudioPlayer is now the single source of truth for track state
            if success:
                logger.log(LogLevel.INFO, "✅ Auto-advanced to next track successfully")
            else:
                logger.log(LogLevel.INFO, "🔚 End of playlist reached")
            return success
        else:
            logger.log(
                LogLevel.WARNING,
                f"Audio service ({type(self._audio_service).__name__}) doesn't support auto-advance",
            )
            return False

    @handle_errors("seek_to")
    def seek_to(self, position_ms: int) -> bool:
        """Seek current playback position.

        Args:
            position_ms: Target position in milliseconds

        Returns:
            bool: True if successful
        """
        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for seek operation")
            return False
        # Convert ms to seconds
        pos_seconds = max(0.0, float(position_ms) / 1000.0)
        # Use backend directly for seeking
        if hasattr(self._backend, "set_position"):
            result = self._backend.set_position(pos_seconds)
            if result is not False:
                # Update position after successful seek
                if hasattr(self._backend, "is_playing"):
                    is_playing = self._backend.is_playing
                    if callable(is_playing):
                        is_playing = is_playing()
                    if not is_playing:
                        # Store position for paused state
                        self._paused_position = pos_seconds

    @handle_errors("is_playing")
    def is_playing(self) -> bool:
        """Check if audio is currently playing.

        Delegates directly to audio service for current state.

        Returns:
            bool: True if playing, False otherwise
        """
        if not self.is_available():
            return False

        # Query backend directly for single source of truth
        if hasattr(self._backend, "is_playing"):
            attr = getattr(self._backend, "is_playing")
            return attr() if callable(attr) else bool(attr)
        else:
            # Fallback to last known action if backend doesn't provide state
            return self._last_action == "playing"

    def _start_playback_tracking(self) -> None:
        """Start playback tracking for position calculation.

        This method is called when a playlist starts playing to enable
        proper state tracking.
        """
        # This is now a no-op since tracking is handled by TrackProgressService
        # Keep method for backward compatibility with routes
        logger.log(LogLevel.DEBUG, "Playback tracking started (handled by TrackProgressService)")

    @handle_errors("set_volume")
    def set_volume(self, volume: int) -> bool:
        """Set audio volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if successful, False otherwise
        """
        if not (0 <= volume <= 100):
            logger.log(LogLevel.WARNING, f"Invalid volume level: {volume}. Must be 0-100")
            return False

        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for volume operation")
            return False

        if hasattr(self._backend, "set_volume"):
            result = self._backend.set_volume(volume)
            if result is not False:
                self._current_volume = volume
                logger.log(LogLevel.INFO, f"Volume set to {volume}")
                return True
        else:
            logger.log(LogLevel.WARNING, "Audio backend does not support volume control")
            return False

    @handle_errors("get_current_volume")
    def get_current_volume(self) -> int:
        """Get current volume level.

        Returns:
            int: Current volume level (0-100)
        """
        if self.is_available() and hasattr(self._audio_service, "get_volume"):
            service_volume = self._audio_service.get_volume()
            if service_volume is not None:
                self._current_volume = service_volume
        return self._current_volume

    def volume_up(self, step: int = 5) -> bool:
        """Increase volume by specified step.

        Args:
            step: Volume increase step (default: 5)

        Returns:
            bool: True if successful, False otherwise
        """
        current_time = time.time()
        if current_time - self._last_volume_change < self._debounce_interval:
            logger.log(LogLevel.DEBUG, "Volume change debounced")
            return False

        new_volume = min(100, self._current_volume + step)
        if new_volume == self._current_volume:
            logger.log(LogLevel.DEBUG, "Volume already at maximum")
            return False

        success = self.set_volume(new_volume)
        if success:
            self._last_volume_change = current_time
        return success

    def volume_down(self, step: int = 5) -> bool:
        """Decrease volume by specified step.

        Args:
            step: Volume decrease step (default: 5)

        Returns:
            bool: True if successful, False otherwise
        """
        current_time = time.time()
        if current_time - self._last_volume_change < self._debounce_interval:
            logger.log(LogLevel.DEBUG, "Volume change debounced")
            return False

        new_volume = max(0, self._current_volume - step)
        if new_volume == self._current_volume:
            logger.log(LogLevel.DEBUG, "Volume already at minimum")
            return False

        success = self.set_volume(new_volume)
        if success:
            self._last_volume_change = current_time
        return success


    def _load_playlist_with_validation(self, playlist_id: str) -> bool:
        """Internal method to load and validate playlist."""
        if not hasattr(self._audio_service, "set_playlist"):
            logger.log(LogLevel.WARNING, "Audio service does not support playlist loading")
            return False

        # Get playlist data
        playlist = self._get_playlist_data(playlist_id)
        if not playlist:
            return False

        # Resolve and validate track paths
        valid_tracks = self._resolve_track_paths(playlist)
        if not valid_tracks:
            logger.log(LogLevel.ERROR, f"No valid tracks found in playlist: {playlist.title}")
            return False

        # Update playlist and controller state
        playlist.tracks = valid_tracks
        self._update_controller_state(playlist_id, playlist)

        logger.log(
            LogLevel.INFO, f"Playlist {playlist_id} loaded with {len(valid_tracks)} valid tracks"
        )
        return True

    def _get_playlist_data(self, playlist_id: str):
        """Get playlist data from service."""
        # Use application service from pure domain architecture
        from app.src.application.services.playlist_application_service import playlist_app_service

        # Get playlist using application service
        try:
            import asyncio

            # Since this is a sync method calling async, we need to handle it properly
            # For now, return None to avoid breaking the system
            playlist = None
            logger.log(
                LogLevel.WARNING,
                "_get_playlist_data needs async refactoring for pure domain architecture",
            )
        except Exception:
            playlist = None
        if not playlist:
            logger.log(LogLevel.ERROR, f"Playlist {playlist_id} not found")
            return None
        return playlist

    def _resolve_track_paths(self, playlist):
        """Resolve track paths using FilePathResolver service."""

        # Initialize path resolver
        uploads_dir = Path(config.upload_folder)
        path_resolver = FilePathResolver(uploads_dir)

        valid_tracks = []
        for track in playlist.tracks:
            # First try existing path
            if self._track_has_valid_path(track):
                valid_tracks.append(track)
                continue

            # Use path resolver service
            resolved_path = path_resolver.resolve_track_path(track, playlist.title)
            if resolved_path:
                # Update track with resolved path
                if hasattr(track, "path"):
                    track.path = resolved_path
                if hasattr(track, "filename"):
                    track.filename = str(resolved_path)
                valid_tracks.append(track)
                logger.log(LogLevel.INFO, f"Resolved track path: {resolved_path}")
            else:
                logger.log(
                    LogLevel.WARNING,
                    f"Track file not found: {getattr(track, 'filename', 'unknown')}",
                )

        return valid_tracks

    def _track_has_valid_path(self, track) -> bool:
        """Check if track already has a valid path."""

        if hasattr(track, "path") and track.path:
            return Path(track.path).exists()
        elif hasattr(track, "filename") and track.filename:
            return Path(track.filename).exists()
        return False

    def _update_controller_state(self, playlist_id: str, playlist):
        """Update controller state with loaded playlist."""
        self._current_playlist_id = playlist_id
        self._current_playlist = playlist

    # NOTE: Playback tracking methods removed - position now handled directly by audio service

    def _is_supported_format(self, filename: str) -> bool:
        """Check if the audio file format is supported.

        Args:
            filename: The filename to check

        Returns:
            bool: True if format is supported, False otherwise
        """
        if not filename:
            return False

        supported_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma"}
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        return extension in supported_extensions

    @handle_errors("play_track")
    def play_track(self, track_number: int) -> bool:
        """Play a specific track by number.

        Args:
            track_number: Track number to play

        Returns:
            bool: True if successful, False otherwise
        """
        if track_number < 1:
            logger.log(LogLevel.WARNING, f"Invalid track number: {track_number}")
            return False

        if not self.is_available():
            logger.log(LogLevel.WARNING, "Audio service not available for track playback")
            return False

        if hasattr(self._audio_service, "play_track"):
            self._audio_service.play_track(track_number)
            logger.log(LogLevel.INFO, f"Playing track {track_number}")
            return True
        else:
            logger.log(LogLevel.WARNING, "Audio service does not support track selection")
            return False

    @handle_errors("handle_playback_control")
    async def handle_playback_control(self, action: str) -> Dict[str, Any]:
        """Handle playback control commands for API routes.

        Args:
            action: Playback action (play, pause, stop, next, previous, toggle)

        Returns:
            Dict containing operation result and current state
        """
        success = False
        current_state = "unknown"
        if action == "play":
            # Prefer resume if paused; otherwise start current playlist
            if not self.is_playing():
                # Try resume first
                success = self.resume()
                if not success:
                    # Attempt to start current playlist
                    success = self.start_current_playlist()
            else:
                success = True
            current_state = "playing" if success else "error"
        elif action == "pause":
            success = self.pause()
            current_state = "paused" if success else "error"
        elif action == "stop":
            success = self.stop()
            current_state = "stopped" if success else "error"
        elif action == "next":
            success = self.next_track()
            current_state = "playing" if success else "error"
        elif action == "previous":
            success = self.previous_track()
            current_state = "playing" if success else "error"
        elif action == "toggle":
            success = self.toggle_play_pause()
            current_state = "playing" if self.is_playing() else "paused"
        else:
            logger.log(LogLevel.WARNING, f"Unknown playback action: {action}")
            return {
                "status": "error",
                "message": f"Unknown action: {action}",
                "timestamp": time.time(),
            }
        result = {
            "status": "success" if success else "error",
            "action": action,
            "state": current_state,
            "volume": self.get_current_volume(),
            "timestamp": time.time(),
        }
        # Add playlist info if available
        playlist_info = self.get_current_playlist_info()
        if playlist_info:
            # Get current position for more accurate state
            current_position_sec = self._calculate_current_position()
            result.update(
                {
                    "playlist_id": playlist_info.get("playlist_id"),
                    "track_id": (
                        playlist_info.get("current_track", {}).get("id")
                        if playlist_info.get("current_track")
                        else None
                    ),
                    "position_ms": int(current_position_sec * 1000),
                    "can_prev": playlist_info.get("can_prev", False),
                    "can_next": playlist_info.get("can_next", False),
                }
            )
        return result

    @handle_errors("get_playback_status")
    async def get_playback_status(self) -> Dict[str, Any]:
        """Get current playback status for API routes.

        Returns:
            Dict containing current playback state information
        """
        is_playing = self.is_playing()
        current_time_sec = 0.0
        duration_sec = 0.0
        duration_ms = 0  # Initialize duration_ms to prevent UnboundLocalError
        track_number = None
        playlist_id = None
        track_id = None

        # HARMONISATION: Use AudioPlayer as single source of truth for track info
        if self._audio_service and hasattr(self._audio_service, "get_current_track_info"):
            track_info = self._audio_service.get_current_track_info()
            track_number = track_info.get("track_number")
            track_id = track_info.get("track_id")
            # Use milliseconds consistently - get duration_ms or convert from duration_sec
            duration_ms = track_info.get("duration_ms", 0)
            if duration_ms == 0 and track_info.get("duration_sec"):
                duration_ms = int(track_info.get("duration_sec", 0) * 1000)
            logger.log(
                LogLevel.DEBUG,
                f"Track info from AudioPlayer: track_number={track_number}, duration_ms={duration_ms}ms, track_id={track_id}",
            )

        # Get current position in milliseconds
        current_time_sec = self._calculate_current_position()
        current_time_ms = int(current_time_sec * 1000)

        # Get playlist info
        playlist_info = self.get_current_playlist_info()
        if playlist_info:
            playlist_id = playlist_info.get("playlist_id")

        # Build status response - unified milliseconds format
        status = {
            "is_playing": is_playing,
            "current_time": current_time_ms,  # Unified: milliseconds
            "duration": duration_ms,  # Unified: milliseconds
            "position_ms": current_time_ms,  # Consistent naming with frontend
            "duration_ms": duration_ms,  # Consistent naming with frontend
            "volume": self.get_current_volume(),
            "track_number": track_number,
            "track_id": track_id,
            "playlist_id": playlist_id,
            "state": "playing" if is_playing else "stopped",
            "timestamp": time.time(),
        }

        # Add navigation info if available
        if playlist_info:
            status.update(
                {
                    "can_prev": playlist_info.get("can_prev", False),
                    "can_next": playlist_info.get("can_next", False),
                }
            )

        return status

    @handle_errors("load_playlist_with_service")
    def load_playlist_with_service(self, playlist_id: str, playlist_service=None) -> bool:
        """Load a playlist for playback.

        Args:
            playlist_id: ID of the playlist to load
            playlist_service: Playlist application service instance to get playlist data

        Returns:
            bool: True if successful, False otherwise
        """
        if not playlist_service:
            logger.log(LogLevel.WARNING, "No playlist service provided")
            return False

        # Get playlist from service
        playlist = playlist_service.get_playlist(playlist_id)
        if not playlist:
            logger.log(LogLevel.ERROR, f"Playlist {playlist_id} not found")
            return False
        if not playlist.tracks:
            logger.log(LogLevel.WARNING, f"Playlist {playlist_id} is empty")
            return False
        # Store current playlist info for player state
        self._current_playlist_id = playlist_id
        self._current_playlist = playlist
        logger.log(
            LogLevel.INFO, f"Playlist {playlist_id} loaded with {len(playlist.tracks)} tracks"
        )
        return True

    @handle_errors("get_current_playlist_info")
    def get_current_playlist_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded playlist.

        NOTE: This method maintains controller's playlist state for UI purposes,
        but current track info comes from AudioPlayer (single source of truth).
        """
        # Get current track info from audio service (source of truth)
        current_track = None
        current_track_number = None
        if self._audio_service and hasattr(self._audio_service, "get_current_track_info"):
            track_info = self._audio_service.get_current_track_info()
            current_track_number = track_info.get("track_number")
            # Basic track info from service
            if track_info.get("track_id"):
                current_track = {
                    "id": track_info.get("track_id"),
                    "title": track_info.get("title") or f"Track {current_track_number}",
                    "filename": track_info.get("filename", "unknown"),
                }

        # Get playlist metadata from controller (for UI)
        playlist_info = {"current_track": current_track, "can_next": False, "can_prev": False}

        # Try to get playlist info from PlaylistManager first (more accurate)
        if self._playlist_manager and hasattr(self._playlist_manager, "get_playlist_info"):
            manager_info = self._playlist_manager.get_playlist_info()
            if manager_info:
                playlist_info.update(manager_info)
                # Override current_track with our track info if available
                if current_track:
                    playlist_info["current_track"] = current_track
                logger.log(
                    LogLevel.DEBUG,
                    f"Using PlaylistManager info: can_next={manager_info.get('can_next')}, can_prev={manager_info.get('can_prev')}",
                )
        # Fallback to controller's own playlist info
        elif hasattr(self, "_current_playlist") and self._current_playlist:
            playlist_info.update(
                {
                    "playlist_id": getattr(self, "_current_playlist_id", None),
                    "playlist_title": self._current_playlist.title,
                    "track_count": len(self._current_playlist.tracks),
                    "current_track_index": (
                        (current_track_number - 1) if current_track_number else 0
                    ),
                    "can_next": (
                        current_track_number < len(self._current_playlist.tracks)
                        if current_track_number
                        else False
                    ),
                    "can_prev": current_track_number > 1 if current_track_number else False,
                }
            )
            logger.log(
                LogLevel.DEBUG,
                f"Using AudioController fallback: can_next={playlist_info['can_next']}, can_prev={playlist_info['can_prev']}",
            )

        return playlist_info

    @handle_errors("start_current_playlist")
    def start_current_playlist(self) -> bool:
        """Start playing the currently loaded playlist from the beginning."""

        if not self._validate_current_playlist():
            return False

        return self._start_playlist_with_validation()

    def _validate_current_playlist(self) -> bool:
        """Validate that current playlist is ready for playback."""
        if not hasattr(self, "_current_playlist") or not self._current_playlist:
            logger.log(LogLevel.WARNING, "No playlist loaded")
            return False

        if not self._current_playlist.tracks:
            logger.log(LogLevel.WARNING, "Current playlist is empty")
            return False

        return True

    def _start_playlist_with_validation(self) -> bool:
        """Internal method to start playlist with track validation."""
        # Validate and resolve track paths (reuse existing logic)
        valid_tracks = self._resolve_track_paths(self._current_playlist)
        if not valid_tracks:
            logger.log(
                LogLevel.ERROR, f"No valid tracks found in playlist: {self._current_playlist.title}"
            )
            return False

        # Update playlist with valid tracks
        self._current_playlist.tracks = valid_tracks

        # Prefer hardware playlist-based playback when available
        if self._audio_service and hasattr(self._audio_service, "set_playlist"):
            return self._start_hardware_playlist()
        else:
            return self._start_fallback_playlist()

    def _start_hardware_playlist(self) -> bool:
        """Start playlist using hardware playlist support."""
        # CORRECTION CRITIQUE: Toujours utiliser set_playlist pour configurer toute la playlist
        logger.log(
            LogLevel.INFO,
            f"Loading playlist into audio service: {self._current_playlist.title} with {len(self._current_playlist.tracks)} tracks",
        )
        success = self._audio_service.set_playlist(self._current_playlist)

        if success:
            # IMPORTANT: Update state when playlist starts
            self._last_action = "playing"

            logger.log(
                LogLevel.INFO,
                f"✅ Playlist configurée avec succès: {self._current_playlist.title} avec {len(self._current_playlist.tracks)} tracks",
            )
            logger.log(LogLevel.INFO, f"🎯 AudioController state: is_playing()={self.is_playing()}")
            return True
        else:
            logger.log(
                LogLevel.ERROR, f"❌ Échec configuration playlist: {self._current_playlist.title}"
            )
            return False

    def _start_fallback_playlist(self) -> bool:
        """Fallback: Configure full playlist even if hardware lacks direct set_playlist support."""
        if hasattr(self._audio_service, "set_playlist"):
            logger.log(
                LogLevel.WARNING,
                "Audio service has set_playlist but hardware path failed, trying direct set_playlist",
            )
            success = self._audio_service.set_playlist(self._current_playlist)
            if success:
                # IMPORTANT: Update state when playlist starts
                self._last_action = "playing"

                logger.log(
                    LogLevel.INFO,
                    f"✅ Fallback réussi avec set_playlist: {self._current_playlist.title}",
                )
                return True

        # Vraiment dernier recours: jouer la première track mais configurer la progression
        logger.log(
            LogLevel.WARNING,
            "Utilisation du dernier recours: configuration manuelle de la playlist",
        )

        # Configurer manuellement la playlist dans l'audio service s'il a des propriétés internes
        if hasattr(self._audio_service, "_playlist"):
            self._audio_service._playlist = self._current_playlist
        if hasattr(self._audio_service, "_current_track"):
            self._audio_service._current_track = self._current_playlist.tracks[0]

        first_track = self._current_playlist.tracks[0]
        track_path = getattr(first_track, "path", None) or getattr(
            first_track, "filename", str(first_track)
        )
        success = self.play(track_path)

        if success:
            logger.log(
                LogLevel.INFO,
                f"⚠️️ Playlist démarrée en mode fallback manuel: {self._current_playlist.title} avec {len(self._current_playlist.tracks)} tracks",
            )
            logger.log(LogLevel.INFO, f"Première track: {track_path}")
            return True
        else:
            logger.log(
                LogLevel.ERROR, f"❌ Échec complet du fallback pour: {self._current_playlist.title}"
            )
            return False

    def _calculate_current_position(self) -> float:
        """Calculate current position in seconds.

        Returns:
            float: Current playback position in seconds
        """
        try:
            # Check if we have a stored paused position
            if hasattr(self, "_paused_position"):
                return float(self._paused_position)

            # Try to get position from audio service
            if self._audio_service and hasattr(self._audio_service, "get_position"):
                return float(self._audio_service.get_position())

            # Fallback to 0.0 if no position available
            return 0.0

        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error calculating current position: {e}")
            return 0.0
