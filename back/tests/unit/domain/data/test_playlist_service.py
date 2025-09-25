# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unit tests for PlaylistService in data domain."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.src.domain.data.services.playlist_service import PlaylistService


class TestPlaylistService:
    """Test suite for PlaylistService."""

    @pytest.fixture
    def mock_playlist_repo(self):
        """Mock playlist repository."""
        repo = AsyncMock()
        repo.get_all.return_value = []
        repo.get_by_id.return_value = None
        repo.get_by_nfc_tag.return_value = None
        repo.create.return_value = "test-id"
        repo.update.return_value = True
        repo.delete.return_value = True
        repo.exists.return_value = True
        repo.count.return_value = 0
        return repo

    @pytest.fixture
    def mock_track_repo(self):
        """Mock track repository."""
        repo = AsyncMock()
        repo.get_by_playlist.return_value = []
        repo.get_by_id.return_value = None
        repo.add_to_playlist.return_value = "track-id"
        repo.update.return_value = True
        repo.delete.return_value = True
        repo.reorder.return_value = True
        repo.delete_by_playlist.return_value = 0
        return repo

    @pytest.fixture
    def service(self, mock_playlist_repo, mock_track_repo):
        """Create PlaylistService instance with mocked dependencies."""
        return PlaylistService(mock_playlist_repo, mock_track_repo)

    @pytest.mark.asyncio
    async def test_get_playlists_empty(self, service, mock_playlist_repo, mock_track_repo):
        """Test getting playlists when none exist."""
        mock_playlist_repo.get_all.return_value = []
        mock_playlist_repo.count.return_value = 0

        result = await service.get_playlists(page=1, page_size=50)

        assert result['playlists'] == []
        assert result['total'] == 0
        assert result['page'] == 1
        assert result['page_size'] == 50
        assert result['total_pages'] == 0
        mock_playlist_repo.get_all.assert_called_once_with(skip=0, limit=50)

    @pytest.mark.asyncio
    async def test_get_playlists_with_data(self, service, mock_playlist_repo, mock_track_repo):
        """Test getting playlists with data."""
        playlist_data = [
            {'id': 'playlist-1', 'title': 'Test Playlist 1'},
            {'id': 'playlist-2', 'title': 'Test Playlist 2'}
        ]
        mock_playlist_repo.get_all.return_value = playlist_data
        mock_playlist_repo.count.return_value = 2
        mock_track_repo.get_by_playlist.return_value = [
            {'id': 'track-1', 'title': 'Track 1'},
            {'id': 'track-2', 'title': 'Track 2'}
        ]

        result = await service.get_playlists(page=1, page_size=50)

        assert len(result['playlists']) == 2
        assert result['total'] == 2
        assert result['playlists'][0]['track_count'] == 2
        assert result['playlists'][1]['track_count'] == 2

    @pytest.mark.asyncio
    async def test_get_playlist_found(self, service, mock_playlist_repo, mock_track_repo):
        """Test getting a single playlist that exists."""
        playlist_data = {'id': 'playlist-1', 'title': 'Test Playlist'}
        track_data = [{'id': 'track-1', 'title': 'Track 1'}]

        mock_playlist_repo.get_by_id.return_value = playlist_data
        mock_track_repo.get_by_playlist.return_value = track_data

        result = await service.get_playlist('playlist-1')

        assert result['id'] == 'playlist-1'
        assert result['title'] == 'Test Playlist'
        assert len(result['tracks']) == 1
        assert result['track_count'] == 1

    @pytest.mark.asyncio
    async def test_get_playlist_not_found(self, service, mock_playlist_repo, mock_track_repo):
        """Test getting a playlist that doesn't exist."""
        mock_playlist_repo.get_by_id.return_value = None

        result = await service.get_playlist('nonexistent')

        assert result is None

    @pytest.mark.asyncio
    async def test_create_playlist_success(self, service, mock_playlist_repo, mock_track_repo):
        """Test creating a playlist successfully."""
        playlist_id = str(uuid.uuid4())
        created_playlist = {
            'id': playlist_id,
            'title': 'New Playlist',
            'description': 'Test description',
            'tracks': [],
            'track_count': 0
        }

        mock_playlist_repo.create.return_value = playlist_id
        mock_playlist_repo.get_by_id.return_value = created_playlist
        mock_track_repo.get_by_playlist.return_value = []

        result = await service.create_playlist('New Playlist', 'Test description')

        assert result['title'] == 'New Playlist'
        assert result['description'] == 'Test description'
        assert result['track_count'] == 0
        mock_playlist_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_playlist_success(self, service, mock_playlist_repo, mock_track_repo):
        """Test updating a playlist successfully."""
        playlist_id = 'playlist-1'
        updates = {'title': 'Updated Title'}
        updated_playlist = {
            'id': playlist_id,
            'title': 'Updated Title',
            'tracks': [],
            'track_count': 0
        }

        mock_playlist_repo.exists.return_value = True
        mock_playlist_repo.update.return_value = True
        mock_playlist_repo.get_by_id.return_value = updated_playlist
        mock_track_repo.get_by_playlist.return_value = []

        result = await service.update_playlist(playlist_id, updates)

        assert result['title'] == 'Updated Title'
        mock_playlist_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_playlist_not_found(self, service, mock_playlist_repo, mock_track_repo):
        """Test updating a playlist that doesn't exist."""
        mock_playlist_repo.exists.return_value = False

        with pytest.raises(ValueError, match="Playlist playlist-1 not found"):
            await service.update_playlist('playlist-1', {'title': 'New Title'})

    @pytest.mark.asyncio
    async def test_delete_playlist_success(self, service, mock_playlist_repo, mock_track_repo):
        """Test deleting a playlist successfully."""
        playlist_id = 'playlist-1'

        mock_track_repo.delete_by_playlist.return_value = 3
        mock_playlist_repo.delete.return_value = True

        result = await service.delete_playlist(playlist_id)

        assert result is True
        mock_track_repo.delete_by_playlist.assert_called_once_with(playlist_id)
        mock_playlist_repo.delete.assert_called_once_with(playlist_id)

    @pytest.mark.asyncio
    async def test_delete_playlist_failure(self, service, mock_playlist_repo, mock_track_repo):
        """Test deleting a playlist that fails."""
        playlist_id = 'playlist-1'

        mock_track_repo.delete_by_playlist.return_value = 0
        mock_playlist_repo.delete.return_value = False

        result = await service.delete_playlist(playlist_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_associate_nfc_tag_success(self, service, mock_playlist_repo, mock_track_repo):
        """Test associating an NFC tag successfully."""
        playlist_id = 'playlist-1'
        nfc_tag_id = 'nfc-123'

        mock_playlist_repo.update.return_value = True

        result = await service.associate_nfc_tag(playlist_id, nfc_tag_id)

        assert result is True
        mock_playlist_repo.update.assert_called_once()
        call_args = mock_playlist_repo.update.call_args[0]
        assert call_args[0] == playlist_id
        assert call_args[1]['nfc_tag_id'] == nfc_tag_id

    @pytest.mark.asyncio
    async def test_get_playlist_by_nfc_found(self, service, mock_playlist_repo, mock_track_repo):
        """Test getting playlist by NFC tag when it exists."""
        nfc_tag_id = 'nfc-123'
        playlist_data = {'id': 'playlist-1', 'title': 'NFC Playlist'}
        track_data = [{'id': 'track-1', 'title': 'Track 1'}]

        mock_playlist_repo.get_by_nfc_tag.return_value = playlist_data
        mock_track_repo.get_by_playlist.return_value = track_data

        result = await service.get_playlist_by_nfc(nfc_tag_id)

        assert result['id'] == 'playlist-1'
        assert result['track_count'] == 1

    @pytest.mark.asyncio
    async def test_get_playlist_by_nfc_not_found(self, service, mock_playlist_repo, mock_track_repo):
        """Test getting playlist by NFC tag when it doesn't exist."""
        mock_playlist_repo.get_by_nfc_tag.return_value = None

        result = await service.get_playlist_by_nfc('nonexistent-nfc')

        assert result is None

    @pytest.mark.asyncio
    async def test_sync_with_filesystem_no_folder(self, service, mock_playlist_repo, mock_track_repo):
        """Test filesystem sync when upload folder doesn't exist."""
        result = await service.sync_with_filesystem('/nonexistent/path')

        expected_stats = {
            'playlists_scanned': 0,
            'playlists_added': 0,
            'playlists_updated': 0,
            'tracks_added': 0,
            'tracks_removed': 0
        }
        assert result == expected_stats