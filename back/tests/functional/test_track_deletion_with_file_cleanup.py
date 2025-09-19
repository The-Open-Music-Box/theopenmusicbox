#!/usr/bin/env python3
"""
Functional tests for track deletion with file cleanup functionality.

Tests the complete workflow of:
1. Creating playlists and tracks
2. Adding physical files
3. Deleting tracks via API
4. Verifying file cleanup occurs automatically
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any


class TestTrackDeletionWithFileCleanup:
    """Test suite for track deletion with automatic file cleanup."""

    @pytest.fixture
    async def playlist_with_files(self, test_config, playlist_repository_adapter):
        """Create a test playlist with physical files."""
        from app.src.utils.path_utils import normalize_folder_name

        # Create playlist
        playlist_data = {
            "title": "Test Track Deletion",
            "description": "Test playlist for track deletion with file cleanup",
        }

        playlist_id = await playlist_repository_adapter.create_playlist(playlist_data)
        playlist = await playlist_repository_adapter.get_playlist_by_id(playlist_id)

        # Setup physical directory
        upload_folder = Path(test_config.upload_folder)
        playlist_folder = upload_folder / playlist.get('path', normalize_folder_name(playlist_data['title']))
        playlist_folder.mkdir(parents=True, exist_ok=True)

        # Create test files and tracks
        test_tracks = []
        for i in range(1, 4):  # Create 3 tracks
            filename = f"track_{i}.mp3"
            file_path = playlist_folder / filename
            file_path.write_text(f"fake audio content {i}")

            track_data = {
                "track_number": i,
                "title": f"Test Track {i}",
                "filename": filename,
                "file_path": str(file_path),
                "duration_ms": 120000 + i * 1000,
            }

            await playlist_repository_adapter.add_track(playlist_id, track_data)
            test_tracks.append(track_data)

        yield {
            "playlist_id": playlist_id,
            "playlist_folder": playlist_folder,
            "tracks": test_tracks
        }

        # Cleanup
        try:
            await playlist_repository_adapter.delete_playlist(playlist_id)
        except:
            pass

        if playlist_folder.exists():
            import shutil
            shutil.rmtree(playlist_folder)

    @pytest.mark.asyncio
    async def test_track_deletion_removes_files(self, playlist_with_files, unified_controller):
        """Test that deleting tracks also removes their physical files."""
        playlist_id = playlist_with_files["playlist_id"]
        playlist_folder = playlist_with_files["playlist_folder"]

        # Verify initial state
        files_before = list(playlist_folder.glob("*.mp3"))
        assert len(files_before) == 3, "Should have 3 files initially"

        # Delete tracks 1 and 3
        tracks_to_delete = [1, 3]
        result = await unified_controller.delete_tracks(playlist_id, tracks_to_delete)

        # Verify deletion success
        assert result.get("status") == "success"
        assert "2 tracks successfully" in result.get("message", "")

        # Verify files were deleted
        files_after = list(playlist_folder.glob("*.mp3"))
        assert len(files_after) == 1, "Should have 1 file remaining"
        assert files_after[0].name == "track_2.mp3", "Only track 2 file should remain"

        # Verify database consistency
        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        updated_playlist = await repo.get_playlist_by_id(playlist_id)
        remaining_tracks = updated_playlist.get("tracks", [])

        assert len(remaining_tracks) == 1, "Should have 1 track in database"
        assert remaining_tracks[0].get("track_number") == 2, "Remaining track should be track 2"

    @pytest.mark.asyncio
    async def test_track_deletion_handles_missing_files_gracefully(
        self, playlist_with_files, unified_controller
    ):
        """Test that track deletion works even when files are already missing."""
        playlist_id = playlist_with_files["playlist_id"]
        playlist_folder = playlist_with_files["playlist_folder"]

        # Manually delete one file
        file_to_remove = playlist_folder / "track_1.mp3"
        file_to_remove.unlink()

        # Delete track 1 (file already missing)
        result = await unified_controller.delete_tracks(playlist_id, [1])

        # Should still succeed
        assert result.get("status") == "success"
        assert "1 tracks successfully" in result.get("message", "")

        # Verify remaining files and tracks
        files_after = list(playlist_folder.glob("*.mp3"))
        assert len(files_after) == 2, "Should have 2 files remaining"

        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        updated_playlist = await repo.get_playlist_by_id(playlist_id)
        remaining_tracks = updated_playlist.get("tracks", [])

        assert len(remaining_tracks) == 2, "Should have 2 tracks in database"

    @pytest.mark.asyncio
    async def test_delete_all_tracks_empties_playlist(
        self, playlist_with_files, unified_controller
    ):
        """Test deleting all tracks empties the playlist but doesn't delete it."""
        playlist_id = playlist_with_files["playlist_id"]
        playlist_folder = playlist_with_files["playlist_folder"]

        # Delete all tracks
        result = await unified_controller.delete_tracks(playlist_id, [1, 2, 3])

        # Verify deletion success
        assert result.get("status") == "success"
        assert "3 tracks successfully" in result.get("message", "")

        # Verify no files remain
        files_after = list(playlist_folder.glob("*.mp3"))
        assert len(files_after) == 0, "No files should remain"

        # Verify playlist still exists but is empty
        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        playlist = await repo.get_playlist_by_id(playlist_id)

        assert playlist is not None, "Playlist should still exist"
        assert len(playlist.get("tracks", [])) == 0, "Playlist should be empty"

    @pytest.mark.asyncio
    async def test_invalid_track_numbers_handled_gracefully(
        self, playlist_with_files, unified_controller
    ):
        """Test that deleting non-existent track numbers is handled gracefully."""
        playlist_id = playlist_with_files["playlist_id"]

        # Try to delete non-existent tracks
        result = await unified_controller.delete_tracks(playlist_id, [99, 100])

        # Should succeed (no tracks to delete)
        assert result.get("status") == "success"

        # Verify no tracks were affected
        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        playlist = await repo.get_playlist_by_id(playlist_id)
        tracks = playlist.get("tracks", [])

        assert len(tracks) == 3, "All original tracks should remain"