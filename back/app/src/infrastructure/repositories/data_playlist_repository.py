# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Data domain playlist repository implementation."""

from typing import List, Optional, Dict, Any

from app.src.monitoring import get_logger
from app.src.domain.data.protocols.repository_protocol import PlaylistRepositoryProtocol
from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import (
    PureSQLitePlaylistRepository
)

logger = get_logger(__name__)


class DataPlaylistRepository(PlaylistRepositoryProtocol):
    """Data domain adapter for playlist repository."""

    def __init__(self, sqlite_repository: PureSQLitePlaylistRepository):
        """Initialize with the SQLite repository.

        Args:
            sqlite_repository: The underlying SQLite repository
        """
        self._repo = sqlite_repository
        logger.info("✅ DataPlaylistRepository initialized")

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all playlists with pagination."""
        return await self._repo.get_playlists_paginated(skip, limit)

    async def get_by_id(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get a playlist by its ID."""
        return await self._repo.get_playlist_by_id(playlist_id)

    async def get_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """Get a playlist by its associated NFC tag."""
        return await self._repo.get_playlist_by_nfc_tag(nfc_tag_id)

    async def create(self, playlist_data: Dict[str, Any]) -> str:
        """Create a new playlist."""
        return await self._repo.create_playlist(playlist_data)

    async def update(self, playlist_id: str, playlist_data: Dict[str, Any]) -> bool:
        """Update an existing playlist."""
        return await self._repo.update_playlist(playlist_id, playlist_data)

    async def delete(self, playlist_id: str) -> bool:
        """Delete a playlist."""
        return await self._repo.delete_playlist(playlist_id)

    async def exists(self, playlist_id: str) -> bool:
        """Check if a playlist exists."""
        playlist = await self.get_by_id(playlist_id)
        return playlist is not None

    async def count(self) -> int:
        """Count total playlists."""
        return await self._repo.count_playlists()