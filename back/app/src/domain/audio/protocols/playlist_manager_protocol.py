# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Playlist manager protocol for dependency injection."""

from typing import Protocol, Optional, Dict, Any
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track


class PlaylistManagerProtocol(Protocol):
    """Protocol defining the interface for playlist management."""

    def set_playlist(self, playlist: Playlist) -> bool:
        """Load and start playing a playlist.

        Args:
            playlist: The playlist to load

        Returns:
            bool: True if playlist was loaded successfully
        """
        ...

    def play_track_by_number(self, track_number: int) -> bool:
        """Play a specific track by number.

        Args:
            track_number: Track number (1-based)

        Returns:
            bool: True if track started playing
        """
        ...

    def next_track(self) -> bool:
        """Advance to next track.

        Returns:
            bool: True if advanced successfully
        """
        ...

    def previous_track(self) -> bool:
        """Go to previous track.

        Returns:
            bool: True if went back successfully
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
        """Stop playback.

        Returns:
            bool: True if stopped successfully
        """
        ...

    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        ...

    @property
    def is_paused(self) -> bool:
        """Check if currently paused."""
        ...

    @property
    def current_playlist(self) -> Optional[Playlist]:
        """Get current playlist."""
        ...

    @property
    def current_track(self) -> Optional[Track]:
        """Get current track."""
        ...

    @property
    def current_track_index(self) -> int:
        """Get current track index (0-based)."""
        ...

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        ...

    def get_playlist_info(self) -> Dict[str, Any]:
        """Get current playlist information."""
        ...

    def get_track_info(self) -> Dict[str, Any]:
        """Get current track information."""
        ...
