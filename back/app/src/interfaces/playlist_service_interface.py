# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Playlist service interface definition.

This module defines the abstract interface for playlist services, promoting
loose coupling and enabling dependency injection with different playlist
implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PlaylistServiceInterface(ABC):
    """Abstract interface for playlist service implementations.
    
    Defines the contract that all playlist services must implement,
    enabling dependency injection and testing with mock implementations.
    """

    @abstractmethod
    def create_playlist(self, title: str) -> dict:
        """Create a new empty playlist with the given title.

        Args:
            title: The title of the new playlist.

        Returns:
            Dictionary representing the created playlist.
        """
        pass

    @abstractmethod
    def delete_playlist(self, playlist_id: str) -> dict:
        """Delete a playlist by its ID.

        Args:
            playlist_id: The ID of the playlist to delete.

        Returns:
            Dictionary with deletion status.

        Raises:
            ValueError: If the playlist is not found.
        """
        pass

    @abstractmethod
    def get_all_playlists(
        self, page: int = 1, page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve all playlists with pagination support.

        Args:
            page: Page number (1-based).
            page_size: Number of playlists per page.

        Returns:
            List of dictionaries representing playlists.
        """
        pass

    @abstractmethod
    def get_playlist_by_id(
        self, playlist_id: str, track_page: int = 1, track_page_size: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a playlist by its ID with optional track pagination.

        Args:
            playlist_id: Playlist ID.
            track_page: Page number for tracks (1-based).
            track_page_size: Number of tracks per page.

        Returns:
            Dictionary representing the playlist or None if not found.
        """
        pass

    @abstractmethod
    def save_playlist_file(self, playlist_id: str, playlist_data=None) -> bool:
        """Save the changes to a playlist.

        Args:
            playlist_id: ID of the playlist to save.
            playlist_data: Optional pre-loaded playlist data with changes.

        Returns:
            True if the save was successful, False otherwise.
        """
        pass
