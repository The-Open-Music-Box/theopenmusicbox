# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for Pure DDD Repository implementation with in-memory SQLite.

Tests verify that the pure DDD architecture components work correctly
with proper isolation and dependency injection.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import PureSQLitePlaylistRepository
from app.src.infrastructure.adapters.pure_playlist_repository_adapter import PurePlaylistRepositoryAdapter
from app.src.infrastructure.database.sqlite_database_service import SQLiteDatabaseService
from app.src.data.database_manager import DatabaseManager
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track


class TestPureDDDRepository:
    """Test Pure DDD Repository implementation with in-memory database."""

    def setup_method(self):
        """Set up test environment with in-memory database."""
        # Use temporary file for better control
        import tempfile
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.test_db_path = self.temp_db.name

        # Create database service directly for testing
        self.database_service = SQLiteDatabaseService(
            database_path=self.test_db_path,
            pool_size=1
        )

        # Create a mock database manager that returns our test service
        self.mock_database_manager = MagicMock()
        self.mock_database_manager.database_service = self.database_service

        # Patch the global database manager getter
        self.database_manager_patcher = patch(
            'app.src.infrastructure.repositories.pure_sqlite_playlist_repository.get_database_manager',
            return_value=self.mock_database_manager
        )
        self.database_manager_patcher.start()

        # Initialize database schema first
        self._create_test_schema()

        # Patch error decorator to let exceptions through for testing
        self.error_decorator_patcher = patch(
            'app.src.infrastructure.repositories.pure_sqlite_playlist_repository.handle_repository_errors',
            side_effect=lambda operation_name: lambda func: func  # Pass-through decorator
        )
        self.error_decorator_patcher.start()

        # Create repository instance
        self.repository = PureSQLitePlaylistRepository()

    def teardown_method(self):
        """Clean up test environment."""
        self.database_manager_patcher.stop()
        self.error_decorator_patcher.stop()
        # Clean up temp file
        import os
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def _create_test_schema(self):
        """Create minimal database schema for testing."""
        # Create playlists table
        create_playlists_sql = """
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

        # Create tracks table
        create_tracks_sql = """
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

        # Execute schema creation
        self.database_service.execute_command(create_playlists_sql, None, "create_playlists_table")
        self.database_service.execute_command(create_tracks_sql, None, "create_tracks_table")

    @pytest.mark.asyncio
    async def test_save_playlist_with_tracks_success(self):
        """Test saving playlist with tracks using pure DDD principles."""
        # Arrange
        playlist = Playlist(
            name="Pure DDD Test Playlist",
            description="Testing pure DDD implementation"
        )

        track1 = Track(
            track_number=1,
            title="Pure Track One",
            filename="pure_track1.mp3",
            file_path="/test/pure_track1.mp3",
            duration_ms=180000,
            artist="Pure Artist"
        )

        track2 = Track(
            track_number=2,
            title="Pure Track Two",
            filename="pure_track2.mp3",
            file_path="/test/pure_track2.mp3",
            duration_ms=240000,
            artist="Pure Artist Two"
        )

        playlist.add_track(track1)
        playlist.add_track(track2)

        # Act
        saved_playlist = await self.repository.save(playlist)

        # Assert
        assert saved_playlist.id is not None
        assert saved_playlist.name == "Pure DDD Test Playlist"
        assert saved_playlist.description == "Testing pure DDD implementation"
        assert len(saved_playlist.tracks) == 2

        # Verify tracks
        assert saved_playlist.tracks[0].title == "Pure Track One"
        assert saved_playlist.tracks[0].track_number == 1
        assert saved_playlist.tracks[1].title == "Pure Track Two"
        assert saved_playlist.tracks[1].track_number == 2

    @pytest.mark.asyncio
    async def test_find_by_id_success(self):
        """Test finding playlist by ID using pure DDD principles."""
        # Arrange - save playlist first
        playlist = Playlist(name="Findable Pure Playlist")
        track = Track(
            track_number=1,
            title="Findable Pure Track",
            filename="findable.mp3",
            file_path="/test/findable.mp3"
        )
        playlist.add_track(track)

        saved = await self.repository.save(playlist)

        # Act
        found_playlist = await self.repository.find_by_id(saved.id)

        # Assert
        assert found_playlist is not None
        assert found_playlist.id == saved.id
        assert found_playlist.name == "Findable Pure Playlist"
        assert len(found_playlist.tracks) == 1
        assert found_playlist.tracks[0].title == "Findable Pure Track"

    @pytest.mark.asyncio
    async def test_find_by_nfc_tag_success(self):
        """Test finding playlist by NFC tag using pure DDD principles."""
        # Arrange
        playlist = Playlist(
            name="NFC Pure Playlist",
            nfc_tag_id="pure-nfc-12345"
        )
        await self.repository.save(playlist)

        # Act
        found_playlist = await self.repository.find_by_nfc_tag("pure-nfc-12345")

        # Assert
        assert found_playlist is not None
        assert found_playlist.name == "NFC Pure Playlist"
        assert found_playlist.nfc_tag_id == "pure-nfc-12345"

    @pytest.mark.asyncio
    async def test_update_nfc_tag_association_success(self):
        """Test updating NFC tag association using pure DDD principles."""
        # Arrange - create two playlists
        playlist1 = Playlist(name="Playlist One")
        playlist2 = Playlist(name="Playlist Two", nfc_tag_id="existing-tag")

        saved1 = await self.repository.save(playlist1)
        saved2 = await self.repository.save(playlist2)

        # Act - associate tag with playlist1 (should remove from playlist2)
        success = await self.repository.update_nfc_tag_association(saved1.id, "existing-tag")

        # Assert
        assert success is True

        # Verify association moved
        found1 = await self.repository.find_by_id(saved1.id)
        found2 = await self.repository.find_by_id(saved2.id)

        assert found1.nfc_tag_id == "existing-tag"
        assert found2.nfc_tag_id is None

    @pytest.mark.asyncio
    async def test_remove_nfc_tag_association_success(self):
        """Test removing NFC tag association using pure DDD principles."""
        # Arrange
        playlist = Playlist(name="Tagged Playlist", nfc_tag_id="tag-to-remove")
        saved = await self.repository.save(playlist)

        # Act
        success = await self.repository.remove_nfc_tag_association("tag-to-remove")

        # Assert
        assert success is True

        # Verify tag was removed
        found = await self.repository.find_by_id(saved.id)
        assert found.nfc_tag_id is None

    @pytest.mark.asyncio
    async def test_find_all_with_pagination(self):
        """Test finding all playlists with pagination using pure DDD principles."""
        # Arrange - create multiple playlists
        for i in range(5):
            playlist = Playlist(name=f"Pure Playlist {i}")
            await self.repository.save(playlist)

        # Act - get paginated results
        page1 = await self.repository.find_all(limit=2, offset=0)
        page2 = await self.repository.find_all(limit=2, offset=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2

        # Verify different playlists
        page1_ids = {p.id for p in page1}
        page2_ids = {p.id for p in page2}
        assert page1_ids != page2_ids

    @pytest.mark.asyncio
    async def test_count_playlists(self):
        """Test counting playlists using pure DDD principles."""
        # Arrange - start with clean database
        initial_count = await self.repository.count()

        # Add playlists
        for i in range(3):
            playlist = Playlist(name=f"Count Test {i}")
            await self.repository.save(playlist)

        # Act
        final_count = await self.repository.count()

        # Assert
        assert final_count == initial_count + 3

    @pytest.mark.asyncio
    async def test_search_playlists(self):
        """Test searching playlists using pure DDD principles."""
        # Arrange
        rock_playlist = Playlist(name="Rock Collection", description="Heavy rock music")
        jazz_playlist = Playlist(name="Jazz Standards", description="Classic jazz pieces")

        await self.repository.save(rock_playlist)
        await self.repository.save(jazz_playlist)

        # Act
        rock_results = await self.repository.search("Rock")
        jazz_results = await self.repository.search("jazz")  # Case insensitive

        # Assert
        assert len(rock_results) == 1
        assert rock_results[0].name == "Rock Collection"

        assert len(jazz_results) == 1
        assert jazz_results[0].name == "Jazz Standards"

    @pytest.mark.asyncio
    async def test_delete_playlist_success(self):
        """Test deleting playlist using pure DDD principles."""
        # Arrange
        playlist = Playlist(name="To Delete")
        saved = await self.repository.save(playlist)

        # Act
        success = await self.repository.delete(saved.id)

        # Assert
        assert success is True

        # Verify deletion
        found = await self.repository.find_by_id(saved.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_repository_implements_domain_interface(self):
        """Test that repository correctly implements domain interface."""
        from app.src.domain.repositories.playlist_repository_interface import PlaylistRepositoryInterface

        # Assert
        assert isinstance(self.repository, PlaylistRepositoryInterface)

        # Verify all interface methods are available
        assert hasattr(self.repository, 'save')
        assert hasattr(self.repository, 'find_by_id')
        assert hasattr(self.repository, 'find_by_name')
        assert hasattr(self.repository, 'find_by_nfc_tag')
        assert hasattr(self.repository, 'find_all')
        assert hasattr(self.repository, 'update')
        assert hasattr(self.repository, 'delete')
        assert hasattr(self.repository, 'count')
        assert hasattr(self.repository, 'search')


class TestPurePlaylistRepositoryAdapter:
    """Test Pure Playlist Repository Adapter with mocked dependencies."""

    def setup_method(self):
        """Set up test environment with mocked dependencies."""
        self.mock_repository = MagicMock()

        # Patch dependency injection
        self.dependency_patcher = patch(
            'app.src.dependencies.get_playlist_repository',
            return_value=self.mock_repository
        )
        self.dependency_patcher.start()

        # Patch error decorator to let exceptions through for testing
        self.error_decorator_patcher = patch(
            'app.src.infrastructure.adapters.pure_playlist_repository_adapter.handle_repository_errors',
            side_effect=lambda operation_name: lambda func: func  # Pass-through decorator
        )
        self.error_decorator_patcher.start()

        # Create adapter instance
        self.adapter = PurePlaylistRepositoryAdapter()

    def teardown_method(self):
        """Clean up test environment."""
        self.dependency_patcher.stop()
        self.error_decorator_patcher.stop()

    @pytest.mark.asyncio
    async def test_create_playlist_success(self):
        """Test creating playlist through adapter."""
        # Arrange
        playlist_data = {
            "title": "Adapter Test Playlist",
            "description": "Testing adapter functionality",
            "tracks": [
                {
                    "track_number": 1,
                    "title": "Adapter Track",
                    "filename": "adapter.mp3",
                    "file_path": "/test/adapter.mp3",
                    "duration": 180000
                }
            ]
        }

        # Mock repository response
        mock_playlist = Playlist(name="Adapter Test Playlist")
        mock_playlist.id = "test-playlist-id"

        # Make save method async
        async def async_save(playlist):
            return mock_playlist

        self.mock_repository.save.side_effect = async_save

        # Act
        result_id = await self.adapter.create_playlist(playlist_data)

        # Assert
        assert result_id == "test-playlist-id"
        self.mock_repository.save.assert_called_once()

        # Verify domain entity was created correctly
        call_args = self.mock_repository.save.call_args[0][0]
        assert isinstance(call_args, Playlist)
        assert call_args.name == "Adapter Test Playlist"
        assert len(call_args.tracks) == 1

    @pytest.mark.asyncio
    async def test_get_playlist_by_id_success(self):
        """Test getting playlist by ID through adapter."""
        # Arrange
        mock_playlist = Playlist(name="Retrieved Playlist")
        mock_playlist.id = "retrieved-id"
        self.mock_repository.find_by_id.return_value = mock_playlist

        # Act
        result = await self.adapter.get_playlist_by_id("retrieved-id")

        # Assert
        assert result is not None
        assert result["title"] == "Retrieved Playlist"
        assert result["id"] == "retrieved-id"
        self.mock_repository.find_by_id.assert_called_once_with("retrieved-id")

    @pytest.mark.asyncio
    async def test_get_playlist_by_nfc_tag_success(self):
        """Test getting playlist by NFC tag through adapter."""
        # Arrange
        mock_playlist = Playlist(name="NFC Playlist", nfc_tag_id="nfc-123")
        mock_playlist.id = "nfc-playlist-id"
        self.mock_repository.find_by_nfc_tag.return_value = mock_playlist

        # Act
        result = await self.adapter.get_playlist_by_nfc_tag("nfc-123")

        # Assert
        assert result is not None
        assert result["title"] == "NFC Playlist"
        assert result["nfc_tag_id"] == "nfc-123"
        self.mock_repository.find_by_nfc_tag.assert_called_once_with("nfc-123")

    @pytest.mark.asyncio
    async def test_add_track_success(self):
        """Test adding track to playlist through adapter."""
        # Arrange
        mock_playlist = Playlist(name="Existing Playlist")
        mock_playlist.id = "existing-id"
        self.mock_repository.find_by_id.return_value = mock_playlist
        self.mock_repository.update.return_value = mock_playlist

        track_data = {
            "track_number": 2,
            "title": "New Track",
            "filename": "new.mp3",
            "file_path": "/test/new.mp3",
            "duration": 200000
        }

        # Act
        success = await self.adapter.add_track("existing-id", track_data)

        # Assert
        assert success is True
        self.mock_repository.find_by_id.assert_called_once_with("existing-id")
        self.mock_repository.update.assert_called_once()

        # Verify track was added to playlist
        updated_playlist = self.mock_repository.update.call_args[0][0]
        assert len(updated_playlist.tracks) == 1
        assert updated_playlist.tracks[0].title == "New Track"

    @pytest.mark.asyncio
    async def test_replace_tracks_success(self):
        """Test replacing all tracks in playlist through adapter."""
        # Arrange
        mock_playlist = Playlist(name="Playlist for Track Replace")
        mock_playlist.id = "replace-id"

        # Add initial track
        initial_track = Track(track_number=1, title="Initial", filename="initial.mp3", file_path="/initial.mp3")
        mock_playlist.add_track(initial_track)

        self.mock_repository.find_by_id.return_value = mock_playlist
        self.mock_repository.update.return_value = mock_playlist

        new_tracks_data = [
            {
                "track_number": 1,
                "title": "Replacement Track 1",
                "filename": "replace1.mp3",
                "file_path": "/replace1.mp3"
            },
            {
                "track_number": 2,
                "title": "Replacement Track 2",
                "filename": "replace2.mp3",
                "file_path": "/replace2.mp3"
            }
        ]

        # Act
        success = await self.adapter.replace_tracks("replace-id", new_tracks_data)

        # Assert
        assert success is True
        self.mock_repository.find_by_id.assert_called_once_with("replace-id")
        self.mock_repository.update.assert_called_once()

        # Verify tracks were replaced
        updated_playlist = self.mock_repository.update.call_args[0][0]
        assert len(updated_playlist.tracks) == 2
        assert updated_playlist.tracks[0].title == "Replacement Track 1"
        assert updated_playlist.tracks[1].title == "Replacement Track 2"

    @pytest.mark.asyncio
    async def test_get_all_playlists_success(self):
        """Test getting all playlists through adapter."""
        # Arrange
        mock_playlists = [
            Playlist(name="Playlist 1"),
            Playlist(name="Playlist 2")
        ]
        mock_playlists[0].id = "id1"
        mock_playlists[1].id = "id2"

        self.mock_repository.find_all.return_value = mock_playlists

        # Act
        result = await self.adapter.get_all_playlists(limit=10, offset=0)

        # Assert
        assert len(result) == 2
        assert result[0]["title"] == "Playlist 1"
        assert result[1]["title"] == "Playlist 2"
        self.mock_repository.find_all.assert_called_once_with(limit=10, offset=0)

    def test_domain_to_dict_conversion(self):
        """Test domain entity to dict conversion."""
        # Arrange
        playlist = Playlist(
            name="Conversion Test",
            description="Testing conversion",
            nfc_tag_id="conv-nfc-123"
        )
        playlist.id = "conv-id"

        track = Track(
            track_number=1,
            title="Conversion Track",
            filename="conv.mp3",
            file_path="/conv.mp3",
            duration_ms=150000,
            artist="Conv Artist",
            album="Conv Album"
        )
        track.id = "track-conv-id"
        playlist.add_track(track)

        # Act
        result_dict = self.adapter._domain_to_dict(playlist)

        # Assert
        assert result_dict["id"] == "conv-id"
        assert result_dict["title"] == "Conversion Test"  # API compatibility
        assert result_dict["name"] == "Conversion Test"   # Domain field
        assert result_dict["description"] == "Testing conversion"
        assert result_dict["nfc_tag_id"] == "conv-nfc-123"

        # Verify track conversion
        track_dict = result_dict["tracks"][0]
        assert track_dict["id"] == "track-conv-id"
        assert track_dict["track_number"] == 1
        assert track_dict["number"] == 1  # Legacy field
        assert track_dict["title"] == "Conversion Track"
        assert track_dict["duration"] == 150000      # Legacy field
        assert track_dict["duration_ms"] == 150000   # New field
        assert track_dict["artist"] == "Conv Artist"
        assert track_dict["album"] == "Conv Album"


class TestDependencyInjectionTestability:
    """Test that dependency injection is properly testable."""

    @pytest.mark.asyncio
    async def test_repository_dependency_injection_mockable(self):
        """Test that repository dependency injection can be mocked for testing."""
        # This test verifies that the DDD architecture supports proper testing
        # by allowing dependency injection to be mocked

        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            # Arrange
            mock_repository = MagicMock()
            mock_get_repo.return_value = mock_repository

            # Import and create adapter (should use mocked dependency)
            from app.src.infrastructure.adapters.pure_playlist_repository_adapter import PurePlaylistRepositoryAdapter
            adapter = PurePlaylistRepositoryAdapter()

            # Access the repository (triggers lazy loading)
            _ = adapter._repo

            # Assert
            mock_get_repo.assert_called_once()
            assert adapter._repository == mock_repository

    def test_database_service_mockable(self):
        """Test that database service can be mocked for unit testing."""
        with patch('app.src.infrastructure.repositories.pure_sqlite_playlist_repository.get_database_manager') as mock_get_manager:
            # Arrange
            mock_manager = MagicMock()
            mock_database_service = MagicMock()
            mock_manager.database_service = mock_database_service
            mock_get_manager.return_value = mock_manager

            # Act
            repository = PureSQLitePlaylistRepository()

            # Assert
            assert repository._database_manager == mock_manager
            assert repository._db_service == mock_database_service
            mock_get_manager.assert_called_once()

    def test_singleton_pattern_testable(self):
        """Test that singleton pattern can be overridden for testing."""
        # This test ensures that singletons don't prevent proper testing isolation

        with patch('app.src.dependencies._playlist_repository_instance', None):
            with patch('app.src.dependencies.PureSQLitePlaylistRepository') as mock_repo_class:
                # Arrange
                mock_instance = MagicMock()
                mock_repo_class.return_value = mock_instance

                # Act
                from app.src.dependencies import get_playlist_repository
                result1 = get_playlist_repository()
                result2 = get_playlist_repository()

                # Assert - singleton behavior but testable
                assert result1 == result2 == mock_instance
                mock_repo_class.assert_called_once()  # Only created once (singleton)