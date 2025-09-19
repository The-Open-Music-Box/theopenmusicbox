#!/usr/bin/env python3
"""
Integration tests for file system operations.

These tests verify the complete integration between:
1. Database operations
2. File system operations
3. Business logic coordination
4. Error handling and recovery
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any


class TestFileSystemIntegration:
    """Test suite for file system integration with business logic."""

    @pytest.fixture
    async def isolated_file_system(self, test_config):
        """Create isolated file system for testing."""
        temp_dir = tempfile.mkdtemp(prefix="tombt_test_")
        temp_path = Path(temp_dir)

        # Override config to use temp directory
        original_upload_folder = test_config.upload_folder
        test_config.upload_folder = str(temp_path)

        yield temp_path

        # Cleanup
        test_config.upload_folder = original_upload_folder
        if temp_path.exists():
            shutil.rmtree(temp_path)

    @pytest.mark.asyncio
    async def test_complete_playlist_lifecycle_with_files(
        self, isolated_file_system, playlist_repository_adapter
    ):
        """Test complete playlist lifecycle including file operations."""
        # 1. Create playlist
        playlist_data = {
            "title": "Integration Test Playlist",
            "description": "Testing complete lifecycle",
        }

        playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)
        assert playlist_id is not None

        # 2. Verify playlist folder structure
        playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        playlist_folder = isolated_file_system / playlist.get('path', '')
        assert not playlist_folder.exists(), "Folder should not exist until first upload"

        # 3. Simulate file upload by creating folder and files
        playlist_folder.mkdir(parents=True, exist_ok=True)

        test_files = []
        for i in range(3):
            filename = f"integration_test_{i}.mp3"
            file_path = playlist_folder / filename
            file_path.write_text(f"Integration test audio content {i}")
            test_files.append(str(file_path))

            # Add track to playlist
            track_data = {
                "track_number": i + 1,
                "title": f"Integration Track {i + 1}",
                "filename": filename,
                "file_path": str(file_path),
                "duration_ms": (i + 1) * 60000,  # 1, 2, 3 minutes
            }
            await playlist_repository_adapter.add_track(playlist_id, track_data)

        # 4. Verify integrated state
        updated_playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        tracks = updated_playlist.get("tracks", [])

        assert len(tracks) == 3, "Should have 3 tracks in database"
        assert playlist_folder.exists(), "Playlist folder should exist"

        files_on_disk = list(playlist_folder.glob("*.mp3"))
        assert len(files_on_disk) == 3, "Should have 3 files on disk"

        # Verify file-database consistency
        for track in tracks:
            file_path = Path(track.get("file_path", ""))
            assert file_path.exists(), f"Track file should exist: {file_path}"
            assert file_path.parent == playlist_folder, "File should be in playlist folder"

        # 5. Test partial track deletion with file cleanup
        from app.src.domain.controllers.unified_controller import unified_controller

        delete_result = await unified_controller.delete_tracks(playlist_id, [2])  # Delete middle track
        assert delete_result.get("status") == "success"

        # Verify partial cleanup
        remaining_playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        remaining_tracks = remaining_playlist.get("tracks", [])
        assert len(remaining_tracks) == 2, "Should have 2 tracks remaining"

        remaining_files = list(playlist_folder.glob("*.mp3"))
        assert len(remaining_files) == 2, "Should have 2 files remaining"

        # Verify specific files remain
        remaining_filenames = {f.name for f in remaining_files}
        expected_remaining = {"integration_test_0.mp3", "integration_test_2.mp3"}
        assert remaining_filenames == expected_remaining, "Correct files should remain"

        # 6. Test complete playlist deletion
        delete_playlist_result = await playlist_repository_adapter.delete_playlist(playlist_id)
        assert delete_playlist_result, "Playlist deletion should succeed"

        # Verify complete cleanup
        deleted_playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        assert deleted_playlist is None, "Playlist should not exist in database"
        assert not playlist_folder.exists(), "Playlist folder should be completely removed"

    @pytest.mark.asyncio
    async def test_file_system_error_handling(
        self, isolated_file_system, playlist_repository_adapter
    ):
        """Test error handling when file system operations fail."""
        import os
        import stat

        # Create playlist and folder
        playlist_data = {"title": "Error Handling Test"}
        playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)

        playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        playlist_folder = isolated_file_system / playlist.get('path', '')
        playlist_folder.mkdir(parents=True, exist_ok=True)

        # Create a file
        test_file = playlist_folder / "test_track.mp3"
        test_file.write_text("test content")

        track_data = {
            "track_number": 1,
            "title": "Test Track",
            "filename": "test_track.mp3",
            "file_path": str(test_file),
            "duration_ms": 60000,
        }
        await playlist_repository_adapter.add_track(playlist_id, track_data)

        # Make folder read-only to simulate permission error
        try:
            playlist_folder.chmod(stat.S_IRUSR | stat.S_IXUSR)  # Read and execute only

            # Try to delete playlist (might fail due to permissions)
            delete_result = await playlist_repository_adapter.delete_playlist(playlist_id)

            # The operation should handle errors gracefully
            # Even if file deletion fails, database deletion should succeed
            deleted_playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
            assert deleted_playlist is None, "Playlist should be removed from database even if file cleanup fails"

        finally:
            # Restore permissions for cleanup
            try:
                playlist_folder.chmod(stat.S_IRWXU)  # Full permissions
            except:
                pass

    @pytest.mark.asyncio
    async def test_concurrent_file_operations(
        self, isolated_file_system, playlist_repository_adapter
    ):
        """Test concurrent file operations don't cause conflicts."""
        # Create multiple playlists concurrently
        playlist_tasks = []
        for i in range(3):
            playlist_data = {
                "title": f"Concurrent Test Playlist {i}",
                "description": f"Testing concurrent operations {i}",
            }
            task = playlist_repository_adapter.create_playlist(playlist_data)
            playlist_tasks.append(task)

        playlist_ids = await asyncio.gather(*playlist_tasks)

        # Create folders and files for each playlist concurrently
        setup_tasks = []
        for i, playlist_id in enumerate(playlist_ids):
            async def setup_playlist_files(pid, index):
                playlist = await playlist_repository_adapter.get_playlist_by_id(pid)
                playlist_folder = isolated_file_system / playlist.get('path', '')
                playlist_folder.mkdir(parents=True, exist_ok=True)

                # Create a file
                test_file = playlist_folder / f"concurrent_track_{index}.mp3"
                test_file.write_text(f"concurrent content {index}")

                # Add track
                track_data = {
                    "track_number": 1,
                    "title": f"Concurrent Track {index}",
                    "filename": f"concurrent_track_{index}.mp3",
                    "file_path": str(test_file),
                    "duration_ms": 60000,
                }
                await playlist_repository_adapter.add_track(pid, track_data)

            setup_tasks.append(setup_playlist_files(playlist_id, i))

        await asyncio.gather(*setup_tasks)

        # Verify all playlists and files exist
        for i, playlist_id in enumerate(playlist_ids):
            playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
            assert playlist is not None, f"Playlist {i} should exist"

            tracks = playlist.get("tracks", [])
            assert len(tracks) == 1, f"Playlist {i} should have 1 track"

            track_file = Path(tracks[0].get("file_path", ""))
            assert track_file.exists(), f"Track file for playlist {i} should exist"

        # Delete all playlists concurrently
        delete_tasks = [
            playlist_repository_adapter.delete_playlist(pid) for pid in playlist_ids
        ]

        delete_results = await asyncio.gather(*delete_tasks)
        assert all(delete_results), "All playlist deletions should succeed"

        # Verify cleanup
        for playlist_id in playlist_ids:
            playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
            assert playlist is None, "All playlists should be deleted"

        # Verify no stray folders remain
        remaining_folders = [d for d in isolated_file_system.iterdir() if d.is_dir()]
        assert len(remaining_folders) == 0, "No playlist folders should remain"

    @pytest.mark.asyncio
    async def test_folder_name_consistency_across_operations(
        self, isolated_file_system, playlist_repository_adapter
    ):
        """Test that folder names remain consistent across all operations."""
        # Create playlist with complex name
        playlist_data = {
            "title": "Complex Name (With) [Special] Characters: 2025",
            "description": "Testing name consistency",
        }

        playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)

        # Get the normalized path
        playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        expected_path = playlist.get('path', '')
        playlist_folder = isolated_file_system / expected_path

        # Create folder and file
        playlist_folder.mkdir(parents=True, exist_ok=True)
        test_file = playlist_folder / "consistency_test.mp3"
        test_file.write_text("consistency test content")

        track_data = {
            "track_number": 1,
            "title": "Consistency Test Track",
            "filename": "consistency_test.mp3",
            "file_path": str(test_file),
            "duration_ms": 60000,
        }
        await playlist_repository_adapter.add_track(playlist_id, track_data)

        # Update playlist (should not change folder path)
        await playlist_repository_adapter.update_playlist(
            playlist_id, {"description": "Updated description"}
        )

        updated_playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)
        updated_path = updated_playlist.get('path', '')

        assert updated_path == expected_path, "Path should remain consistent after update"
        assert playlist_folder.exists(), "Original folder should still exist"
        assert test_file.exists(), "Original file should still exist"

        # Delete playlist should clean up correct folder
        delete_result = await playlist_repository_adapter.delete_playlist(playlist_id)
        assert delete_result, "Deletion should succeed"
        assert not playlist_folder.exists(), "Correct folder should be cleaned up"