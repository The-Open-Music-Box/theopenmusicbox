# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""NFC association service for playlist-NFC tag management.

This service handles the association and disassociation of NFC tags
with playlists, providing a clean interface for NFC-related operations.
"""

from typing import Any, Dict, Optional

from app.src.data.playlist_repository import PlaylistRepository
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class NfcAssociationService:
    """Service for managing NFC tag associations with playlists.
    
    Handles linking and unlinking NFC tags to playlists and retrieving
    playlists by their associated NFC tags.
    """

    def __init__(self, config_obj=None):
        """Initialize the NfcAssociationService.
        
        Args:
            config_obj: Optional configuration object. If not provided, uses global config.
        """
        from app.src.config import config as global_config

        self.config = config_obj or global_config
        self.repository = PlaylistRepository(self.config)

    def get_playlist_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a playlist by its associated NFC tag ID.

        Args:
            nfc_tag_id: NFC tag ID.

        Returns:
            Dictionary representing the playlist or None if not found.
        """
        return self.repository.get_playlist_by_nfc_tag(nfc_tag_id)

    def associate_nfc_tag(self, playlist_id: str, nfc_tag_id: str) -> bool:
        """Associate an NFC tag with a playlist.

        Args:
            playlist_id: Playlist ID.
            nfc_tag_id: NFC tag ID to associate.

        Returns:
            True if the association succeeded, False otherwise.
        """
        try:
            success = self.repository.associate_nfc_tag(playlist_id, nfc_tag_id)
            if success:
                logger.log(
                    LogLevel.INFO,
                    f"Successfully associated NFC tag {nfc_tag_id} with playlist {playlist_id}"
                )
            else:
                logger.log(
                    LogLevel.ERROR,
                    f"Failed to associate NFC tag {nfc_tag_id} with playlist {playlist_id}"
                )
            return success
        except (ValueError, TypeError, KeyError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error associating NFC tag {nfc_tag_id} with playlist {playlist_id}: {str(e)}"
            )
            return False

    def disassociate_nfc_tag(self, playlist_id: str) -> bool:
        """Remove the association of an NFC tag from a playlist.

        Args:
            playlist_id: Playlist ID.

        Returns:
            True if the disassociation succeeded, False otherwise.
        """
        try:
            success = self.repository.disassociate_nfc_tag(playlist_id)
            if success:
                logger.log(
                    LogLevel.INFO,
                    f"Successfully disassociated NFC tag from playlist {playlist_id}"
                )
            else:
                logger.log(
                    LogLevel.ERROR,
                    f"Failed to disassociate NFC tag from playlist {playlist_id}"
                )
            return success
        except (ValueError, TypeError, KeyError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error disassociating NFC tag from playlist {playlist_id}: {str(e)}"
            )
            return False

    def get_nfc_associations(self) -> Dict[str, str]:
        """Get all NFC tag associations.
        
        Returns:
            Dictionary mapping NFC tag IDs to playlist IDs.
        """
        try:
            # Get all playlists and extract NFC associations
            playlists = self.repository.get_all_playlists()
            associations = {}
            
            for playlist in playlists:
                nfc_tag_id = playlist.get("nfc_tag_id")
                if nfc_tag_id:
                    associations[nfc_tag_id] = playlist["id"]
                    
            return associations
        except (ValueError, TypeError, KeyError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error retrieving NFC associations: {str(e)}"
            )
            return {}
