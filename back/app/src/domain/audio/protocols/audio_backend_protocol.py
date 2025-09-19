# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Audio backend protocol for dependency injection."""

from typing import Protocol, Optional


class AudioBackendProtocol(Protocol):
    """Protocol defining the interface for audio backends."""

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        ...

    @property
    def is_paused(self) -> bool:
        """Check if audio is currently paused."""
        ...

    @property
    def is_busy(self) -> bool:
        """Check if backend is busy processing."""
        ...

    def play_file(self, file_path: str) -> bool:
        """Play an audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if playback started successfully
        """
        ...

    def pause(self) -> bool:
        """Pause current playback.

        Returns:
            bool: True if paused successfully
        """
        ...

    def resume(self) -> bool:
        """Resume paused playback.

        Returns:
            bool: True if resumed successfully
        """
        ...

    def stop(self) -> bool:
        """Stop current playback.

        Returns:
            bool: True if stopped successfully
        """
        ...

    def set_volume(self, volume: int) -> bool:
        """Set playback volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if volume was set successfully
        """
        ...

    def get_volume(self) -> int:
        """Get current volume level.

        Returns:
            int: Current volume (0-100)
        """
        ...

    def get_position(self) -> float:
        """Get current playback position in seconds.

        Returns:
            float: Current position in seconds
        """
        ...

    def set_position(self, position_seconds: float) -> bool:
        """Set playback position (seek).

        Args:
            position_seconds: Position to seek to in seconds

        Returns:
            bool: True if seeking was successful
        """
        ...

    def get_duration(self) -> Optional[float]:
        """Get duration of current track in seconds.

        Returns:
            Optional[float]: Duration in seconds, None if not available
        """
        ...

    def cleanup(self) -> None:
        """Clean up backend resources."""
        ...
