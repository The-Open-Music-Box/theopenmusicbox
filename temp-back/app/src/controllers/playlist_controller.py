# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Playlist controller for handling playlist business logic.

This controller extracts business logic from the route handlers and provides
a clean interface for playlist operations, following the Single Responsibility
Principle and dependency injection patterns.
"""

from typing import Any, Dict, List, Optional

from app.src.core.service_container import ServiceContainer
from app.src.helpers.error_handling import ErrorHandler
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class PlaylistController:
    """
    Controller for playlist business logic.
    
    Handles playlist operations by coordinating between services and
    providing a clean interface for route handlers.
    """

    def __init__(self, service_container: Optional[ServiceContainer] = None):
        """
        Initialize the PlaylistController.
        
        Args:
            service_container: Optional service container for dependency injection.
        """
        self.service_container = service_container or ServiceContainer()
        self.playlist_service = self.service_container.get_playlist_service()
        self.error_handler = ErrorHandler()

    def get_all_playlists(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        Get all playlists with pagination.
        
        Args:
            page: Page number (1-based).
            page_size: Number of playlists per page.
            
        Returns:
            Dictionary containing playlists and pagination info.
        """
        try:
            playlists = self.playlist_service.get_all_playlists(page, page_size)
            
            return {
                "playlists": playlists,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": len(playlists)
                }
            }
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error retrieving playlists: {str(e)}")
            raise

    def get_playlist_by_id(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a playlist by its ID.
        
        Args:
            playlist_id: The playlist ID.
            
        Returns:
            Playlist data or None if not found.
        """
        try:
            return self.playlist_service.get_playlist_by_id(playlist_id)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error retrieving playlist {playlist_id}: {str(e)}")
            raise

    def create_playlist(self, title: str) -> Dict[str, Any]:
        """
        Create a new playlist.
        
        Args:
            title: The playlist title.
            
        Returns:
            Created playlist data.
        """
        try:
            if not title or not title.strip():
                raise ValueError("Playlist title cannot be empty")
                
            playlist = self.playlist_service.create_playlist(title.strip())
            logger.log(LogLevel.INFO, f"Created playlist: {title}")
            return playlist
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error creating playlist '{title}': {str(e)}")
            raise

    def delete_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """
        Delete a playlist.
        
        Args:
            playlist_id: The playlist ID.
            
        Returns:
            Deletion status.
        """
        try:
            # Check if playlist exists
            playlist = self.playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise ValueError(f"Playlist {playlist_id} not found")
                
            success = self.playlist_service.delete_playlist(playlist_id)
            if success:
                logger.log(LogLevel.INFO, f"Deleted playlist: {playlist_id}")
                return {"id": playlist_id, "deleted": True}
            else:
                raise RuntimeError("Failed to delete playlist")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error deleting playlist {playlist_id}: {str(e)}")
            raise

    def reorder_tracks(self, playlist_id: str, track_order: List[int]) -> Dict[str, Any]:
        """
        Reorder tracks in a playlist.
        
        Args:
            playlist_id: The playlist ID.
            track_order: List of track numbers in desired order.
            
        Returns:
            Operation status.
        """
        try:
            if not track_order:
                raise ValueError("Track order cannot be empty")
                
            success = self.playlist_service.reorder_tracks(playlist_id, track_order)
            if success:
                logger.log(LogLevel.INFO, f"Reordered tracks in playlist {playlist_id}")
                return {"status": "success"}
            else:
                raise RuntimeError("Failed to reorder tracks")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error reordering tracks in playlist {playlist_id}: {str(e)}")
            raise

    def delete_tracks(self, playlist_id: str, track_numbers: List[int]) -> Dict[str, Any]:
        """
        Delete tracks from a playlist.
        
        Args:
            playlist_id: The playlist ID.
            track_numbers: List of track numbers to delete.
            
        Returns:
            Operation status.
        """
        try:
            if not track_numbers:
                raise ValueError("Track numbers cannot be empty")
                
            success = self.playlist_service.delete_tracks(playlist_id, track_numbers)
            if success:
                logger.log(LogLevel.INFO, f"Deleted {len(track_numbers)} tracks from playlist {playlist_id}")
                return {"status": "success"}
            else:
                raise RuntimeError("Failed to delete tracks")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error deleting tracks from playlist {playlist_id}: {str(e)}")
            raise

    def start_playlist(self, playlist_id: str, audio_service) -> Dict[str, Any]:
        """
        Start playing a playlist.
        
        Args:
            playlist_id: The playlist ID.
            audio_service: Audio service instance.
            
        Returns:
            Operation status.
        """
        try:
            success = self.playlist_service.start_playlist(playlist_id, audio_service)
            if success:
                logger.log(LogLevel.INFO, f"Started playlist {playlist_id}")
                return {"status": "success"}
            else:
                raise RuntimeError("Failed to start playlist")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error starting playlist {playlist_id}: {str(e)}")
            raise

    def play_track(self, playlist_id: str, track_number: int, audio_service) -> Dict[str, Any]:
        """
        Play a specific track from a playlist.
        
        Args:
            playlist_id: The playlist ID.
            track_number: Track number to play.
            audio_service: Audio service instance.
            
        Returns:
            Operation status.
        """
        try:
            success = self.playlist_service.play_track(playlist_id, track_number, audio_service)
            if success:
                logger.log(LogLevel.INFO, f"Playing track {track_number} from playlist {playlist_id}")
                return {"status": "success"}
            else:
                raise RuntimeError("Failed to play track")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error playing track {track_number} from playlist {playlist_id}: {str(e)}")
            raise

    def associate_nfc_tag(self, playlist_id: str, nfc_tag_id: str) -> Dict[str, Any]:
        """
        Associate an NFC tag with a playlist.
        
        Args:
            playlist_id: The playlist ID.
            nfc_tag_id: The NFC tag ID.
            
        Returns:
            Operation status.
        """
        try:
            success = self.playlist_service.associate_nfc_tag(playlist_id, nfc_tag_id)
            if success:
                logger.log(LogLevel.INFO, f"Associated NFC tag {nfc_tag_id} with playlist {playlist_id}")
                return {"status": "success"}
            else:
                raise RuntimeError("Failed to associate NFC tag")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error associating NFC tag {nfc_tag_id} with playlist {playlist_id}: {str(e)}")
            raise

    def disassociate_nfc_tag(self, playlist_id: str) -> Dict[str, Any]:
        """
        Remove NFC tag association from a playlist.
        
        Args:
            playlist_id: The playlist ID.
            
        Returns:
            Operation status.
        """
        try:
            success = self.playlist_service.disassociate_nfc_tag(playlist_id)
            if success:
                logger.log(LogLevel.INFO, f"Disassociated NFC tag from playlist {playlist_id}")
                return {"status": "success"}
            else:
                raise RuntimeError("Failed to disassociate NFC tag")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error disassociating NFC tag from playlist {playlist_id}: {str(e)}")
            raise

    def get_playlist_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a playlist by its associated NFC tag.
        
        Args:
            nfc_tag_id: The NFC tag ID.
            
        Returns:
            Playlist data or None if not found.
        """
        try:
            return self.playlist_service.get_playlist_by_nfc_tag(nfc_tag_id)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error retrieving playlist by NFC tag {nfc_tag_id}: {str(e)}")
            raise

    def sync_with_filesystem(self) -> Dict[str, Any]:
        """
        Synchronize playlists with the filesystem.
        
        Returns:
            Synchronization statistics.
        """
        try:
            stats = self.playlist_service.sync_with_filesystem()
            logger.log(LogLevel.INFO, f"Filesystem sync completed", extra=stats)
            return {"status": "success", "stats": stats}
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during filesystem sync: {str(e)}")
            raise
