# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

import time
from pathlib import Path
from typing import Any, Dict, Optional

from mutagen.mp3 import MP3

from app.src.module.audio.models import AudioState
from app.src.services.notification_service import PlaybackSubject
from app.src.config import config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

# MARK: - Audio State Manager Class


class AudioStateManager:
    """Manages audio playback state and track information."""

    # MARK: - Initialization
    def __init__(self):
        self._is_playing = False
        self._current_track = None
        self._playlist = None
        self._volume = config.audio.default_volume  # Use centralized config
        self._stream_start_time = 0
        self._paused_position = 0
        self._pause_time = 0
        self._audio_cache = {}  # Cache for track durations

    # MARK: - State Properties
    @property
    def is_playing(self) -> bool:
        """Return True if audio is currently playing."""
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        """Return True if player is paused but a track is loaded."""
        return not self._is_playing and self._current_track is not None

    @property
    def current_track(self) -> Optional[Track]:
        """Get the currently loaded track."""
        return self._current_track

    @property
    def playlist(self) -> Optional[Playlist]:
        """Get the current playlist."""
        return self._playlist

    @property
    def volume(self) -> int:
        """Get the current volume setting (0-100)."""
        return self._volume

    @property
    def current_position(self) -> float:
        """Get the current playback position in seconds."""
        if self._is_playing:
            return time.time() - self._stream_start_time
        elif self.is_paused:
            return self._paused_position
        return 0.0

    # MARK: - State Setters
    def set_playing(self, is_playing: bool) -> None:
        """Update the playing state."""
        self._is_playing = is_playing

        # Update timing information based on state change
        if is_playing:
            # If we're starting from a paused state, adjust for the pause duration
            if self._paused_position > 0:
                self._stream_start_time = time.time() - self._paused_position
            elif self._stream_start_time == 0:
                self._stream_start_time = time.time()
        else:
            # If we're pausing, save the current position
            if self._stream_start_time > 0:
                self._paused_position = time.time() - self._stream_start_time
                self._pause_time = time.time()

    def set_playlist(self, playlist: Playlist) -> None:
        """Set the current playlist."""
        self._playlist = playlist
        logger.log(
            LogLevel.INFO,
            f"Playlist set: {playlist.name} ({len(playlist.tracks)} tracks)",
        )

    def set_current_track(self, track: Track) -> None:
        """Set the current track."""
        self._current_track = track
        logger.log(LogLevel.INFO, f"Current track set: {track.title or track.filename}")

    # MARK: - Playlist Navigation
    def set_current_track_by_number(self, track_number: int) -> Optional[Track]:
        """Set the current track by its number in the playlist."""
        if not self._playlist or not self._playlist.tracks:
            logger.log(LogLevel.WARNING, "No playlist or empty playlist")
            return None

        track = next(
            (t for t in self._playlist.tracks if t.number == track_number), None
        )
        if not track:
            logger.log(
                LogLevel.WARNING, f"Track number {track_number} not found in playlist"
            )
            return None

        self.set_current_track(track)
        return track

    def get_next_track_number(self) -> Optional[int]:
        """Get the next track number in the playlist."""
        if not self._current_track or not self._playlist or not self._playlist.tracks:
            return None

        next_number = self._current_track.number + 1
        if next_number <= len(self._playlist.tracks):
            return next_number
        return None

    def get_previous_track_number(self) -> Optional[int]:
        """Get the previous track number in the playlist."""
        if not self._current_track or not self._playlist or not self._playlist.tracks:
            return None

        prev_number = self._current_track.number - 1
        if prev_number >= 1:  # Track numbers are 1-based
            return prev_number
        return None

    # MARK: - State Management
    def reset_playback_state(self) -> None:
        """Reset all playback state variables."""
        self._is_playing = False
        self._stream_start_time = 0
        self._paused_position = 0
        self._pause_time = 0

    def clear_all(self) -> None:
        """Clear all state including current track and playlist."""
        self.reset_playback_state()
        self._current_track = None
        self._playlist = None

    def set_volume(self, volume: int) -> None:
        """Set the volume (0-100)."""
        self._volume = max(0, min(100, volume))

    # MARK: - Playback Position Management
    def start_playback_from(self, position_seconds: float) -> None:
        """Start playback timing from the specified position."""
        self._stream_start_time = time.time() - position_seconds
        self._paused_position = 0
        self._is_playing = True

    def store_pause_position(self) -> float:
        """Store the current position for later resumption."""
        if self._stream_start_time > 0 and self._is_playing:
            self._paused_position = time.time() - self._stream_start_time
            self._pause_time = time.time()
        return self._paused_position

    # MARK: - Track Information
    def get_track_duration(self, file_path: Path) -> float:
        """Get track duration in seconds with caching."""
        path_str = str(file_path)

        # Check cache first
        if path_str in self._audio_cache:
            return self._audio_cache[path_str]

        # Calculate duration
        try:
            if path_str.lower().endswith(".mp3"):
                audio = MP3(path_str)
                duration = audio.info.length
                self._audio_cache[path_str] = duration
                return duration
            return 0
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error getting track duration: {str(e)}")
            return 0

    def get_track_info(self) -> Dict[str, Any]:
        """Get formatted information about the current track."""
        if not self._current_track:
            return {}

        return {
            "number": self._current_track.number,
            "title": getattr(
                self._current_track, "title", f"Track {self._current_track.number}"
            ),
            "filename": getattr(self._current_track, "filename", None),
            "duration": self.get_track_duration(self._current_track.path),
        }
