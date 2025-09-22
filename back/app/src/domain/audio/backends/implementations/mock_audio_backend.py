# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Mock Audio Backend Implementation.

This module provides a clean mock audio backend implementation for testing and development.
It implements the AudioBackendProtocol interface and focuses purely on simulating audio
operations without requiring real hardware.
"""

import time
from typing import Optional

from app.src.config import config
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.domain.protocols.notification_protocol import PlaybackNotifierProtocol as PlaybackSubject

from .base_audio_backend import BaseAudioBackend
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_errors

logger = get_logger(__name__)


class MockAudioBackend(BaseAudioBackend):
    """Clean mock audio backend for testing and development.

    This implementation simulates audio playback without requiring real hardware.
    It provides predictable behavior for testing auto-advance and playlist functionality.
    """

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        """Initialize the mock audio backend."""
        super().__init__(playback_subject)
        self._track_duration = config.audio.mock_track_duration  # Simulated duration
        self._play_start_time: Optional[float] = None
        self._volume = 50  # Default volume
        self._initialized = False

        logger.log(LogLevel.INFO, "🧪 Mock Audio Backend initialized")

    @handle_errors("initialize")
    def initialize(self) -> bool:
        """Initialize the audio backend (legacy compatibility method).

        Returns:
            bool: True if initialization was successful
        """
        with self._state_lock:
            self._initialized = True
        logger.log(LogLevel.DEBUG, "🧪 Mock: Audio backend initialized")
        return True

    @handle_errors("shutdown")
    def shutdown(self) -> None:
        """Shutdown the audio backend (legacy compatibility method)."""
        with self._state_lock:
            self._is_playing = False
            self._current_file_path = None
            self._play_start_time = None
            self._initialized = False
        logger.log(LogLevel.DEBUG, "🧪 Mock: Audio backend shutdown")

    # AudioBackendProtocol required methods
    @handle_errors("play")
    async def play(self, file_path: str) -> bool:
        """Play an audio file (AudioBackendProtocol interface)."""
        return self.play_file(file_path)

    @handle_errors("pause")
    async def pause(self) -> bool:
        """Pause current playback."""
        with self._state_lock:
            if self._is_playing:
                self._is_playing = False
                logger.log(LogLevel.INFO, "🧪 Mock: Playback paused")
                return True
            return False

    @handle_errors("resume")
    async def resume(self) -> bool:
        """Resume paused playback."""
        with self._state_lock:
            if not self._is_playing and self._current_file_path:
                self._is_playing = True
                logger.log(LogLevel.INFO, "🧪 Mock: Playback resumed")
                return True
            return False

    @handle_errors("stop")
    async def stop(self) -> bool:
        """Stop current playback (async version)."""
        with self._state_lock:
            self._is_playing = False
            self._current_file_path = None
            self._play_start_time = None
            logger.log(LogLevel.INFO, "🧪 Mock: Playback stopped")
            return True

    @handle_errors("set_volume")
    async def set_volume(self, volume: int) -> bool:
        """Set playback volume."""
        if 0 <= volume <= 100:
            self._volume = volume
            logger.log(LogLevel.INFO, f"🧪 Mock: Volume set to {volume}")
            return True
        return False

    @handle_errors("get_volume")
    async def get_volume(self) -> int:
        """Get current volume level."""
        return getattr(self, '_volume', 50)

    @handle_errors("seek")
    async def seek(self, position_ms: int) -> bool:
        """Seek to a specific position."""
        if position_ms >= 0:
            logger.log(LogLevel.INFO, f"🧪 Mock: Seeked to {position_ms}ms")
            return True
        return False

    @handle_errors("get_position")
    async def get_position(self) -> Optional[int]:
        """Get current playback position."""
        if self._is_playing and self._play_start_time:
            elapsed = time.time() - self._play_start_time
            return int(elapsed * 1000)  # Convert to ms
        return None

    @handle_errors("get_duration")
    async def get_duration(self) -> Optional[int]:
        """Get duration of current track."""
        if self._current_file_path:
            return int(self._track_duration * 1000)  # Convert to ms
        return None

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._is_playing

    @handle_errors("play_file")
    def play_file(self, file_path: str) -> bool:
        """Play a single audio file (simulated).

        Args:
            file_path: Path to the audio file to play

        Returns:
            bool: True if playback started successfully, False otherwise
        """
        path = self._validate_file_path(file_path)
        if not path:
            return False

        with self._state_lock:
            # Simulate stopping current playback
            self._is_playing = False
            # Start "playing" the new file
            self._current_file_path = str(path)
            self._is_playing = True
            self._play_start_time = time.time()
            logger.log(LogLevel.INFO, f"🧪 Mock: Started playing {path.name}")
            self._notify_playback_event("track_started", {"file_path": str(path)})
            return True

    @handle_errors("stop")
    def stop(self) -> bool:
        """Stop playback (simulated).

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self._state_lock:
            self._is_playing = False
            self._current_file_path = None
            self._play_start_time = None
        logger.log(LogLevel.INFO, "🧪 Mock: Playback stopped")
        return True

    @handle_errors("pause")
    def pause(self) -> bool:
        """Pause playback (simulated).

        Returns:
            bool: True if paused successfully, False otherwise
        """
        if not self._is_playing:
            return False

        with self._state_lock:
            self._is_playing = False
        logger.log(LogLevel.INFO, "🧪 Mock: Playback paused")
        return True

    @handle_errors("resume")
    def resume(self) -> bool:
        """Resume paused playback (simulated).

        Returns:
            bool: True if resumed successfully, False otherwise
        """
        if self._is_playing or not self._current_file_path:
            return False

        with self._state_lock:
            self._is_playing = True
            # Reset play start time for position calculation
            self._play_start_time = time.time()
        logger.log(LogLevel.INFO, "🧪 Mock: Playback resumed")
        return True

    @handle_errors("get_position")
    def get_position(self) -> float:
        """Get current playback position in seconds (simulated).

        Returns:
            float: Current position in seconds, 0.0 if not available
        """
        with self._state_lock:
            if not self._is_playing or not self._play_start_time:
                return 0.0
            elapsed = time.time() - self._play_start_time
            # Don't exceed the simulated track duration
            return min(elapsed, self._track_duration)

    @handle_errors("set_volume")
    def set_volume(self, volume: int) -> bool:
        """Set playback volume (simulated).

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if volume was set successfully, False otherwise
        """
        with self._state_lock:
            self._volume = max(0, min(100, volume))
        logger.log(LogLevel.DEBUG, f"🧪 Mock: Volume set to {self._volume}%")
        return True

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing (simulated).

        Returns:
            bool: True if playing, False otherwise
        """
        with self._state_lock:
            return self._is_playing

    @property
    def is_busy(self) -> bool:
        """Check if the backend is busy (simulated).

        This is used by PlaylistController to detect when a track has finished playing.

        Returns:
            bool: True if backend is busy, False if idle/finished
        """
        with self._state_lock:
            # Check if track has finished based on duration
            if self._is_playing and self._play_start_time:
                elapsed = time.time() - self._play_start_time
                return elapsed < self._track_duration

            return self._is_playing

    def _update_internal_state(self) -> None:
        """Update internal state by checking if track has finished.

        This method should be called by monitoring systems to ensure
        state consistency without side effects in properties.
        """
        with self._state_lock:
            if self._is_playing and self._play_start_time:
                elapsed = time.time() - self._play_start_time
                if elapsed >= self._track_duration:
                    self._is_playing = False
                    logger.log(LogLevel.DEBUG, "🧪 Mock: Track finished, state updated")
                    self._notify_playback_event(
                        "track_ended",
                        {
                            "file_path": self._current_file_path,
                            "duration": self._track_duration,
                            "elapsed": elapsed,
                        },
                    )

    @handle_errors("cleanup")
    def cleanup(self) -> None:
        """Clean up audio resources (simulated)."""
        logger.log(LogLevel.INFO, "🧪 Cleaning up mock audio backend")
        with self._state_lock:
            self._is_playing = False
            self._current_file_path = None
            self._play_start_time = None
        logger.log(LogLevel.INFO, "🧪 Mock audio backend cleanup completed")
