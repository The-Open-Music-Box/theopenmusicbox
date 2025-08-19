# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Refactored PlaylistService that orchestrates specialized services.

This service acts as a facade that delegates to specialized services for
different aspects of playlist management, following the Single Responsibility
Principle and dependency injection patterns.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime, timezone

from app.src.interfaces.playlist_service_interface import PlaylistServiceInterface
from app.src.model.playlist import Playlist
from app.src.model.track import Track
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.playlist_crud_service import PlaylistCrudService
from app.src.services.track_management_service import TrackManagementService
from app.src.services.nfc_association_service import NfcAssociationService
from app.src.services.filesystem_sync_service import FilesystemSyncService

logger = ImprovedLogger(__name__)


class PlaylistService(PlaylistServiceInterface):
    """
    Orchestrating service for playlist management.
    
    This service implements the PlaylistServiceInterface by delegating
    to specialized services for different aspects of playlist management.
    It maintains backward compatibility while providing a clean, modular
    architecture.
    """

    def __init__(self, config_obj=None):
        """
        Initialize the PlaylistService with specialized services.
        
        Args:
            config_obj: Optional configuration object. If not provided, uses global config.
        """
        from app.src.config import config as global_config

        self.config = config_obj or global_config
        
        # Initialize specialized services
        self.crud_service = PlaylistCrudService(config_obj)
        self.track_service = TrackManagementService(config_obj)
        self.nfc_service = NfcAssociationService(config_obj)
        self.sync_service = FilesystemSyncService(config_obj)
        
        self.upload_folder = Path(self.config.upload_folder)

    # === PlaylistServiceInterface Implementation ===

    def get_all_playlists(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """Retrieve all playlists with pagination support."""
        return self.crud_service.get_all_playlists(page, page_size)

    def get_playlist_by_id(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a playlist by its ID."""
        return self.crud_service.get_playlist_by_id(playlist_id)

    def create_playlist(self, title: str) -> Dict[str, Any]:
        """Create a new playlist."""
        return self.crud_service.create_playlist(title)

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist."""
        try:
            result = self.crud_service.delete_playlist(playlist_id)
            return result.get("deleted", False)
        except ValueError:
            return False

    def update_playlist(self, playlist_id: str, updates: Dict[str, Any]) -> bool:
        """Update playlist metadata."""
        try:
            playlist = self.crud_service.get_playlist_by_id(playlist_id)
            if not playlist:
                return False
            
            # Apply updates
            playlist.update(updates)
            return self.crud_service.save_playlist_file(playlist_id, playlist)
        except (ValueError, TypeError, KeyError) as e:
            logger.log(LogLevel.ERROR, f"Error updating playlist {playlist_id}: {str(e)}")
            return False

    # === Track Management Delegation ===

    def reorder_tracks(self, playlist_id: str, track_order: List[int]) -> bool:
        """Reorder tracks in a playlist."""
        return self.track_service.reorder_tracks(playlist_id, track_order)

    def delete_tracks(self, playlist_id: str, track_numbers: List[int]) -> bool:
        """Delete tracks from a playlist."""
        return self.track_service.delete_tracks(playlist_id, track_numbers)

    # === NFC Association Delegation ===

    def get_playlist_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a playlist by its associated NFC tag ID."""
        return self.nfc_service.get_playlist_by_nfc_tag(nfc_tag_id)

    def associate_nfc_tag(self, playlist_id: str, nfc_tag_id: str) -> bool:
        """Associate an NFC tag with a playlist."""
        return self.nfc_service.associate_nfc_tag(playlist_id, nfc_tag_id)

    def disassociate_nfc_tag(self, playlist_id: str) -> bool:
        """Remove the association of an NFC tag from a playlist."""
        return self.nfc_service.disassociate_nfc_tag(playlist_id)

    # === Filesystem Synchronization Delegation ===

    def create_playlist_from_folder(self, folder_path: Path, title: Optional[str] = None) -> Optional[str]:
        """Create a playlist from a folder of audio files."""
        return self.sync_service.create_playlist_from_folder(folder_path, title)

    def update_playlist_tracks(self, playlist_id: str, folder_path: Path) -> Tuple[bool, Dict[str, int]]:
        """Update the tracks of a playlist from the contents of a folder."""
        return self.sync_service.update_playlist_tracks(playlist_id, folder_path)

    def sync_with_filesystem(self) -> Dict[str, int]:
        """Synchronize playlists in the database with the filesystem."""
        return self.sync_service.sync_with_filesystem()

    # === Backward Compatibility Methods ===

    def save_playlist_file(self, playlist_id: str, playlist_data=None) -> bool:
        """Save the changes to a playlist."""
        return self.crud_service.save_playlist_file(playlist_id, playlist_data)

    def to_model(self, playlist_data: Dict[str, Any]) -> Playlist:
        """Convert playlist data to a Playlist model object."""
        tracks = []
        for track_data in playlist_data.get("tracks", []):
            file_path = Path(
                self.upload_folder.parent, playlist_data["path"], track_data["filename"]
            )
            track = Track(
                number=track_data["number"],
                title=track_data.get("title", f"Track {track_data['number']}"),
                filename=track_data["filename"],
                path=file_path,
                duration=track_data.get("duration"),
                artist=track_data.get("artist"),
                album=track_data.get("album"),
                id=track_data.get("id"),
            )
            tracks.append(track)

        return Playlist(
            name=playlist_data["title"],
            tracks=tracks,
            description=playlist_data.get("description"),
            id=playlist_data["id"],
            nfc_tag_id=playlist_data.get("nfc_tag_id"),
        )

    def from_model(self, playlist: Playlist) -> Dict[str, Any]:
        """Convert a Playlist model object to a dictionary for storage."""
        # Compute the relative path for the playlist
        if playlist.tracks and playlist.tracks[0].path:
            folder_path = playlist.tracks[0].path.parent
            try:
                rel_path = folder_path.relative_to(self.upload_folder.parent)
            except ValueError:
                rel_path = Path(self.config.upload_folder) / playlist.name.lower().replace(" ", "_")
        else:
            rel_path = Path(self.config.upload_folder) / playlist.name.lower().replace(" ", "_")

        # Build the playlist dictionary
        playlist_data = {
            "id": playlist.id or str(uuid4()),
            "type": "playlist",
            "title": playlist.name,
            "path": str(rel_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "nfc_tag_id": playlist.nfc_tag_id,
            "tracks": [],
        }

        # Add all tracks
        for track in playlist.tracks:
            track_data = {
                "number": track.number,
                "title": track.title,
                "filename": track.filename,
                "duration": track.duration,
                "artist": track.artist,
                "album": track.album,
                "play_counter": 0,
            }
            playlist_data["tracks"].append(track_data)

        return playlist_data

    # === Audio Playback Methods ===

    def play_playlist_with_validation(self, playlist_data: Dict[str, Any], audio) -> bool:
        """Play a playlist using the audio player with validation."""
        try:
            playlist_obj = self.to_model(playlist_data)
            if not playlist_obj.tracks:
                logger.log(
                    LogLevel.WARNING,
                    f"No valid tracks in playlist: {playlist_data.get('title', playlist_data.get('id'))}"
                )
                return False
                
            valid_tracks = [track for track in playlist_obj.tracks if track.path.exists()]
            if not valid_tracks:
                logger.log(
                    LogLevel.WARNING,
                    f"No accessible tracks in playlist: {playlist_data.get('title', playlist_data.get('id'))}"
                )
                return False
                
            playlist_obj.tracks = valid_tracks
            result = audio.set_playlist(playlist_obj)
            
            if result:
                logger.log(
                    LogLevel.INFO,
                    f"Started playlist: {playlist_obj.name} with {len(valid_tracks)} tracks"
                )
                # Update last played timestamp
                self.update_playlist(playlist_data["id"], {"last_played": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
                return True
            else:
                logger.log(LogLevel.WARNING, f"Failed to start playlist: {playlist_obj.name}")
                return False
                
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.log(LogLevel.ERROR, f"Error playing playlist: {str(e)}")
            return False

    def start_playlist(self, playlist_id: str, audio) -> bool:
        """Start playback of the specified playlist."""
        playlist_data = self.get_playlist_by_id(playlist_id)
        if not playlist_data:
            logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
            return False
        return self.play_playlist_with_validation(playlist_data, audio)

    def play_track(self, playlist_id: str, track_number: int, audio) -> bool:
        """Play a specific track from a playlist."""
        playlist_data = self.get_playlist_by_id(playlist_id)
        if not playlist_data or not playlist_data.get("tracks"):
            logger.log(LogLevel.WARNING, f"Playlist or tracks not found for id: {playlist_id}")
            return False
            
        track = next((t for t in playlist_data["tracks"] if t["number"] == track_number), None)
        if not track:
            logger.log(LogLevel.WARNING, f"Track {track_number} not found in playlist {playlist_id}")
            return False
            
        audio.play_track(track_number)
        return True

    def add_playlist(self, playlist_data: Dict[str, Any]) -> str:
        """Add a new playlist with the provided data (for YouTube service)."""
        try:
            playlist_id = str(uuid4())
            
            formatted_playlist = {
                "id": playlist_id,
                "type": "playlist",
                "title": playlist_data.get("title", "YouTube Download"),
                "path": playlist_data.get("folder", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "youtube_id": playlist_data.get("youtube_id"),
                "tracks": [],
            }

            # Process tracks if available
            tracks = playlist_data.get("tracks", [])
            for i, track_data in enumerate(tracks, 1):
                track = {
                    "number": i,
                    "title": track_data.get("title", f"Track {i}"),
                    "filename": track_data.get("filename", ""),
                    "duration": track_data.get("duration", 0),
                    "artist": track_data.get("artist", "YouTube"),
                    "album": track_data.get("album", formatted_playlist["title"]),
                    "play_counter": 0,
                }
                formatted_playlist["tracks"].append(track)

            # Use CRUD service to create the playlist
            self.crud_service.repository.create_playlist(formatted_playlist)
            logger.log(LogLevel.INFO, f"Created playlist from YouTube download: {formatted_playlist['title']}")
            return playlist_id

        except (ValueError, TypeError, KeyError) as e:
            logger.log(LogLevel.ERROR, f"Error adding playlist from YouTube data: {str(e)}")
            raise
