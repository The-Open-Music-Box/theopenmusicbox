# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Test playlist deletion with filesystem folder cleanup.

Verifies that when a playlist is deleted via the API, its associated folder
in the uploads directory is also removed from the filesystem.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.src.infrastructure.adapters.pure_playlist_repository_adapter import PurePlaylistRepositoryAdapter
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track


class TestPlaylistDeleteFolderCleanup:
    """Test that playlist deletion includes filesystem cleanup."""

    def setup_method(self):
        """Set up test with temporary upload folder."""
        # Create temporary upload directory
        self.temp_upload_dir = tempfile.mkdtemp()

        # Mock the repository and config
        self.mock_repository = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.upload_folder = self.temp_upload_dir

    def teardown_method(self):
        """Clean up temporary directories."""
        import shutil
        if os.path.exists(self.temp_upload_dir):
            shutil.rmtree(self.temp_upload_dir)

    @pytest.mark.asyncio
    async def test_delete_playlist_removes_associated_folder(self):
        """Test that deleting a playlist removes its folder from uploads directory."""
        playlist_id = "test-playlist-123"

        # Create test playlist folder with some files
        playlist_folder = Path(self.temp_upload_dir) / playlist_id
        playlist_folder.mkdir(parents=True)
        (playlist_folder / "track1.mp3").touch()
        (playlist_folder / "track2.mp3").touch()

        # Verify folder exists
        assert playlist_folder.exists()
        assert len(list(playlist_folder.iterdir())) == 2

        # Create playlist domain object
        playlist = Playlist(name="Test Playlist", id=playlist_id)

        # Mock repository responses - make them async
        async def mock_find_by_id(id):
            return playlist

        async def mock_delete(id):
            return True

        self.mock_repository.find_by_id = mock_find_by_id
        self.mock_repository.delete = mock_delete

        # Patch dependencies and error decorator
        with patch('app.src.dependencies.get_config', return_value=self.mock_config):
            with patch('app.src.services.error.unified_error_decorator.handle_repository_errors',
                       side_effect=lambda operation_name: lambda func: func):
                with patch.object(PurePlaylistRepositoryAdapter, '_repo', self.mock_repository):
                    adapter = PurePlaylistRepositoryAdapter()
                    adapter._repository = self.mock_repository

                    # Act - delete playlist
                    result = await adapter.delete_playlist(playlist_id)

        # Assert
        assert result is True
        assert not playlist_folder.exists()  # Folder should be removed

        # Verify repository was called
        assert playlist_folder  # Mock verification

    @pytest.mark.asyncio
    async def test_delete_playlist_handles_missing_folder_gracefully(self):
        """Test that deletion succeeds even if folder doesn't exist."""
        playlist_id = "nonexistent-folder-playlist"

        # Create playlist domain object
        playlist = Playlist(name="Test Playlist", id=playlist_id)

        # Mock repository responses
        self.mock_repository.find_by_id.return_value = playlist
        self.mock_repository.delete.return_value = True

        # Patch dependencies
        with patch('app.src.dependencies.get_config', return_value=self.mock_config):
            with patch.object(PurePlaylistRepositoryAdapter, '_repo', self.mock_repository):
                adapter = PurePlaylistRepositoryAdapter()
                adapter._repository = self.mock_repository

                # Act - delete playlist (no folder exists)
                result = await adapter.delete_playlist(playlist_id)

        # Assert - should succeed even with no folder
        assert result is True

        # Verify repository was called
        self.mock_repository.find_by_id.assert_called_once_with(playlist_id)
        self.mock_repository.delete.assert_called_once_with(playlist_id)

    @pytest.mark.asyncio
    async def test_delete_playlist_handles_folder_cleanup_error_gracefully(self):
        """Test that database deletion succeeds even if folder cleanup fails."""
        playlist_id = "cleanup-error-playlist"

        # Create test playlist folder
        playlist_folder = Path(self.temp_upload_dir) / playlist_id
        playlist_folder.mkdir(parents=True)
        (playlist_folder / "track.mp3").touch()

        # Create playlist domain object
        playlist = Playlist(name="Test Playlist", id=playlist_id)

        # Mock repository responses
        self.mock_repository.find_by_id.return_value = playlist
        self.mock_repository.delete.return_value = True

        # Mock shutil.rmtree to raise an exception
        with patch('shutil.rmtree', side_effect=PermissionError("Cannot delete folder")):
            with patch('app.src.infrastructure.adapters.pure_playlist_repository_adapter.get_config', return_value=self.mock_config):
                with patch.object(PurePlaylistRepositoryAdapter, '_repo', self.mock_repository):
                    adapter = PurePlaylistRepositoryAdapter()
                    adapter._repository = self.mock_repository

                    # Act - delete playlist (folder cleanup will fail)
                    result = await adapter.delete_playlist(playlist_id)

        # Assert - database deletion should still succeed
        assert result is True
        assert playlist_folder.exists()  # Folder should still exist due to cleanup failure

        # Verify repository was called
        self.mock_repository.find_by_id.assert_called_once_with(playlist_id)
        self.mock_repository.delete.assert_called_once_with(playlist_id)

    @pytest.mark.asyncio
    async def test_delete_playlist_skips_cleanup_if_database_delete_fails(self):
        """Test that folder cleanup is skipped if database deletion fails."""
        playlist_id = "db-delete-fail-playlist"

        # Create test playlist folder
        playlist_folder = Path(self.temp_upload_dir) / playlist_id
        playlist_folder.mkdir(parents=True)
        (playlist_folder / "track.mp3").touch()

        # Create playlist domain object
        playlist = Playlist(name="Test Playlist", id=playlist_id)

        # Mock repository responses - database delete fails
        self.mock_repository.find_by_id.return_value = playlist
        self.mock_repository.delete.return_value = False

        # Patch dependencies
        with patch('app.src.dependencies.get_config', return_value=self.mock_config):
            with patch.object(PurePlaylistRepositoryAdapter, '_repo', self.mock_repository):
                adapter = PurePlaylistRepositoryAdapter()
                adapter._repository = self.mock_repository

                # Act - delete playlist (database delete will fail)
                result = await adapter.delete_playlist(playlist_id)

        # Assert - operation should fail and folder should remain
        assert result is False
        assert playlist_folder.exists()  # Folder should remain since DB delete failed

        # Verify repository was called
        self.mock_repository.find_by_id.assert_called_once_with(playlist_id)
        self.mock_repository.delete.assert_called_once_with(playlist_id)

    @pytest.mark.asyncio
    async def test_delete_playlist_handles_nested_folder_structure(self):
        """Test deletion of playlist with nested folder structure."""
        playlist_id = "nested-structure-playlist"

        # Create test playlist folder with nested structure
        playlist_folder = Path(self.temp_upload_dir) / playlist_id
        playlist_folder.mkdir(parents=True)

        # Create nested folders and files
        sub_folder = playlist_folder / "artist" / "album"
        sub_folder.mkdir(parents=True)
        (sub_folder / "track1.mp3").touch()
        (sub_folder / "track2.mp3").touch()
        (playlist_folder / "cover.jpg").touch()

        # Verify complex structure exists
        assert playlist_folder.exists()
        assert sub_folder.exists()
        assert len(list(playlist_folder.rglob("*"))) >= 4  # At least 4 items (2 dirs + 3 files)

        # Create playlist domain object
        playlist = Playlist(name="Nested Playlist", id=playlist_id)

        # Mock repository responses
        self.mock_repository.find_by_id.return_value = playlist
        self.mock_repository.delete.return_value = True

        # Patch dependencies
        with patch('app.src.dependencies.get_config', return_value=self.mock_config):
            with patch.object(PurePlaylistRepositoryAdapter, '_repo', self.mock_repository):
                adapter = PurePlaylistRepositoryAdapter()
                adapter._repository = self.mock_repository

                # Act - delete playlist
                result = await adapter.delete_playlist(playlist_id)

        # Assert - entire nested structure should be removed
        assert result is True
        assert not playlist_folder.exists()  # Entire folder tree should be gone

        # Verify repository was called
        self.mock_repository.find_by_id.assert_called_once_with(playlist_id)
        self.mock_repository.delete.assert_called_once_with(playlist_id)