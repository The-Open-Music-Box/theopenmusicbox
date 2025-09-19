#!/usr/bin/env python3
"""
Functional tests for playlist folder deletion functionality.

Tests the complete workflow of:
1. Creating playlists with physical folders
2. Adding files to folders
3. Deleting playlists via repository
4. Verifying complete folder cleanup occurs
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any


class TestPlaylistFolderDeletion:
    """Test suite for playlist deletion with automatic folder cleanup."""

    @pytest.mark.asyncio
    async def test_playlist_deletion_removes_folder_and_contents(
        self, test_config, playlist_repository_adapter
    ):
        """Test that deleting a playlist removes its folder and all contents."""
        from app.src.utils.path_utils import normalize_folder_name

        # Create playlist
        playlist_data = {
            "title": "Test Folder Deletion",
            "description": "Test playlist for folder deletion",
        }

        playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)
        playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)

        # Setup physical directory with files and subdirectories
        upload_folder = Path(test_config.upload_folder)
        playlist_folder = upload_folder / playlist.get('path', normalize_folder_name(playlist_data['title']))
        playlist_folder.mkdir(parents=True, exist_ok=True)

        # Create various files and subdirectories
        test_files = [
            "track1.mp3",
            "track2.mp3",
            "subfolder/nested_track.mp3",
            "images/cover.jpg",
            "metadata.txt"
        ]

        created_files = []
        for file_path in test_files:
            full_path = playlist_folder / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"test content for {file_path}")
            created_files.append(full_path)

        # Verify folder and files exist
        assert playlist_folder.exists(), "Playlist folder should exist"
        assert playlist_folder.is_dir(), "Playlist folder should be a directory"

        files_count = len(list(playlist_folder.rglob("*")))
        assert files_count >= len(test_files), f"Should have at least {len(test_files)} files/folders"

        # Delete playlist
        delete_success = await playlist_repository_adapter.delete_playlist(playlist_id)
        assert delete_success, "Playlist deletion should succeed"

        # Verify complete cleanup
        assert not playlist_folder.exists(), "Playlist folder should be completely removed"

        # Verify playlist no longer exists in database
        deleted_playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        assert deleted_playlist is None, "Playlist should not exist in database"

    @pytest.mark.asyncio
    async def test_playlist_deletion_handles_missing_folder(
        self, test_config, playlist_repository_adapter
    ):
        """Test that playlist deletion works even when folder is already missing."""
        # Create playlist
        playlist_data = {
            "title": "Missing Folder Test",
            "description": "Test playlist with missing folder",
        }

        playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)

        # Don't create the physical folder (simulates missing folder scenario)

        # Delete playlist should still work
        delete_success = await playlist_repository_adapter.delete_playlist(playlist_id)
        assert delete_success, "Playlist deletion should succeed even with missing folder"

        # Verify playlist no longer exists in database
        deleted_playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        assert deleted_playlist is None, "Playlist should not exist in database"

    @pytest.mark.asyncio
    async def test_multiple_playlist_folders_cleanup(
        self, test_config, playlist_repository_adapter
    ):
        """Test cleanup of playlists with various folder naming patterns."""
        from app.src.utils.path_utils import normalize_folder_name

        test_cases = [
            {"title": "Simple Name", "expected_path": "simple_name"},
            {"title": "Name With Spaces", "expected_path": "name_with_spaces"},
            {"title": "Name (With) [Special] Chars:", "expected_path": "name__with___special__chars_"},
        ]

        upload_folder = Path(test_config.upload_folder)
        created_playlists = []

        try:
            for case in test_cases:
                # Create playlist
                playlist_data = {
                    "title": case["title"],
                    "description": f"Test playlist: {case['title']}",
                }

                playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)
                playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)

                # Verify expected path normalization
                expected_path = case["expected_path"]
                actual_path = playlist.get('path', '')
                assert actual_path == expected_path, f"Path should be normalized to {expected_path}, got {actual_path}"

                # Create physical folder and file
                playlist_folder = upload_folder / actual_path
                playlist_folder.mkdir(parents=True, exist_ok=True)
                (playlist_folder / "test_file.mp3").write_text("test content")

                created_playlists.append({
                    "id": playlist_id,
                    "folder": playlist_folder,
                    "title": case["title"]
                })

            # Verify all folders exist
            for playlist_info in created_playlists:
                assert playlist_info["folder"].exists(), f"Folder should exist for {playlist_info['title']}"

            # Delete all playlists
            for playlist_info in created_playlists:
                delete_success = await playlist_repository_adapter.delete_playlist(playlist_info["id"])
                assert delete_success, f"Should delete playlist {playlist_info['title']}"

            # Verify all folders are cleaned up
            for playlist_info in created_playlists:
                assert not playlist_info["folder"].exists(), f"Folder should be removed for {playlist_info['title']}"

        finally:
            # Cleanup any remaining folders
            for playlist_info in created_playlists:
                if playlist_info["folder"].exists():
                    import shutil
                    shutil.rmtree(playlist_info["folder"])

    @pytest.mark.asyncio
    async def test_playlist_deletion_with_legacy_folder_names(
        self, test_config, playlist_repository_adapter
    ):
        """Test cleanup of playlists with legacy folder naming (original title as folder name)."""
        from app.src.utils.path_utils import normalize_folder_name

        # Create playlist
        playlist_data = {
            "title": "Legacy Test Playlist (2025)",
            "description": "Test for legacy folder cleanup",
        }

        playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)
        playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)

        upload_folder = Path(test_config.upload_folder)
        normalized_folder = upload_folder / playlist.get('path', normalize_folder_name(playlist_data['title']))
        legacy_folder = upload_folder / playlist_data['title']  # Original title as folder name

        # Create both normalized and legacy folders (simulates migration scenario)
        normalized_folder.mkdir(parents=True, exist_ok=True)
        legacy_folder.mkdir(parents=True, exist_ok=True)

        (normalized_folder / "new_file.mp3").write_text("new format content")
        (legacy_folder / "legacy_file.mp3").write_text("legacy format content")

        # Verify both folders exist
        assert normalized_folder.exists(), "Normalized folder should exist"
        assert legacy_folder.exists(), "Legacy folder should exist"

        # Delete playlist
        delete_success = await playlist_repository_adapter.delete_playlist(playlist_id)
        assert delete_success, "Playlist deletion should succeed"

        # Verify both folders are cleaned up
        assert not normalized_folder.exists(), "Normalized folder should be removed"
        assert not legacy_folder.exists(), "Legacy folder should be removed"