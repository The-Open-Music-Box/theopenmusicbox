# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Simple test for playlist folder cleanup functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.src.infrastructure.adapters.pure_playlist_repository_adapter import PurePlaylistRepositoryAdapter


class TestPlaylistFolderCleanupSimple:
    """Simple test for folder cleanup functionality."""

    def setup_method(self):
        """Set up test with temporary upload folder."""
        self.temp_upload_dir = tempfile.mkdtemp()
        self.mock_config = MagicMock()
        self.mock_config.upload_folder = self.temp_upload_dir

    def teardown_method(self):
        """Clean up temporary directories."""
        import shutil
        if os.path.exists(self.temp_upload_dir):
            shutil.rmtree(self.temp_upload_dir)

    @pytest.mark.asyncio
    async def test_cleanup_playlist_folder_method_directly(self):
        """Test the _cleanup_playlist_folder method directly."""
        playlist_id = "direct-test-playlist"

        # Create test playlist folder with files
        playlist_folder = Path(self.temp_upload_dir) / playlist_id
        playlist_folder.mkdir(parents=True)
        (playlist_folder / "track1.mp3").touch()
        (playlist_folder / "track2.mp3").touch()

        # Verify folder exists
        assert playlist_folder.exists()
        assert len(list(playlist_folder.iterdir())) == 2

        # Create adapter and test cleanup directly
        with patch('app.src.dependencies.get_config', return_value=self.mock_config):
            adapter = PurePlaylistRepositoryAdapter()

            # Act - call cleanup method directly
            await adapter._cleanup_playlist_folder(playlist_id)

        # Assert - folder should be removed
        assert not playlist_folder.exists()

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_folder(self):
        """Test cleanup of folder that doesn't exist."""
        playlist_id = "nonexistent-folder"

        # Create adapter
        with patch('app.src.dependencies.get_config', return_value=self.mock_config):
            adapter = PurePlaylistRepositoryAdapter()

            # Act - call cleanup on non-existent folder (should not raise error)
            await adapter._cleanup_playlist_folder(playlist_id)

        # Should complete without error
        assert True

    @pytest.mark.asyncio
    async def test_cleanup_nested_folder(self):
        """Test cleanup of folder with nested structure."""
        playlist_id = "nested-test-playlist"

        # Create test playlist folder with nested structure
        playlist_folder = Path(self.temp_upload_dir) / playlist_id
        playlist_folder.mkdir(parents=True)

        # Create nested folders and files
        sub_folder = playlist_folder / "artist" / "album"
        sub_folder.mkdir(parents=True)
        (sub_folder / "track1.mp3").touch()
        (sub_folder / "track2.mp3").touch()
        (playlist_folder / "cover.jpg").touch()

        # Verify structure exists
        assert playlist_folder.exists()
        assert sub_folder.exists()
        assert len(list(playlist_folder.rglob("*"))) >= 4

        # Create adapter and test cleanup
        with patch('app.src.dependencies.get_config', return_value=self.mock_config):
            adapter = PurePlaylistRepositoryAdapter()

            # Act - cleanup nested structure
            await adapter._cleanup_playlist_folder(playlist_id)

        # Assert - entire structure should be removed
        assert not playlist_folder.exists()