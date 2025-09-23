# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""WM8960 Audio Backend Implementation.

This module provides a clean WM8960 audio backend implementation for Raspberry Pi hardware.
It implements the AudioBackendProtocol interface and provides real hardware audio playback
through the WM8960 codec using pygame for reliable audio format handling.
"""

import os
import asyncio
import subprocess
import time
from pathlib import Path
from typing import Optional

try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from app.src.config import config
from app.src.monitoring import get_logger
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_errors
from app.src.monitoring.logging.log_level import LogLevel
from app.src.domain.protocols.notification_protocol import PlaybackNotifierProtocol as PlaybackSubject

from .base_audio_backend import BaseAudioBackend

logger = get_logger(__name__)


class WM8960AudioBackend(BaseAudioBackend):
    """WM8960 audio backend for Raspberry Pi hardware.

    This implementation provides real audio playback through the WM8960 codec
    using ALSA and subprocess-based audio control.
    """

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        """Initialize the WM8960 audio backend."""
        super().__init__(playback_subject)
        self._is_paused = False
        self._play_start_time = None
        self._pause_time = None

        # Initialize hardware
        self._initialize_wm8960_hardware()

        # Initialize pygame mixer for proper audio handling
        if PYGAME_AVAILABLE:
            # Simple default pygame initialization on startup
            self._init_pygame_simple()
        else:
            logger.log(LogLevel.WARNING, "🔊 WM8960: pygame not available - audio will not work")

        logger.log(LogLevel.INFO, "🔊 WM8960 Audio Backend initialized")

    @handle_errors("_init_pygame_simple")
    def _init_pygame_simple(self) -> bool:
        """Initialize pygame mixer with WM8960-specific ALSA configuration."""
        logger.log(LogLevel.INFO, "🔊 WM8960: Initializing pygame mixer with WM8960 ALSA configuration")

        # Detect the WM8960 device first if not already done
        if not hasattr(self, '_audio_device'):
            self._audio_device = self._detect_wm8960_device()

        # Configure SDL to use ALSA with the specific WM8960 device
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['SDL_AUDIODEV'] = self._audio_device

        logger.log(LogLevel.INFO, f"🔊 WM8960: Configuring SDL with ALSA device: {self._audio_device}")

        # Clear any existing pygame state
        if pygame.mixer.get_init():
            pygame.mixer.quit()

        # Use configuration optimized for WM8960 with explicit ALSA targeting
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.init()

        # Verify initialization
        if pygame.mixer.get_init():
            init_info = pygame.mixer.get_init()
            logger.log(
                LogLevel.INFO, f"🔊 WM8960: pygame mixer initialized successfully with {init_info} on device {self._audio_device}"
            )
            return True
        else:
            logger.log(LogLevel.ERROR, "🔊 WM8960: pygame mixer failed to initialize")
            return False

    @handle_errors("_detect_wm8960_device")
    def _detect_wm8960_device(self) -> str:
        """Detect WM8960 audio device automatically.

        Returns:
            str: ALSA device identifier for WM8960
        """
        try:
            # Try to get list of audio devices
            result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        except FileNotFoundError:
            # aplay not found (e.g., on macOS), use default
            logger.log(LogLevel.INFO, "🔊 WM8960: aplay not found, using default device")
            return config.hardware.alsa_device or "plughw:1,0"
        if result.returncode == 0:
            output = result.stdout
            # Look for WM8960 card
            for line in output.split("\n"):
                if "wm8960" in line.lower():
                    # Extract card number for hw:X,0 format
                    if "card" in line.lower():
                        # Parse "card X: cardname" to get card number
                        parts = line.split("card")
                        if len(parts) >= 2:
                            card_part = parts[1].split(":")[0].strip()  # Get number part
                            if card_part.isdigit():
                                # Use plughw for better compatibility with different audio formats
                                device = f"plughw:{card_part},0"
                                logger.log(
                                    LogLevel.INFO, f"🔊 WM8960: Detected audio device: {device}"
                                )
                                return device
                            else:
                                # Fallback: try card name format
                                card_name = (
                                    parts[1].split(":")[1].strip().split()[0]
                                )  # Get card name
                                device = f"hw:{card_name},0"
                                logger.log(
                                    LogLevel.INFO, f"🔊 WM8960: Using card name format: {device}"
                                )
                                return device
            # Fallback: look for any card with wm8960 in name and extract number
            for line in output.split("\n"):
                if "wm8960soundcard" in line.lower():
                    # Try to extract card number from any line containing wm8960soundcard
                    if "card" in line:
                        card_num = line.split("card")[1].split(":")[0].strip()
                        if card_num.isdigit():
                            device = f"hw:{card_num},0"
                            logger.log(LogLevel.INFO, f"🔊 WM8960: Fallback detected: {device}")
                            return device
        # Final fallback to config
        device = config.hardware.alsa_device or "plughw:0,0"
        logger.log(LogLevel.INFO, f"🔊 WM8960: Using configured device: {device}")
        return device

    @handle_errors("_initialize_wm8960_hardware")
    def _initialize_wm8960_hardware(self) -> bool:
        """Initialize WM8960 hardware settings.

        Returns:
            bool: True if initialization was successful
        """
        # Detect the correct audio device for pygame configuration
        self._audio_device = self._detect_wm8960_device()
        logger.log(LogLevel.INFO, f"🔊 WM8960: Detected audio device: {self._audio_device}")
        return True

    @handle_errors("play_file")
    def play_file(self, file_path: str) -> bool:
        """Play a single audio file through WM8960 using pygame.

        Args:
            file_path: Path to the audio file to play

        Returns:
            bool: True if playback started successfully, False otherwise
        """
        path = self._validate_file_path(file_path)
        if not path:
            return False

        with self._state_lock:
            # Stop current playback if any
            self._stop_current_playback()
            # Use pygame for reliable audio playback
            if not PYGAME_AVAILABLE:
                logger.log(LogLevel.ERROR, "🔊 WM8960: pygame not available - cannot play audio")
                return False
            if not pygame.mixer.get_init():
                logger.log(
                    LogLevel.WARNING,
                    "🔊 WM8960: pygame mixer not initialized, attempting to initialize",
                )
                if not self._init_pygame_simple():
                    logger.log(LogLevel.ERROR, "🔊 WM8960: Failed to initialize pygame mixer")
                    return False
            else:
                # Verify current initialization is using the correct device
                current_init = pygame.mixer.get_init()
                expected_device = getattr(self, '_audio_device', None)
                current_device = os.environ.get('SDL_AUDIODEV', 'default')

                if expected_device and current_device != expected_device:
                    logger.log(
                        LogLevel.INFO,
                        f"🔊 WM8960: Reconfiguring pygame for correct device (current: {current_device}, expected: {expected_device})"
                    )
                    if not self._init_pygame_simple():
                        logger.log(LogLevel.ERROR, "🔊 WM8960: Failed to reconfigure pygame mixer")
                        return False
            return self._play_with_pygame(str(path))

    @handle_errors("_play_with_pygame")
    def _play_with_pygame(self, file_path: str) -> bool:
        """Play audio file using pygame.mixer.music (preferred method)."""
        logger.log(LogLevel.INFO, f"🔊 WM8960: Using pygame.mixer.music for playback")
        # Load and play the audio file with pygame.mixer.music
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self._current_file_path = file_path
        self._is_playing = True
        self._is_paused = False
        self._play_start_time = time.time()
        self._pause_time = None
        logger.log(
            LogLevel.INFO,
            f"🔊 WM8960: Started playing {Path(file_path).name} with pygame.mixer.music",
        )
        return True

    @handle_errors("stop_sync")
    def stop_sync(self) -> bool:
        """Stop playback.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self._state_lock:
            self._stop_current_playback()
        logger.log(LogLevel.INFO, "🔊 WM8960: Playback stopped")
        return True

    @handle_errors("pause_sync")
    def pause_sync(self) -> bool:
        """Pause playback using pygame.mixer.music.pause().

        Returns:
            bool: True if paused successfully, False otherwise
        """
        if not self._is_playing or self._is_paused:
            return False

        with self._state_lock:
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                # Proper pause with pygame.mixer.music
                pygame.mixer.music.pause()
                self._is_playing = False
                self._is_paused = True
                self._pause_time = time.time()
                logger.log(LogLevel.INFO, "🔊 WM8960: Playback paused")
                return True
            else:
                return False

    @handle_errors("resume_sync")
    def resume_sync(self) -> bool:
        """Resume paused playback using pygame.mixer.music.unpause().

        Returns:
            bool: True if resumed successfully, False otherwise
        """
        if not self._is_paused:
            return False

        with self._state_lock:
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                # Proper unpause with pygame.mixer.music
                pygame.mixer.music.unpause()
                self._is_playing = True
                self._is_paused = False
                # Adjust play start time to account for pause duration
                if self._pause_time and self._play_start_time:
                    pause_duration = time.time() - self._pause_time
                    self._play_start_time += pause_duration
                self._pause_time = None
                logger.log(LogLevel.INFO, "🔊 WM8960: Playback resumed")
                return True
            else:
                return False

    @handle_errors("get_position_sync")
    def get_position_sync(self) -> float:
        """Get current playback position in seconds.

        Returns:
            float: Current position in seconds
        """
        with self._state_lock:
            if not self._play_start_time:
                return 0.0
            if self._is_paused and self._pause_time:
                # If paused, return position at pause time
                position = self._pause_time - self._play_start_time
            elif self._is_playing:
                # If playing, return current elapsed time
                position = time.time() - self._play_start_time
            else:
                return 0.0
            # Validate position - should not be negative or extremely large
            if position < 0:
                logger.log(
                    LogLevel.WARNING,
                    f"🔊 WM8960: Negative position detected ({position:.2f}s), resetting to 0",
                )
                return 0.0
            elif position > 7200:  # More than 2 hours is suspicious
                logger.log(
                    LogLevel.WARNING,
                    f"🔊 WM8960: Suspiciously large position ({position:.2f}s), might indicate timing issue",
                )
            return position

    @handle_errors("set_position")
    def set_position(self, position: float) -> bool:
        """Set playback position (seek functionality).

        Args:
            position: Position in seconds to seek to

        Returns:
            bool: True if position was set successfully, False otherwise

        Note: pygame.mixer.music doesn't support direct seeking, so we restart
        playback from the beginning and use pygame.mixer.music.set_pos() if available.
        """
        if not self._current_file_path:
            return False

        with self._state_lock:
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                was_playing = self._is_playing
                was_paused = self._is_paused
                # Stop current playback
                pygame.mixer.music.stop()
                # Reload and start playback
                pygame.mixer.music.load(self._current_file_path)
                # Try to use pygame's set_pos if available (pygame 2.0+)
                seek_success = False
                try:
                    # Test if pygame supports the start parameter first
                    import inspect

                    play_sig = inspect.signature(pygame.mixer.music.play)
                    has_start_param = "start" in play_sig.parameters
                    if has_start_param:
                        # Try to use the start parameter
                        pygame.mixer.music.play(start=position)
                        # Assume seeking worked for now - pygame doesn't give us feedback
                        seek_success = True
                        logger.log(
                            LogLevel.INFO,
                            f"🔊 WM8960: Attempted seek to {position:.1f}s using play(start=)",
                        )
                    else:
                        # No start parameter available
                        pygame.mixer.music.play()
                        seek_success = False
                        logger.log(
                            LogLevel.WARNING,
                            "🔊 WM8960: pygame.mixer.music.play() doesn't support start parameter",
                        )
                except Exception as e:
                    # Fallback to simple play without seeking
                    pygame.mixer.music.play()
                    seek_success = False
                    logger.log(LogLevel.WARNING, f"🔊 WM8960: Seek failed, playing from start: {e}")

    @handle_errors("set_volume_sync")
    def set_volume_sync(self, volume: int) -> bool:
        """Set playback volume through pygame and ALSA.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if volume was set successfully, False otherwise
        """
        with self._state_lock:
            self._volume = max(0, min(100, volume))
            # Set pygame volume (0.0 to 1.0)
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                pygame_volume = self._volume / 100.0
                pygame.mixer.music.set_volume(pygame_volume)
                logger.log(LogLevel.DEBUG, f"🔊 WM8960: pygame volume set to {pygame_volume}")
                # Also set system volume via ALSA
                volume_percent = f"{self._volume}%"
                subprocess.run(
                    ["amixer", "sset", "Master", volume_percent], check=True, capture_output=True
                )
                logger.log(LogLevel.DEBUG, f"🔊 WM8960: ALSA volume set to {self._volume}%")

    @property
    def is_paused(self) -> bool:
        """Check if audio is currently paused.

        Returns:
            bool: True if paused, False otherwise
        """
        return getattr(self, "_is_paused", False)

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing.

        Returns:
            bool: True if playing, False otherwise
        """
        with self._state_lock:
            # Check pygame.mixer.music playback status
            if PYGAME_AVAILABLE and self._is_playing and not self._is_paused:
                if not pygame.mixer.music.get_busy():
                    # pygame music finished
                    self._is_playing = False
                    self._is_paused = False
                    self._play_start_time = None
                    logger.log(LogLevel.DEBUG, "🔊 WM8960: pygame track finished")

            return self._is_playing

    @property
    def is_busy(self) -> bool:
        """Check if the backend is busy.

        This is used by PlaylistController to detect when a track has finished playing.

        Returns:
            bool: True if backend is busy, False if idle/finished
        """
        with self._state_lock:
            # Check if pygame.mixer.music is still playing
            if PYGAME_AVAILABLE and self._is_playing and not self._is_paused:
                if not pygame.mixer.music.get_busy():
                    # Track finished
                    self._is_playing = False
                    self._is_paused = False
                    self._play_start_time = None
                    logger.log(LogLevel.DEBUG, "🔊 WM8960: Track ended, backend no longer busy")
                    return False

            return self._is_playing

    # Async methods required by AudioBackendProtocol
    async def pause(self) -> bool:
        """Async wrapper for pause method.

        Returns:
            bool: True if pause was successful
        """
        return self.pause_sync()

    async def resume(self) -> bool:
        """Async wrapper for resume method.

        Returns:
            bool: True if resume was successful
        """
        return self.resume_sync()

    async def stop(self) -> bool:
        """Async wrapper for stop method.

        Returns:
            bool: True if stop was successful
        """
        return self.stop_sync()

    async def set_volume(self, volume: int) -> bool:
        """Async wrapper for set_volume method.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if volume was set successfully
        """
        return self.set_volume_sync(volume)

    async def get_position(self) -> Optional[int]:
        """Get current playback position.

        Returns:
            int: Current position in milliseconds or None if not playing
        """
        position_s = self.get_position_sync()
        if position_s > 0:
            return int(position_s * 1000)
        return None

    async def play(self, file_path: str) -> bool:
        """Async wrapper for play_file method.

        Args:
            file_path: Path to the audio file to play

        Returns:
            bool: True if playback started successfully
        """
        return await asyncio.get_event_loop().run_in_executor(None, self.play_file, file_path)

    async def get_volume(self) -> int:
        """Get current volume level.

        Returns:
            int: Current volume (0-100)
        """
        return self._volume

    async def seek(self, position_ms: int) -> bool:
        """Seek to a specific position.

        Args:
            position_ms: Position in milliseconds

        Returns:
            bool: True if seek was successful
        """
        position_s = position_ms / 1000.0
        return self.set_position(position_s)

    async def get_duration(self) -> Optional[int]:
        """Get duration of current track.

        Returns:
            int: Duration in milliseconds or None if not available
        """
        # pygame doesn't provide easy duration access, return None for now
        # This could be improved by using mutagen or similar library
        return None

    @handle_errors("cleanup")
    def cleanup(self) -> None:
        """Clean up audio resources."""
        logger.log(LogLevel.INFO, "🔊 Cleaning up WM8960 audio backend")
        with self._state_lock:
            self._stop_current_playback()
        logger.log(LogLevel.INFO, "🔊 WM8960 audio backend cleanup completed")

    @handle_errors("_stop_current_playback")
    def _stop_current_playback(self) -> None:
        """Stop the current pygame.mixer.music playback."""
        # Stop pygame.mixer.music if active
        if PYGAME_AVAILABLE and pygame.mixer.get_init():
            pygame.mixer.music.stop()
            logger.log(LogLevel.DEBUG, "🔊 WM8960: Stopped pygame.mixer.music playback")
        self._is_playing = False
        self._is_paused = False
        self._play_start_time = None
        self._pause_time = None
        self._current_file_path = None
