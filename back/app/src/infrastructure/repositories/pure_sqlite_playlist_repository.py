# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Pure DDD SQLite Playlist Repository

Clean implementation of playlist repository following DDD principles.
Uses DatabaseManager for connection management and focuses only on data access.
"""

import uuid
from typing import List, Optional

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track
from app.src.domain.repositories.playlist_repository_interface import PlaylistRepositoryInterface
from app.src.data.database_manager import get_database_manager
from app.src.services.error.unified_error_decorator import handle_repository_errors

logger = get_logger(__name__)


class PureSQLitePlaylistRepository(PlaylistRepositoryInterface):
    """Pure DDD SQLite playlist repository implementation.

    This repository implementation follows DDD principles:
    - Only handles data persistence concerns
    - Uses DatabaseManager for all connection management
    - No mixed concerns (transaction management is in DatabaseService)
    - Implements domain repository interface
    """

    def __init__(self):
        """Initialize pure DDD playlist repository.

        Gets database service from DatabaseManager singleton.
        No direct database path management - delegated to infrastructure service.
        """
        self._database_manager = get_database_manager()
        self._db_service = self._database_manager.database_service
        logger.log(LogLevel.INFO, "✅ Pure DDD SQLite Playlist Repository initialized")

    @handle_repository_errors("playlist")
    async def save(self, playlist: Playlist) -> Playlist:
        """Save a playlist using pure DDD principles.

        Args:
            playlist: Playlist domain entity to save

        Returns:
            Saved playlist entity with ID assigned
        """
        # Assign ID if not present (domain concern)
        if not playlist.id:
            playlist.id = str(uuid.uuid4())

        # Save playlist data with consistent path generation
        from app.src.utils.path_utils import normalize_folder_name
        path = normalize_folder_name(playlist.name)

        playlist_command = """
            INSERT OR REPLACE INTO playlists
            (id, title, description, nfc_tag_id, path, type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        playlist_params = (
            playlist.id,
            playlist.name,
            playlist.description,
            playlist.nfc_tag_id,
            path,
            "album",
        )

        # Prepare batch operations for atomic transaction
        operations = [
            {
                "query": playlist_command,
                "params": playlist_params,
                "type": "command"
            },
            {
                "query": "DELETE FROM tracks WHERE playlist_id = ?",
                "params": (playlist.id,),
                "type": "command"
            }
        ]

        # Add track insertions
        for track in playlist.tracks:
            track_command = """
                INSERT INTO tracks
                (id, playlist_id, track_number, title, filename, file_path, duration_ms, artist, album, created_at, updated_at, play_count, server_seq)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0)
            """
            track_params = (
                track.id or str(uuid.uuid4()),
                playlist.id,
                track.track_number,
                track.title,
                track.filename,
                track.file_path,
                track.duration_ms,
                track.artist,
                track.album,
            )
            operations.append({
                "query": track_command,
                "params": track_params,
                "type": "command"
            })

        # Execute all operations in a single transaction
        self._db_service.execute_batch(operations, f"save_playlist_{playlist.id}")

        logger.log(LogLevel.INFO, f"✅ Saved playlist: {playlist.name}")
        return playlist

    @handle_repository_errors("playlist")
    async def find_by_id(self, playlist_id: str) -> Optional[Playlist]:
        """Find playlist by ID using pure DDD principles.

        Args:
            playlist_id: Unique identifier

        Returns:
            Playlist domain entity or None if not found
        """
        # Get playlist data
        playlist_query = "SELECT * FROM playlists WHERE id = ?"
        playlist_row = self._db_service.execute_single(
            playlist_query,
            (playlist_id,),
            f"find_playlist_{playlist_id}"
        )

        if not playlist_row:
            return None

        # Get tracks data
        tracks_query = """
            SELECT * FROM tracks
            WHERE playlist_id = ?
            ORDER BY track_number
        """
        track_rows = self._db_service.execute_query(
            tracks_query,
            (playlist_id,),
            f"find_tracks_for_playlist_{playlist_id}"
        )

        return self._build_playlist_from_rows(playlist_row, track_rows)

    @handle_repository_errors("playlist")
    async def find_by_name(self, name: str) -> Optional[Playlist]:
        """Find playlist by name using pure DDD principles.

        Args:
            name: Playlist name

        Returns:
            Playlist domain entity or None if not found
        """
        playlist_query = "SELECT * FROM playlists WHERE title = ?"
        playlist_row = self._db_service.execute_single(
            playlist_query,
            (name,),
            f"find_playlist_by_name_{name}"
        )

        if not playlist_row:
            return None

        # Get tracks for this playlist
        tracks_query = """
            SELECT * FROM tracks
            WHERE playlist_id = ?
            ORDER BY track_number
        """
        track_rows = self._db_service.execute_query(
            tracks_query,
            (playlist_row["id"],),
            f"find_tracks_for_playlist_{playlist_row['id']}"
        )

        return self._build_playlist_from_rows(playlist_row, track_rows)

    @handle_repository_errors("playlist")
    async def find_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Playlist]:
        """Find playlist by NFC tag using pure DDD principles.

        Args:
            nfc_tag_id: NFC tag identifier

        Returns:
            Playlist domain entity or None if not found
        """
        playlist_query = "SELECT * FROM playlists WHERE nfc_tag_id = ?"
        playlist_row = self._db_service.execute_single(
            playlist_query,
            (nfc_tag_id,),
            f"find_playlist_by_nfc_{nfc_tag_id}"
        )

        if not playlist_row:
            return None

        # Get tracks for this playlist
        tracks_query = """
            SELECT * FROM tracks
            WHERE playlist_id = ?
            ORDER BY track_number
        """
        track_rows = self._db_service.execute_query(
            tracks_query,
            (playlist_row["id"],),
            f"find_tracks_for_playlist_{playlist_row['id']}"
        )

        return self._build_playlist_from_rows(playlist_row, track_rows)

    @handle_repository_errors("playlist")
    async def find_all(self, limit: int = None, offset: int = 0) -> List[Playlist]:
        """Find all playlists with pagination using pure DDD principles.

        Args:
            limit: Maximum number of playlists to return
            offset: Number of playlists to skip

        Returns:
            List of playlist domain entities
        """
        query = "SELECT * FROM playlists ORDER BY updated_at DESC"
        params = []

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        if offset > 0:
            query += " OFFSET ?"
            params.append(offset)

        playlist_rows = self._db_service.execute_query(
            query,
            tuple(params),
            f"find_all_playlists_limit_{limit}_offset_{offset}"
        )

        playlists = []
        for playlist_row in playlist_rows:
            # Get tracks for each playlist
            tracks_query = """
                SELECT * FROM tracks
                WHERE playlist_id = ?
                ORDER BY track_number
            """
            track_rows = self._db_service.execute_query(
                tracks_query,
                (playlist_row["id"],),
                f"find_tracks_for_playlist_{playlist_row['id']}"
            )

            playlist = self._build_playlist_from_rows(playlist_row, track_rows)
            playlists.append(playlist)

        return playlists

    async def update(self, playlist: Playlist) -> Playlist:
        """Update existing playlist using pure DDD principles.

        Args:
            playlist: Updated playlist domain entity

        Returns:
            Updated playlist entity
        """
        # For this implementation, update is same as save with REPLACE
        return await self.save(playlist)

    @handle_repository_errors("playlist")
    async def delete(self, playlist_id: str) -> bool:
        """Delete playlist by ID using pure DDD principles.

        Args:
            playlist_id: Playlist identifier

        Returns:
            True if deleted, False if not found
        """
        delete_command = "DELETE FROM playlists WHERE id = ?"
        affected_rows = self._db_service.execute_command(
            delete_command,
            (playlist_id,),
            f"delete_playlist_{playlist_id}"
        )

        deleted = affected_rows > 0
        if deleted:
            logger.log(LogLevel.INFO, f"✅ Deleted playlist: {playlist_id}")

        return deleted

    @handle_repository_errors("playlist")
    async def count(self) -> int:
        """Count total playlists using pure DDD principles.

        Returns:
            Total playlist count
        """
        count_query = "SELECT COUNT(*) FROM playlists"
        result = self._db_service.execute_single(count_query, None, "count_playlists")
        return result[0] if result else 0

    @handle_repository_errors("playlist")
    async def search(self, query: str, limit: int = None) -> List[Playlist]:
        """Search playlists by name or description using pure DDD principles.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching playlist domain entities
        """
        search_query = """
            SELECT * FROM playlists
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY updated_at DESC
        """
        params = [f"%{query}%", f"%{query}%"]

        if limit is not None:
            search_query += " LIMIT ?"
            params.append(limit)

        playlist_rows = self._db_service.execute_query(
            search_query,
            tuple(params),
            f"search_playlists_{query}"
        )

        playlists = []
        for playlist_row in playlist_rows:
            # Get tracks for each playlist
            tracks_query = """
                SELECT * FROM tracks
                WHERE playlist_id = ?
                ORDER BY track_number
            """
            track_rows = self._db_service.execute_query(
                tracks_query,
                (playlist_row["id"],),
                f"find_tracks_for_playlist_{playlist_row['id']}"
            )

            playlist = self._build_playlist_from_rows(playlist_row, track_rows)
            playlists.append(playlist)

        return playlists

    @handle_repository_errors("playlist")
    async def update_nfc_tag_association(self, playlist_id: str, nfc_tag_id: str) -> bool:
        """Update NFC tag association for a playlist.

        Args:
            playlist_id: Playlist ID to associate
            nfc_tag_id: NFC tag identifier

        Returns:
            True if update successful, False otherwise
        """
        # Execute operations in batch transaction for atomicity
        operations = [
            {
                "query": "UPDATE playlists SET nfc_tag_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE nfc_tag_id = ?",
                "params": (nfc_tag_id,),
                "type": "command"
            },
            {
                "query": "UPDATE playlists SET nfc_tag_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                "params": (nfc_tag_id, playlist_id),
                "type": "command"
            }
        ]

        results = self._db_service.execute_batch(
            operations,
            f"update_nfc_association_{playlist_id}_{nfc_tag_id}"
        )

        # Check if the second operation (actual association) affected any rows
        success = results[1] > 0 if len(results) > 1 else False

        if success:
            logger.log(
                LogLevel.INFO,
                f"✅ Updated playlist {playlist_id} with NFC tag {nfc_tag_id}"
            )
        else:
            logger.log(
                LogLevel.WARNING,
                f"⚠️ No playlist found with ID {playlist_id}"
            )

        return success

    @handle_repository_errors("playlist")
    async def remove_nfc_tag_association(self, nfc_tag_id: str) -> bool:
        """Remove NFC tag association from any playlist.

        Args:
            nfc_tag_id: NFC tag identifier to unassociate

        Returns:
            True if removal successful
        """
        remove_command = """
            UPDATE playlists
            SET nfc_tag_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE nfc_tag_id = ?
        """

        self._db_service.execute_command(
            remove_command,
            (nfc_tag_id,),
            f"remove_nfc_association_{nfc_tag_id}"
        )

        logger.log(LogLevel.INFO, f"✅ Removed NFC tag {nfc_tag_id} from all playlists")
        return True

    @handle_repository_errors("playlist")
    async def update_track_numbers(self, playlist_id: str, track_number_mapping: dict) -> bool:
        """Update track numbers for tracks in a playlist.

        This method efficiently updates track numbers using UPDATE statements
        instead of deleting and reinserting tracks.

        Args:
            playlist_id: Playlist identifier
            track_number_mapping: Dictionary mapping old track numbers to new track numbers

        Returns:
            True if successful, False otherwise
        """
        if not track_number_mapping:
            logger.log(LogLevel.WARNING, "Empty track number mapping provided")
            return False

        try:
            # Use transaction to ensure atomicity
            async def update_operation():
                # First, temporarily set all track numbers to negative values to avoid conflicts
                temp_mapping = {}
                for old_num, new_num in track_number_mapping.items():
                    temp_mapping[old_num] = -new_num

                # Step 1: Update to temporary negative values
                for old_num, temp_num in temp_mapping.items():
                    await self._db_service.execute(
                        """
                        UPDATE tracks
                        SET track_number = ?
                        WHERE playlist_id = ? AND track_number = ?
                        """,
                        (temp_num, playlist_id, old_num),
                        f"temp_update_track_{playlist_id}_{old_num}"
                    )

                # Step 2: Update from temporary values to final values
                for old_num, new_num in track_number_mapping.items():
                    await self._db_service.execute(
                        """
                        UPDATE tracks
                        SET track_number = ?
                        WHERE playlist_id = ? AND track_number = ?
                        """,
                        (new_num, playlist_id, -new_num),
                        f"final_update_track_{playlist_id}_{new_num}"
                    )

                return True

            # Execute within transaction
            result = await self._db_service.transaction(update_operation)

            if result:
                logger.log(
                    LogLevel.INFO,
                    f"✅ Updated track numbers for playlist {playlist_id}: {len(track_number_mapping)} tracks reordered"
                )
            else:
                logger.log(
                    LogLevel.ERROR,
                    f"❌ Failed to update track numbers for playlist {playlist_id}"
                )

            return result

        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"❌ Error updating track numbers for playlist {playlist_id}: {e}"
            )
            return False

    def _build_playlist_from_rows(self, playlist_row, track_rows) -> Playlist:
        """Build playlist domain entity from database rows.

        Args:
            playlist_row: SQLite playlist row
            track_rows: List of SQLite track rows

        Returns:
            Playlist domain entity
        """
        tracks = []
        for track_row in track_rows:
            # Generate file_path if missing but filename exists
            file_path = track_row["file_path"] if track_row["file_path"] else ""
            filename = track_row["filename"] if track_row["filename"] else ""

            if not file_path and filename:
                # Use playlist title to generate file_path
                playlist_folder = (
                    playlist_row["title"]
                    if playlist_row["title"]
                    else "Unknown"
                )
                try:
                    from app.src.config import config
                    from pathlib import Path

                    file_path = str(Path(config.upload_folder) / playlist_folder / filename)
                except:
                    # Fallback if config not available
                    file_path = f"./uploads/{playlist_folder}/{filename}"

            track = Track(
                id=track_row["id"],
                track_number=track_row["track_number"] if track_row["track_number"] else 1,
                title=track_row["title"] if track_row["title"] else "Unknown",
                filename=filename,
                file_path=file_path,
                duration_ms=track_row["duration_ms"] if track_row["duration_ms"] else None,
                artist=track_row["artist"] if track_row["artist"] else None,
                album=track_row["album"] if track_row["album"] else None,
            )
            tracks.append(track)

        # Build playlist domain entity
        playlist = Playlist(
            id=playlist_row["id"],
            name=playlist_row["title"],  # Legacy schema uses 'title'
            description=playlist_row["description"],
            nfc_tag_id=playlist_row["nfc_tag_id"],
            path=playlist_row["path"],
            tracks=tracks,
        )

        return playlist