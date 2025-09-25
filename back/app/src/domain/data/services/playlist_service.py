# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Playlist service for data domain."""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.src.monitoring import get_logger
from app.src.domain.decorators.error_handler import handle_domain_errors
from app.src.domain.data.protocols.repository_protocol import (
    PlaylistRepositoryProtocol,
    TrackRepositoryProtocol
)
from app.src.domain.data.protocols.service_protocol import PlaylistServiceProtocol

logger = get_logger(__name__)


class PlaylistService(PlaylistServiceProtocol):
    """Service for managing playlist data operations."""

    def __init__(
        self,
        playlist_repository: PlaylistRepositoryProtocol,
        track_repository: TrackRepositoryProtocol
    ):
        """Initialize the playlist service.

        Args:
            playlist_repository: Repository for playlist operations
            track_repository: Repository for track operations
        """
        self._playlist_repo = playlist_repository
        self._track_repo = track_repository
        logger.info("✅ PlaylistService initialized in data domain")

    @handle_domain_errors(operation_name="get_playlists")
    async def get_playlists(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get paginated playlists.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with playlists and pagination info
        """
        skip = (page - 1) * page_size

        # Get playlists and total count
        playlists = await self._playlist_repo.get_all(skip=skip, limit=page_size)
        total = await self._playlist_repo.count()

        # Add track count for each playlist
        for playlist in playlists:
            tracks = await self._track_repo.get_by_playlist(playlist['id'])
            playlist['track_count'] = len(tracks)

        return {
            'playlists': playlists,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    @handle_domain_errors(operation_name="get_playlist")
    async def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get a single playlist with its tracks.

        Args:
            playlist_id: The playlist ID

        Returns:
            Playlist data with tracks or None
        """
        playlist = await self._playlist_repo.get_by_id(playlist_id)
        if not playlist:
            return None

        # Get tracks for the playlist
        tracks = await self._track_repo.get_by_playlist(playlist_id)
        playlist['tracks'] = tracks
        playlist['track_count'] = len(tracks)

        return playlist

    @handle_domain_errors(operation_name="create_playlist")
    async def create_playlist(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new playlist.

        Args:
            name: Playlist name
            description: Optional description

        Returns:
            Created playlist data
        """
        playlist_id = str(uuid.uuid4())
        playlist_data = {
            'id': playlist_id,
            'title': name,
            'description': description or '',
            'type': 'album',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        await self._playlist_repo.create(playlist_data)
        logger.info(f"✅ Created playlist: {name} (ID: {playlist_id})")

        return await self.get_playlist(playlist_id)

    @handle_domain_errors(operation_name="update_playlist")
    async def update_playlist(self, playlist_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update playlist metadata.

        Args:
            playlist_id: The playlist ID
            updates: Dictionary of updates

        Returns:
            Updated playlist data
        """
        # Check if playlist exists
        if not await self._playlist_repo.exists(playlist_id):
            raise ValueError(f"Playlist {playlist_id} not found")

        # Add updated timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()

        success = await self._playlist_repo.update(playlist_id, updates)
        if not success:
            raise RuntimeError(f"Failed to update playlist {playlist_id}")

        logger.info(f"✅ Updated playlist {playlist_id}")
        return await self.get_playlist(playlist_id)

    @handle_domain_errors(operation_name="delete_playlist")
    async def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist and all its tracks.

        Args:
            playlist_id: The playlist ID

        Returns:
            True if successful
        """
        # Delete all tracks first
        deleted_tracks = await self._track_repo.delete_by_playlist(playlist_id)
        logger.info(f"Deleted {deleted_tracks} tracks from playlist {playlist_id}")

        # Delete the playlist
        success = await self._playlist_repo.delete(playlist_id)
        if success:
            logger.info(f"✅ Deleted playlist {playlist_id}")
        else:
            logger.warning(f"Failed to delete playlist {playlist_id}")

        return success

    @handle_domain_errors(operation_name="associate_nfc_tag")
    async def associate_nfc_tag(self, playlist_id: str, nfc_tag_id: str) -> bool:
        """Associate an NFC tag with a playlist.

        Args:
            playlist_id: The playlist ID
            nfc_tag_id: The NFC tag ID

        Returns:
            True if successful
        """
        updates = {
            'nfc_tag_id': nfc_tag_id,
            'updated_at': datetime.utcnow().isoformat()
        }

        success = await self._playlist_repo.update(playlist_id, updates)
        if success:
            logger.info(f"✅ Associated NFC tag {nfc_tag_id} with playlist {playlist_id}")

        return success

    @handle_domain_errors(operation_name="get_playlist_by_nfc")
    async def get_playlist_by_nfc(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist associated with an NFC tag.

        Args:
            nfc_tag_id: The NFC tag ID

        Returns:
            Playlist data or None
        """
        playlist = await self._playlist_repo.get_by_nfc_tag(nfc_tag_id)
        if playlist:
            tracks = await self._track_repo.get_by_playlist(playlist['id'])
            playlist['tracks'] = tracks
            playlist['track_count'] = len(tracks)

        return playlist

    @handle_domain_errors(operation_name="sync_with_filesystem")
    async def sync_with_filesystem(self, upload_folder: str) -> Dict[str, Any]:
        """Synchronize playlists with filesystem.

        Args:
            upload_folder: Path to the upload folder

        Returns:
            Synchronization statistics
        """
        stats = {
            'playlists_scanned': 0,
            'playlists_added': 0,
            'playlists_updated': 0,
            'tracks_added': 0,
            'tracks_removed': 0
        }

        upload_path = Path(upload_folder)
        if not upload_path.exists():
            logger.warning(f"Upload folder does not exist: {upload_folder}")
            return stats

        # Scan all directories in upload folder
        for playlist_dir in upload_path.iterdir():
            if not playlist_dir.is_dir():
                continue

            stats['playlists_scanned'] += 1
            playlist_name = playlist_dir.name

            # Check if playlist already exists
            existing_playlists = await self._playlist_repo.get_all()
            existing = next(
                (p for p in existing_playlists if p['title'] == playlist_name),
                None
            )

            if existing:
                # Update tracks for existing playlist
                await self._sync_playlist_tracks(existing['id'], playlist_dir, stats)
            else:
                # Create new playlist
                playlist = await self.create_playlist(
                    name=playlist_name,
                    description=f"Auto-imported from {playlist_dir.name}"
                )
                stats['playlists_added'] += 1
                await self._sync_playlist_tracks(playlist['id'], playlist_dir, stats)

        logger.info(f"✅ Filesystem sync completed: {stats}")
        return stats

    async def _sync_playlist_tracks(self, playlist_id: str, playlist_dir: Path, stats: Dict[str, Any]):
        """Synchronize tracks for a playlist.

        Args:
            playlist_id: The playlist ID
            playlist_dir: Directory containing audio files
            stats: Statistics dictionary to update
        """
        # Get audio files
        audio_extensions = {'.mp3', '.flac', '.wav', '.m4a', '.ogg'}
        audio_files = sorted([
            f for f in playlist_dir.iterdir()
            if f.is_file() and f.suffix.lower() in audio_extensions
        ])

        # Get existing tracks
        existing_tracks = await self._track_repo.get_by_playlist(playlist_id)
        existing_files = {t['filename'] for t in existing_tracks if t.get('filename')}

        # Add new tracks
        for idx, audio_file in enumerate(audio_files, 1):
            if audio_file.name not in existing_files:
                track_data = {
                    'id': str(uuid.uuid4()),
                    'playlist_id': playlist_id,
                    'track_number': idx,
                    'title': audio_file.stem,
                    'filename': audio_file.name,
                    'file_path': str(audio_file),
                    'created_at': datetime.utcnow().isoformat()
                }
                await self._track_repo.add_to_playlist(playlist_id, track_data)
                stats['tracks_added'] += 1

        # Remove tracks that no longer exist
        current_files = {f.name for f in audio_files}
        for track in existing_tracks:
            if track.get('filename') and track['filename'] not in current_files:
                await self._track_repo.delete(track['id'])
                stats['tracks_removed'] += 1