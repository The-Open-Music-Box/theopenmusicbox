# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Audio service interface definition.

This module defines the abstract interface for audio services, promoting
loose coupling and enabling dependency injection with different audio
implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional


class AudioServiceInterface(ABC):
    """Abstract interface for audio service implementations.
    
    Defines the contract that all audio services must implement,
    enabling dependency injection and testing with mock implementations.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the audio service is available and ready.
        
        Returns:
            True if audio service is available, False otherwise
        """
        pass

    @abstractmethod
    def play(self) -> bool:
        """Start or resume audio playback.
        
        Returns:
            True if operation was successful, False otherwise
        """
        pass

    @abstractmethod
    def pause(self) -> bool:
        """Pause audio playback.
        
        Returns:
            True if operation was successful, False otherwise
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop audio playback.
        
        Returns:
            True if operation was successful, False otherwise
        """
        pass

    @abstractmethod
    def is_playing(self) -> bool:
        """Check if audio is currently playing.
        
        Returns:
            True if audio is playing, False otherwise
        """
        pass

    @abstractmethod
    def set_volume(self, volume: int) -> bool:
        """Set the audio volume level.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            True if operation was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_volume(self) -> int:
        """Get the current audio volume level.
        
        Returns:
            Current volume level (0-100)
        """
        pass

    @abstractmethod
    def next_track(self) -> bool:
        """Skip to the next track.
        
        Returns:
            True if operation was successful, False otherwise
        """
        pass

    @abstractmethod
    def previous_track(self) -> bool:
        """Go to the previous track.
        
        Returns:
            True if operation was successful, False otherwise
        """
        pass

    @abstractmethod
    def play_track(self, track_number: int) -> bool:
        """Play a specific track by number.
        
        Args:
            track_number: Track number to play
            
        Returns:
            True if operation was successful, False otherwise
        """
        pass

    @abstractmethod
    def load_playlist(self, playlist_data: dict) -> bool:
        """Load a playlist for playback.
        
        Args:
            playlist_data: Playlist data dictionary
            
        Returns:
            True if operation was successful, False otherwise
        """
        pass
