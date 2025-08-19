"""
Track operations interface for playlist track management.

This module defines the abstract interface for track operations,
ensuring consistent implementation across different track management services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class TrackOperationsInterface(ABC):
    """Abstract interface for track operations within playlists."""

    @abstractmethod
    def delete_tracks(self, playlist_id: str, track_numbers: List[int]) -> bool:
        """Delete tracks from a playlist by their track numbers.

        Args:
            playlist_id: ID of the playlist containing the tracks to delete.
            track_numbers: List of track numbers to delete.

        Returns:
            True if the deletion was successful, False otherwise.

        Raises:
            ValueError: If input parameters are invalid.
            PlaylistNotFoundError: If playlist doesn't exist.
            FileOperationError: If file system operation fails.
        """
        pass

    @abstractmethod
    def reorder_tracks(self, playlist_id: str, track_order: List[int]) -> bool:
        """Reorder tracks in a playlist based on the provided order.

        Args:
            playlist_id: ID of the playlist to reorder tracks in.
            track_order: List of track numbers in the desired order.

        Returns:
            True if the reordering was successful, False otherwise.

        Raises:
            ValueError: If input parameters are invalid.
            PlaylistNotFoundError: If playlist doesn't exist.
        """
        pass

    @abstractmethod
    def get_tracks_by_playlist(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all tracks for a specific playlist.

        Args:
            playlist_id: ID of the playlist.

        Returns:
            List of track dictionaries.

        Raises:
            ValueError: If playlist_id is invalid.
            PlaylistNotFoundError: If playlist doesn't exist.
        """
        pass

    @abstractmethod
    def move_track_up(self, playlist_id: str, track_number: int) -> bool:
        """Move a track up in the playlist order.

        Args:
            playlist_id: ID of the playlist.
            track_number: Number of the track to move up.

        Returns:
            True if successful, False otherwise.

        Raises:
            ValueError: If input parameters are invalid.
            PlaylistNotFoundError: If playlist doesn't exist.
        """
        pass

    @abstractmethod
    def move_track_down(self, playlist_id: str, track_number: int) -> bool:
        """Move a track down in the playlist order.

        Args:
            playlist_id: ID of the playlist.
            track_number: Number of the track to move down.

        Returns:
            True if successful, False otherwise.

        Raises:
            ValueError: If input parameters are invalid.
            PlaylistNotFoundError: If playlist doesn't exist.
        """
        pass

    @abstractmethod
    def get_track_count(self, playlist_id: str) -> int:
        """Get the number of tracks in a playlist.

        Args:
            playlist_id: ID of the playlist.

        Returns:
            Number of tracks in the playlist.

        Raises:
            ValueError: If playlist_id is invalid.
            PlaylistNotFoundError: If playlist doesn't exist.
        """
        pass
