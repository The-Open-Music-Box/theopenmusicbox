# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Test to investigate playlist persistence issue.

This test verifies that created playlists can be retrieved immediately after creation.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from app.src.infrastructure.adapters.pure_playlist_repository_adapter import PurePlaylistRepositoryAdapter
from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import PureSQLitePlaylistRepository
from app.src.infrastructure.database.sqlite_database_service import SQLiteDatabaseService


class TestPlaylistPersistenceIssue:
    """Test playlist persistence issue diagnosis."""

    def setup_method(self):
        """Set up test with real database components."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # Create real database service
        self.database_service = SQLiteDatabaseService(
            database_path=self.temp_db.name,
            pool_size=1
        )

        # Mock database manager
        self.mock_database_manager = MagicMock()
        self.mock_database_manager.database_service = self.database_service

        # Create test schema
        self._create_test_schema()

        # Patch database manager dependency
        self.db_manager_patcher = patch(
            'app.src.infrastructure.repositories.pure_sqlite_playlist_repository.get_database_manager',
            return_value=self.mock_database_manager
        )
        self.db_manager_patcher.start()

        # Create repository and adapter instances
        self.repository = PureSQLitePlaylistRepository()
        self.adapter = PurePlaylistRepositoryAdapter()

        # Connect adapter to repository
        with patch.object(PurePlaylistRepositoryAdapter, '_repo', self.repository):
            self.adapter._repository = self.repository

    def teardown_method(self):
        """Clean up test environment."""
        self.db_manager_patcher.stop()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def _create_test_schema(self):
        """Create test database schema."""
        playlists_sql = """
        CREATE TABLE IF NOT EXISTS playlists (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            nfc_tag_id TEXT,
            path TEXT,
            type TEXT DEFAULT 'album',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        tracks_sql = """
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            playlist_id TEXT NOT NULL,
            track_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            filename TEXT,
            file_path TEXT,
            duration_ms INTEGER,
            artist TEXT,
            album TEXT,
            play_count INTEGER DEFAULT 0,
            server_seq INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
        )
        """

        self.database_service.execute_command(playlists_sql, None, "create_playlists_table")
        self.database_service.execute_command(tracks_sql, None, "create_tracks_table")

    @pytest.mark.asyncio
    async def test_create_and_find_playlist_immediately(self):
        """Test that created playlist can be found immediately."""
        # Create playlist via adapter (same path as application)
        playlist_data = {
            "title": "Persistence Test Playlist",
            "description": "Testing immediate retrieval after creation",
            "tracks": [
                {
                    "track_number": 1,
                    "title": "Test Track",
                    "filename": "test.mp3",
                    "file_path": "/test/test.mp3",
                    "duration_ms": 180000
                }
            ]
        }

        # Create playlist
        playlist_id = await self.adapter.create_playlist(playlist_data)
        assert playlist_id is not None
        print(f"Created playlist with ID: {playlist_id}")

        # Try to find it immediately
        found_playlists = await self.adapter.find_all(limit=50, offset=0)
        print(f"Found {len(found_playlists)} playlists")

        # Should find at least 1 playlist (the one we just created)
        assert len(found_playlists) >= 1

        # Find the specific playlist we created
        created_playlist = None
        for playlist in found_playlists:
            if playlist["id"] == playlist_id:
                created_playlist = playlist
                break

        assert created_playlist is not None, f"Created playlist {playlist_id} not found in results"
        assert created_playlist["title"] == "Persistence Test Playlist"
        assert len(created_playlist["tracks"]) == 1

    @pytest.mark.asyncio
    async def test_repository_direct_save_and_find(self):
        """Test repository methods directly."""
        from app.src.domain.models.playlist import Playlist
        from app.src.domain.models.track import Track

        # Create domain entities
        playlist = Playlist(name="Direct Repository Test")
        track = Track(
            track_number=1,
            title="Direct Track",
            filename="direct.mp3",
            file_path="/direct.mp3",
            duration_ms=180000
        )
        playlist.add_track(track)

        # Save via repository
        saved_playlist = await self.repository.save(playlist)
        print(f"Saved playlist: {saved_playlist.id}")

        # Find via repository
        found_playlists = await self.repository.find_all(limit=50, offset=0)
        print(f"Repository found {len(found_playlists)} playlists")

        # Should find at least 1 playlist
        assert len(found_playlists) >= 1

        # Find our specific playlist
        found_playlist = None
        for p in found_playlists:
            if p.id == saved_playlist.id:
                found_playlist = p
                break

        assert found_playlist is not None
        assert found_playlist.name == "Direct Repository Test"

    @pytest.mark.asyncio
    async def test_database_raw_queries(self):
        """Test raw database queries to verify data is actually stored."""
        # Create playlist via adapter
        playlist_data = {
            "title": "Raw Query Test",
            "description": "Testing with raw SQL queries",
            "tracks": []
        }

        playlist_id = await self.adapter.create_playlist(playlist_data)
        print(f"Created playlist ID: {playlist_id}")

        # Check database directly
        raw_playlists = self.database_service.execute_query(
            "SELECT * FROM playlists", None, "check_playlists"
        )
        print(f"Raw database query found {len(raw_playlists)} playlists")

        # Should have at least 1 playlist in database
        assert len(raw_playlists) >= 1

        # Find our playlist
        our_playlist = None
        for playlist in raw_playlists:
            if playlist["id"] == playlist_id:
                our_playlist = playlist
                break

        assert our_playlist is not None
        assert our_playlist["title"] == "Raw Query Test"
        print(f"Found playlist in raw query: {our_playlist}")

    @pytest.mark.asyncio
    async def test_application_service_path(self):
        """Test the exact path used by the application service."""
        from app.src.application.services.playlist_application_service import PlaylistApplicationService

        # Create application service with our adapter
        app_service = PlaylistApplicationService(self.adapter)

        # Create playlist via application service
        result = await app_service.create_playlist_use_case("App Service Test", "Testing application service")
        assert result["status"] == "success"
        playlist_id = result["playlist_id"]
        print(f"App service created playlist: {playlist_id}")

        # Get all playlists via application service
        get_result = await app_service.get_all_playlists_use_case(page=1, page_size=50)
        assert get_result["status"] == "success"
        playlists = get_result["playlists"]
        print(f"App service found {len(playlists)} playlists")

        # Should find at least 1 playlist
        assert len(playlists) >= 1

        # Find our specific playlist
        found_playlist = None
        for playlist in playlists:
            if playlist["id"] == playlist_id:
                found_playlist = playlist
                break

        assert found_playlist is not None
        assert found_playlist["title"] == "App Service Test"