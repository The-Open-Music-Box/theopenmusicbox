# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Audio Backend Interface.

This module defines the abstraction layer for audio playback systems.
Different implementations (pygame, other libraries) can be provided as
long as they implement this interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable


class AudioBackend(ABC):
    """Interface for audio playback systems."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the audio system.

        Returns:
            bool: True if initialization was successful
        """

    @abstractmethod
    def shutdown(self) -> bool:
        """Shut down the audio system and free all resources.

        Returns:
            bool: True if shutdown was successful
        """

    @abstractmethod
    def load(self, file_path: Path) -> bool:
        """Load an audio file for playback.

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if loading was successful
        """

    @abstractmethod
    def play(self) -> bool:
        """Start playing the loaded audio.

        Returns:
            bool: True if playback started successfully
        """

    @abstractmethod
    def pause(self) -> bool:
        """Pause the currently playing audio.

        Returns:
            bool: True if pausing was successful
        """

    @abstractmethod
    def resume(self) -> bool:
        """Resume playback from a paused state.

        Returns:
            bool: True if resuming was successful
        """

    @abstractmethod
    def stop(self) -> bool:
        """Stop playback and unload the current audio file.

        Returns:
            bool: True if stopping was successful
        """

    @abstractmethod
    def set_position(self, position_seconds: float) -> bool:
        """Set the playback position.

        Args:
            position_seconds: Position in seconds

        Returns:
            bool: True if setting position was successful
        """

    @abstractmethod
    def get_position(self) -> float:
        """Get the current playback position in seconds.

        Returns:
            float: Current position in seconds
        """

    @abstractmethod
    def set_volume(self, volume: int) -> bool:
        """Set the playback volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if setting volume was successful
        """

    @abstractmethod
    def get_volume(self) -> int:
        """Get the current volume.

        Returns:
            int: Current volume (0-100)
        """

    @abstractmethod
    def is_playing(self) -> bool:
        """Check if audio is currently playing.

        Returns:
            bool: True if audio is playing
        """

    @abstractmethod
    def register_end_event_callback(self, callback: Callable[[], None]) -> bool:
        """Register a callback to be called when playback ends.

        Args:
            callback: Function to call when playback ends

        Returns:
            bool: True if registration was successful
        """

    @abstractmethod
    def get_duration(self, file_path: Path) -> float:
        """Get the duration of an audio file in seconds.

        Args:
            file_path: Path to the audio file

        Returns:
            float: Duration in seconds
        """
