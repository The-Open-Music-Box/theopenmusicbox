# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Playlist CRUD service for basic playlist operations.

This service handles core playlist CRUD operations including creation,
retrieval, updates, and deletion. It focuses on basic playlist management
without filesystem synchronization or complex business logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.src.data.playlist_repository import get_playlist_repository
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class PlaylistCrudService:
    """Service for basic playlist CRUD operations.
    
    Handles creation, retrieval, updates, and deletion of playlists
    without complex business logic or filesystem operations.
    """

    def __init__(self, config_obj=None):
        """Initialize the PlaylistCrudService.
        
        Args:
            config_obj: Optional configuration object. If not provided, uses global config.
        """
        from app.src.config import config as global_config

        self.config = config_obj or global_config
        self.repository = get_playlist_repository()

    def create_playlist(self, title: str) -> dict:
        """Create a new empty playlist with the given title.

        Args:
            title: The title of the new playlist.

        Returns:
            Dictionary representing the created playlist.
        """
        playlist_data = {
            "id": str(uuid4()),
            "type": "playlist",
            "title": title,
            "path": title.replace(" ", "_"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tracks": [],
        }
        self.repository.create_playlist(playlist_data)
        return playlist_data

    def delete_playlist(self, playlist_id: str) -> dict:
        """Delete a playlist by its ID.

        Args:
            playlist_id: The ID of the playlist to delete.

        Returns:
            Dictionary with deletion status.

        Raises:
            ValueError: If the playlist is not found.
        """
        deleted = self.repository.delete_playlist(playlist_id)
        if not deleted:
            raise ValueError(f"Playlist with id {playlist_id} not found")
        return {"id": playlist_id, "deleted": True}

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
        offset = (page - 1) * page_size
        return self.repository.get_all_playlists(limit=page_size, offset=offset)

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
        track_offset = (track_page - 1) * track_page_size
        return self.repository.get_playlist_by_id(
            playlist_id, track_limit=track_page_size, track_offset=track_offset
        )

    def save_playlist_file(self, playlist_id: str, playlist_data=None) -> bool:
        """Save the changes to a playlist.

        Args:
            playlist_id: ID of the playlist to save.
            playlist_data: Optional pre-loaded playlist data with changes.

        Returns:
            True if the save was successful, False otherwise.
        """
        try:
            if playlist_data:
                playlist = playlist_data
                logger.log(
                    LogLevel.INFO, f"Using provided playlist data for {playlist_id}"
                )
            else:
                playlist = self.repository.get_playlist_by_id(playlist_id)
                if not playlist:
                    logger.log(
                        LogLevel.ERROR,
                        f"Failed to save playlist: {playlist_id} not found",
                    )
                    return False

            # Update the playlist in the repository
            playlist_id_to_update = playlist["id"]
            updated_data = dict(playlist)

            # Update playlist metadata
            meta_success = self.repository.update_playlist(
                playlist_id_to_update, updated_data
            )

            # Update tracks if present
            tracks_success = True
            if "tracks" in playlist and playlist["tracks"]:
                logger.log(
                    LogLevel.INFO,
                    f"Updating {len(playlist['tracks'])} tracks for playlist {playlist_id}",
                )
                tracks_success = self.repository.replace_tracks(
                    playlist_id_to_update, playlist["tracks"]
                )

            success = meta_success and tracks_success
            if success:
                logger.log(LogLevel.INFO, f"Successfully saved playlist: {playlist_id}")
            else:
                logger.log(
                    LogLevel.ERROR,
                    f"Failed to save playlist: {playlist_id} (meta: {meta_success}, tracks: {tracks_success})",
                )

            return success
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.log(LogLevel.ERROR, f"Error saving playlist {playlist_id}: {str(e)}")
            return False

    def update_playlist(self, playlist_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a playlist with new data.

        Args:
            playlist_id: ID of the playlist to update.
            update_data: Dictionary containing the fields to update.

        Returns:
            Dictionary representing the updated playlist.

        Raises:
            ValueError: If the playlist is not found or data is invalid.
        """
        # Validate the playlist exists
        existing_playlist = self.repository.get_playlist_by_id(playlist_id)
        if not existing_playlist:
            raise ValueError(f"Playlist with ID {playlist_id} not found")

        # Validate update data
        if "name" in update_data or "title" in update_data:
            name_field = "name" if "name" in update_data else "title"
            if not update_data[name_field] or not update_data[name_field].strip():
                raise ValueError("Playlist name cannot be empty")

        # Update the playlist
        success = self.repository.update_playlist(playlist_id, update_data)
        if not success:
            raise ValueError(f"Failed to update playlist {playlist_id}")

        # Return the updated playlist
        return self.repository.get_playlist_by_id(playlist_id)

    def playlist_exists(self, playlist_id: str) -> bool:
        """Check if a playlist exists.

        Args:
            playlist_id: ID of the playlist to check.

        Returns:
            True if the playlist exists, False otherwise.
        """
        playlist = self.repository.get_playlist_by_id(playlist_id)
        return playlist is not None

    def _validate_playlist_data(self, data: Dict[str, Any]) -> bool:
        """Validate playlist data.

        Args:
            data: Dictionary containing playlist data to validate.

        Returns:
            True if data is valid, False otherwise.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        if not data:
            raise ValueError("Playlist data cannot be empty")

        # Check for required name/title field
        name_field = data.get("name") or data.get("title")
        if not name_field or not name_field.strip():
            raise ValueError("Playlist name cannot be empty")

        return True

    def get_playlist_count(self) -> int:
        """Get the total number of playlists.

        Returns:
            Total count of playlists.
        """
        playlists = self.repository.get_all_playlists()
        return len(playlists) if playlists else 0
