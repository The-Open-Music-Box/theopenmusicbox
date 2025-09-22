# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""macOS Audio Backend Implementation.

This module provides a clean audio backend implementation for macOS using pygame
with Core Audio. It implements the AudioBackendProtocol interface and focuses
purely on audio playback, leaving playlist management to the PlaylistController.
"""

import os
from pathlib import Path
from typing import Optional

import pygame
from app.src.monitoring import get_logger
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_errors
from app.src.monitoring.logging.log_level import LogLevel
from app.src.domain.protocols.notification_protocol import PlaybackNotifierProtocol as PlaybackSubject

from .base_audio_backend import BaseAudioBackend

logger = get_logger(__name__)


class MacOSAudioBackend(BaseAudioBackend):
    """Clean macOS audio backend implementation using pygame with Core Audio.

    This implementation focuses purely on audio playback operations and does not
    handle playlist logic, which is managed by the PlaylistController.
    """

    @handle_errors("__init__")
    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        """Initialize the macOS audio backend."""
        super().__init__(playback_subject)
        self._mixer_initialized = False

        # Set macOS-compatible pygame audio settings
        os.environ["SDL_AUDIODRIVER"] = "coreaudio"  # macOS native audio
        # Initialize pygame mixer for macOS
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.init()
        self._mixer_initialized = True
        logger.log(LogLevel.INFO, "✓ macOS Audio Backend initialized with Core Audio")

    @handle_errors("play_file")
    def play_file(self, file_path: str) -> bool:
        """Play a single audio file.

        Args:
            file_path: Path to the audio file to play

        Returns:
            bool: True if playback started successfully, False otherwise
        """
        if not self._mixer_initialized:
            logger.log(LogLevel.ERROR, "Audio mixer not initialized")
            return False

        with self._state_lock:
            path = Path(file_path)
            if not path.exists():
                logger.log(LogLevel.ERROR, f"Audio file not found: {path}")
                return False
            # Stop any current playback with proper cleanup
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                # Wait for mixer to fully stop to avoid race conditions
                import time

                time.sleep(0.1)
            # Ensure mixer is in clean state
            pygame.mixer.music.unload()
            # Load and play the file with error handling
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
            # Verify playback actually started
            if not pygame.mixer.music.get_busy():
                logger.log(
                    LogLevel.WARNING, f"⚠️️ macOS: Playback may not have started for {path.name}"
                )
            # Update state
            self._is_playing = True
            self._current_file_path = str(path)
            logger.log(LogLevel.INFO, f"🎵 macOS: Started playing {path.name}")
            return True

    @handle_errors("stop")
    def stop(self) -> bool:
        """Stop playback.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self._state_lock:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                # Brief pause to ensure clean stop
                import time

                time.sleep(0.05)
            # Properly unload to free resources
            pygame.mixer.music.unload()
            self._is_playing = False
            self._current_file_path = None
        logger.log(LogLevel.INFO, "⏹️ macOS: Playback stopped")
        return True

    @handle_errors("pause")
    def pause(self) -> bool:
        """Pause playbook.

        Returns:
            bool: True if paused successfully, False otherwise
        """
        if not self._is_playing:
            return False

        with self._state_lock:
            pygame.mixer.music.pause()
            self._is_playing = False
        logger.log(LogLevel.INFO, "⏸️ macOS: Playback paused")
        return True

    @handle_errors("resume")
    def resume(self) -> bool:
        """Resume paused playback.

        Returns:
            bool: True if resumed successfully, False otherwise
        """
        if self._is_playing or not self._current_file_path:
            return False

        with self._state_lock:
            pygame.mixer.music.unpause()
            self._is_playing = True
        logger.log(LogLevel.INFO, "▶️ macOS: Playback resumed")
        return True

    @handle_errors("get_position")
    def get_position(self) -> float:
        """Get current playback position in seconds.

        Returns:
            float: Current position in seconds, 0.0 if not available
        """
        with self._state_lock:
            if not self._is_playing or not self._current_file_path:
                return 0.0
            # pygame doesn't provide direct position info,
            # so this is a simplified implementation
            # The PlaylistController will handle more sophisticated position tracking
            return 0.0

    @handle_errors("set_volume")
    def set_volume(self, volume: int) -> bool:
        """Set playback volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if volume was set successfully, False otherwise
        """
        with self._state_lock:
            self._volume = max(0, min(100, volume))
            # pygame volume is 0.0 to 1.0
            pygame_volume = self._volume / 100.0
            pygame.mixer.music.set_volume(pygame_volume)
        logger.log(LogLevel.DEBUG, f"🔊 macOS: Volume set to {self._volume}%")
        return True

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing.

        Returns:
            bool: True if playing, False otherwise
        """
        with self._state_lock:
            # Sync with pygame state
            if self._is_playing and not pygame.mixer.music.get_busy():
                self._is_playing = False
                logger.log(LogLevel.DEBUG, "macOS: Track finished, updated internal state")

            return self._is_playing

    @property
    def is_busy(self) -> bool:
        """Check if the backend is busy (playing or loading).

        This is used by PlaylistController to detect when a track has finished playing.

        Returns:
            bool: True if backend is busy, False if idle/finished
        """
        with self._state_lock:
            pygame_busy = pygame.mixer.music.get_busy()

            # Update internal state based on pygame state
            if self._is_playing and not pygame_busy:
                self._is_playing = False
                logger.log(LogLevel.DEBUG, "macOS: Track ended, backend no longer busy")

            return pygame_busy

    @handle_errors("cleanup")
    def cleanup(self) -> None:
        """Clean up audio resources."""
        logger.log(LogLevel.INFO, "🧹 Cleaning up macOS audio backend")
        with self._state_lock:
            pygame.mixer.music.stop()
            self._is_playing = False
            self._current_file_path = None
        if self._mixer_initialized:
            pygame.mixer.quit()
            self._mixer_initialized = False
        logger.log(LogLevel.INFO, "✓ macOS audio backend cleanup completed")
