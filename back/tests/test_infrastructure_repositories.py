# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for infrastructure repositories following Domain-Driven Design principles.

These tests verify that infrastructure implementations correctly handle persistence
while respecting domain boundaries and contracts.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import PureSQLitePlaylistRepository
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track


class TestPureSQLitePlaylistRepository:
    """Test SQLite playlist repository implementation."""
    
    def setup_method(self):
        """Set up test database."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Pure DDD repository uses dependency injection, not direct instantiation
        from unittest.mock import patch, MagicMock
        from app.src.infrastructure.database.sqlite_database_service import SQLiteDatabaseService

        # Create test database service
        self.database_service = SQLiteDatabaseService(self.temp_db.name, pool_size=1)
        mock_manager = MagicMock()
        mock_manager.database_service = self.database_service

        # Patch dependency injection
        self.patcher = patch(
            'app.src.infrastructure.repositories.pure_sqlite_playlist_repository.get_database_manager',
            return_value=mock_manager
        )
        self.patcher.start()

        # Create test schema
        self._create_test_schema()

        self.repository = PureSQLitePlaylistRepository()
    
    def teardown_method(self):
        """Clean up test database."""
        self.patcher.stop()
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def _create_test_schema(self):
        """Create test database schema."""
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

        self.database_service.execute_command(create_playlists_sql, None, "create_playlists_table")
        self.database_service.execute_command(create_tracks_sql, None, "create_tracks_table")
    
    @pytest.mark.asyncio
    async def test_save_playlist_success(self):
        """Test successful playlist persistence."""
        # Arrange
        playlist = Playlist(
            name="Test Playlist",
            description="A test playlist for repository testing"
        )
        
        track1 = Track(
            track_number=1,
            title="Track One",
            filename="track1.mp3",
            file_path="/music/track1.mp3",
            duration_ms=180000,
            artist="Artist One"
        )
        
        track2 = Track(
            track_number=2,
            title="Track Two",
            filename="track2.mp3",
            file_path="/music/track2.mp3",
            duration_ms=240000,
            artist="Artist Two"
        )
        
        playlist.add_track(track1)
        playlist.add_track(track2)
        
        # Act
        saved_playlist = await self.repository.save(playlist)
        
        # Assert
        assert saved_playlist.id is not None  # ID should be assigned
        assert saved_playlist.name == "Test Playlist"
        assert saved_playlist.description == "A test playlist for repository testing"
        assert len(saved_playlist.tracks) == 2
        
        # Verify tracks are preserved
        assert saved_playlist.tracks[0].title == "Track One"
        assert saved_playlist.tracks[1].title == "Track Two"
    
    @pytest.mark.asyncio
    async def test_find_by_id_success(self):
        """Test finding playlist by ID."""
        # Arrange - save a playlist first
        playlist = Playlist(name="Findable Playlist")
        track = Track(track_number=1, title="Findable Track", filename="find.mp3", file_path="/find.mp3")
        playlist.add_track(track)
        
        saved = await self.repository.save(playlist)
        playlist_id = saved.id
        
        # Act
        found_playlist = await self.repository.find_by_id(playlist_id)
        
        # Assert
        assert found_playlist is not None
        assert found_playlist.id == playlist_id
        assert found_playlist.name == "Findable Playlist"
        assert len(found_playlist.tracks) == 1
        assert found_playlist.tracks[0].title == "Findable Track"
    
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self):
        """Test finding non-existent playlist."""
        # Act
        found_playlist = await self.repository.find_by_id("nonexistent-id")
        
        # Assert
        assert found_playlist is None
    
    @pytest.mark.asyncio
    async def test_find_by_name_success(self):
        """Test finding playlist by name."""
        # Arrange
        playlist = Playlist(name="Unique Name Playlist")
        await self.repository.save(playlist)
        
        # Act
        found_playlist = await self.repository.find_by_name("Unique Name Playlist")
        
        # Assert
        assert found_playlist is not None
        assert found_playlist.name == "Unique Name Playlist"
    
    @pytest.mark.asyncio
    async def test_find_by_nfc_tag_success(self):
        """Test finding playlist by NFC tag."""
        # Arrange
        playlist = Playlist(name="NFC Playlist", nfc_tag_id="nfc-12345")
        await self.repository.save(playlist)
        
        # Act
        found_playlist = await self.repository.find_by_nfc_tag("nfc-12345")
        
        # Assert
        assert found_playlist is not None
        assert found_playlist.name == "NFC Playlist"
        assert found_playlist.nfc_tag_id == "nfc-12345"
    
    @pytest.mark.asyncio
    async def test_find_all_with_pagination(self):
        """Test finding all playlists with pagination."""
        # Arrange - create multiple playlists
        for i in range(5):
            playlist = Playlist(name=f"Playlist {i}")
            await self.repository.save(playlist)
        
        # Act - get first page (2 items)
        playlists_page1 = await self.repository.find_all(limit=2, offset=0)
        
        # Act - get second page (2 items)
        playlists_page2 = await self.repository.find_all(limit=2, offset=2)
        
        # Assert
        assert len(playlists_page1) == 2
        assert len(playlists_page2) == 2
        
        # Should be different playlists
        page1_names = {p.name for p in playlists_page1}
        page2_names = {p.name for p in playlists_page2}
        assert page1_names != page2_names
    
    @pytest.mark.asyncio
    async def test_update_playlist(self):
        """Test updating existing playlist."""
        # Arrange - save initial playlist
        playlist = Playlist(name="Original Name", description="Original Description")
        saved = await self.repository.save(playlist)
        
        # Modify playlist
        saved.name = "Updated Name"
        saved.description = "Updated Description"
        
        # Act
        updated = await self.repository.update(saved)
        
        # Verify update
        found = await self.repository.find_by_id(saved.id)
        
        # Assert
        assert found.name == "Updated Name"
        assert found.description == "Updated Description"
    
    @pytest.mark.asyncio
    async def test_delete_playlist_success(self):
        """Test successful playlist deletion."""
        # Arrange
        playlist = Playlist(name="To Delete")
        saved = await self.repository.save(playlist)
        playlist_id = saved.id
        
        # Act
        deleted = await self.repository.delete(playlist_id)
        
        # Assert
        assert deleted is True
        
        # Verify playlist is gone
        found = await self.repository.find_by_id(playlist_id)
        assert found is None
    
    @pytest.mark.asyncio
    async def test_delete_playlist_not_found(self):
        """Test deleting non-existent playlist."""
        # Act
        deleted = await self.repository.delete("nonexistent-id")
        
        # Assert
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_count_playlists(self):
        """Test counting total playlists."""
        # Arrange - start with empty database
        initial_count = await self.repository.count()
        assert initial_count == 0
        
        # Add playlists
        for i in range(3):
            playlist = Playlist(name=f"Count Test {i}")
            await self.repository.save(playlist)
        
        # Act
        final_count = await self.repository.count()
        
        # Assert
        assert final_count == 3
    
    @pytest.mark.asyncio
    async def test_search_playlists(self):
        """Test searching playlists by name/description."""
        # Arrange
        playlist1 = Playlist(name="Rock Music", description="Heavy rock songs")
        playlist2 = Playlist(name="Classical Collection", description="Beautiful classical pieces")
        playlist3 = Playlist(name="Jazz Favorites", description="Smooth jazz tracks")
        
        await self.repository.save(playlist1)
        await self.repository.save(playlist2)
        await self.repository.save(playlist3)
        
        # Act - search by name
        rock_results = await self.repository.search("Rock", limit=10)
        
        # Act - search by description
        jazz_results = await self.repository.search("jazz", limit=10)  # Case insensitive
        
        # Assert
        assert len(rock_results) == 1
        assert rock_results[0].name == "Rock Music"
        
        assert len(jazz_results) == 1
        assert jazz_results[0].name == "Jazz Favorites"
    
    @pytest.mark.asyncio
    async def test_track_serialization_deserialization(self):
        """Test that tracks are properly serialized/deserialized."""
        # Arrange - playlist with complex track data
        playlist = Playlist(name="Serialization Test")
        
        track = Track(
            track_number=5,
            title="Complex Track",
            filename="complex.mp3",
            file_path="/music/artists/albums/complex.mp3",
            duration_ms=267000,
            artist="Test Artist",
            album="Test Album",
            id="track-uuid-123"
        )
        
        playlist.add_track(track)
        
        # Act - save and retrieve
        saved = await self.repository.save(playlist)
        found = await self.repository.find_by_id(saved.id)
        
        # Assert - all track data preserved
        retrieved_track = found.tracks[0]
        assert retrieved_track.track_number == 5
        assert retrieved_track.title == "Complex Track"
        assert retrieved_track.filename == "complex.mp3"
        assert retrieved_track.file_path == "/music/artists/albums/complex.mp3"
        assert retrieved_track.duration_ms == 267000
        assert retrieved_track.artist == "Test Artist"
        assert retrieved_track.album == "Test Album"
        assert retrieved_track.id == "track-uuid-123"
    
    @pytest.mark.asyncio
    async def test_empty_tracks_serialization(self):
        """Test playlist with no tracks is handled correctly."""
        # Arrange
        playlist = Playlist(name="Empty Playlist")
        
        # Act
        saved = await self.repository.save(playlist)
        found = await self.repository.find_by_id(saved.id)
        
        # Assert
        assert found is not None
        assert found.name == "Empty Playlist"
        assert len(found.tracks) == 0
    
    @pytest.mark.asyncio
    async def test_repository_respects_domain_contracts(self):
        """Test that repository implementation respects domain repository interface."""
        # This test verifies that the repository behaves according to DDD principles
        
        # Arrange - create domain entities
        playlist = Playlist(name="Domain Contract Test")
        track = Track(track_number=1, title="Domain Track", filename="domain.mp3", file_path="/domain.mp3")
        playlist.add_track(track)
        
        # Act - use repository as domain interface
        from app.src.domain.repositories.playlist_repository_interface import PlaylistRepositoryProtocol
        
        # Verify repository implements the interface
        assert isinstance(self.repository, PlaylistRepositoryProtocol)
        
        # Act - perform domain operations
        saved = await self.repository.save(playlist)
        found = await self.repository.find_by_id(saved.id)
        
        # Assert - domain entities maintain their integrity
        assert isinstance(found, Playlist)
        assert found.is_valid()  # Domain validation passes
        assert isinstance(found.tracks[0], Track)
        assert found.tracks[0].is_valid()  # Domain validation passes