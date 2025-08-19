# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Audio controller for managing audio playback and volume control.

This controller handles audio-related operations including playback control,
volume management, and audio state tracking. It provides a clean interface
between the audio hardware/service and the rest of the application.
"""

import time
from typing import Optional

from app.src.config import config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class AudioController:
    """Controller for audio playback and volume management.
    
    Manages audio operations including play/pause/resume, volume control,
    and audio state tracking. Provides debouncing for control inputs
    and maintains volume state consistency.
    """

    def __init__(self, audio_service=None):
        """Initialize the AudioController.
        
        Args:
            audio_service: The audio service instance for playback control
        """
        self._audio_service = audio_service
        self._current_volume = config.audio.default_volume
        self._last_pause_toggle_time = 0
        self._pause_toggle_cooldown = 0.3  # 300ms cooldown between toggles

    def set_audio_service(self, audio_service):
        """Set the audio service instance.
        
        Args:
            audio_service: The audio service instance
        """
        self._audio_service = audio_service
        if audio_service and hasattr(audio_service, '_volume'):
            self._current_volume = audio_service._volume

    def get_audio_service(self) -> Optional[object]:
        """Get the current audio service instance.
        
        Returns:
            The audio service instance or None if not available
        """
        return self._audio_service

    def is_audio_available(self) -> bool:
        """Check if audio service is available.
        
        Returns:
            True if audio service is available, False otherwise
        """
        return self._audio_service is not None

    def toggle_playback(self) -> bool:
        """Toggle between play and pause states with debouncing.
        
        Implements cooldown mechanism to prevent double-triggering of
        play/pause commands from physical controls.
        
        Returns:
            True if operation was successful, False otherwise
        """
        if not self._audio_service:
            logger.log(
                LogLevel.WARNING,
                "Cannot toggle playback: No audio service available"
            )
            return False

        # Check cooldown to prevent double-triggering
        current_time = time.time()
        time_since_last_toggle = current_time - self._last_pause_toggle_time
        
        if time_since_last_toggle < self._pause_toggle_cooldown:
            logger.log(
                LogLevel.WARNING,
                f"Playback toggle ignored - cooldown active ({time_since_last_toggle:.3f}s < {self._pause_toggle_cooldown}s)"
            )
            return False
        
        self._last_pause_toggle_time = current_time
        
        try:
            # Log the current state before handling
            is_playing_before = self._audio_service.is_playing
            logger.log(
                LogLevel.INFO,
                f"Processing playback toggle - current state: is_playing={is_playing_before}"
            )

            if is_playing_before:
                logger.log(LogLevel.INFO, "Executing PAUSE")
                self._audio_service.pause()
                # Verify state after pause
                is_playing_after = self._audio_service.is_playing
                logger.log(
                    LogLevel.INFO,
                    f"State after PAUSE: is_playing={is_playing_after}"
                )
            else:
                logger.log(LogLevel.INFO, "Executing RESUME")
                self._audio_service.resume()
                # Verify state after resume
                is_playing_after = self._audio_service.is_playing
                logger.log(
                    LogLevel.INFO,
                    f"State after RESUME: is_playing={is_playing_after}"
                )
            
            return True
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error toggling playback: {str(e)}"
            )
            return False

    def increase_volume(self) -> bool:
        """Increase the volume by the configured step amount.
        
        Returns:
            True if operation was successful, False otherwise
        """
        if not self._audio_service:
            logger.log(
                LogLevel.WARNING,
                "Cannot increase volume: No audio service available"
            )
            return False

        try:
            new_volume = min(
                self._current_volume + config.audio.volume_step, 
                config.audio.max_volume
            )
            logger.log(
                LogLevel.INFO,
                f"Increasing volume from {self._current_volume}% to {new_volume}%"
            )
            
            success = self._audio_service.set_volume(new_volume)
            if success:
                self._current_volume = new_volume
            
            return success
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error increasing volume: {str(e)}"
            )
            return False

    def decrease_volume(self) -> bool:
        """Decrease the volume by the configured step amount.
        
        Returns:
            True if operation was successful, False otherwise
        """
        if not self._audio_service:
            logger.log(
                LogLevel.WARNING,
                "Cannot decrease volume: No audio service available"
            )
            return False

        try:
            new_volume = max(
                self._current_volume - config.audio.volume_step, 
                config.audio.min_volume
            )
            logger.log(
                LogLevel.INFO,
                f"Decreasing volume from {self._current_volume}% to {new_volume}%"
            )
            
            success = self._audio_service.set_volume(new_volume)
            if success:
                self._current_volume = new_volume
            
            return success
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error decreasing volume: {str(e)}"
            )
            return False

    def set_volume(self, volume: int) -> bool:
        """Set the volume to a specific level.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            True if operation was successful, False otherwise
        """
        if not self._audio_service:
            logger.log(
                LogLevel.WARNING,
                "Cannot set volume: No audio service available"
            )
            return False

        if not (config.audio.min_volume <= volume <= config.audio.max_volume):
            logger.log(
                LogLevel.WARNING,
                f"Invalid volume level: {volume}. Must be between {config.audio.min_volume} and {config.audio.max_volume}"
            )
            return False

        try:
            logger.log(
                LogLevel.INFO,
                f"Setting volume from {self._current_volume}% to {volume}%"
            )
            
            success = self._audio_service.set_volume(volume)
            if success:
                self._current_volume = volume
            
            return success
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error setting volume: {str(e)}"
            )
            return False

    def get_current_volume(self) -> int:
        """Get the current volume level.
        
        Returns:
            Current volume level (0-100)
        """
        # Always get the actual volume from the audio instance if available
        if self._audio_service:
            actual_volume = getattr(self._audio_service, "_volume", self._current_volume)
            self._current_volume = actual_volume
        return self._current_volume

    def next_track(self) -> bool:
        """Skip to the next track.
        
        Returns:
            True if operation was successful, False otherwise
        """
        if not self._audio_service:
            logger.log(
                LogLevel.WARNING,
                "Cannot skip to next track: No audio service available"
            )
            return False

        try:
            logger.log(LogLevel.INFO, "Skipping to next track")
            self._audio_service.next_track()
            return True
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error skipping to next track: {str(e)}"
            )
            return False

    def previous_track(self) -> bool:
        """Go to the previous track.
        
        Returns:
            True if operation was successful, False otherwise
        """
        if not self._audio_service:
            logger.log(
                LogLevel.WARNING,
                "Cannot go to previous track: No audio service available"
            )
            return False

        try:
            logger.log(LogLevel.INFO, "Going to previous track")
            self._audio_service.previous_track()
            return True
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error going to previous track: {str(e)}"
            )
            return False

    def get_playback_state(self) -> dict:
        """Get the current playback state.
        
        Returns:
            Dictionary containing playback state information
        """
        if not self._audio_service:
            return {
                "is_playing": False,
                "volume": self._current_volume,
                "audio_available": False
            }

        try:
            return {
                "is_playing": getattr(self._audio_service, 'is_playing', False),
                "volume": self._current_volume,
                "audio_available": True
            }
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error getting playback state: {str(e)}"
            )
            return {
                "is_playing": False,
                "volume": self._current_volume,
                "audio_available": False
            }
