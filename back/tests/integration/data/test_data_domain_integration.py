# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Integration tests for data domain."""

import pytest
import tempfile
import os
from pathlib import Path
import sqlite3

from app.src.infrastructure.di.container import get_container
from app.src.infrastructure.di.data_container import register_data_domain_services
from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import (
    PureSQLitePlaylistRepository
)
from app.src.infrastructure.database.sqlite_database_service import SQLiteDatabaseService
from app.src.domain.data.services.playlist_service import PlaylistService
from app.src.domain.data.services.track_service import TrackService
from app.src.infrastructure.repositories.data_playlist_repository import DataPlaylistRepository
from app.src.infrastructure.repositories.data_track_repository import DataTrackRepository


@pytest.fixture
async def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Create tables
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE playlists (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            nfc_tag_id TEXT,
            path TEXT,
            type TEXT DEFAULT 'album',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE tracks (
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
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
async def data_services(temp_db):
    """Create data domain services with real database."""
    # Create database service
    db_service = SQLiteDatabaseService(temp_db)

    # Create repository
    sqlite_repo = PureSQLitePlaylistRepository(db_service)

    # Create data domain repositories
    playlist_repo = DataPlaylistRepository(sqlite_repo)
    track_repo = DataTrackRepository(sqlite_repo)

    # Create services
    playlist_service = PlaylistService(playlist_repo, track_repo)
    track_service = TrackService(track_repo, playlist_repo)

    return {
        'playlist_service': playlist_service,
        'track_service': track_service,
        'playlist_repo': playlist_repo,
        'track_repo': track_repo
    }


class TestDataDomainIntegration:
    """Integration tests for data domain services."""

    @pytest.mark.asyncio
    async def test_complete_playlist_workflow(self, data_services):
        """Test complete playlist creation, modification, and deletion workflow."""
        playlist_service = data_services['playlist_service']
        track_service = data_services['track_service']

        # 1. Create a playlist
        playlist = await playlist_service.create_playlist(
            "Test Playlist",
            "A test playlist for integration testing"
        )

        assert playlist['title'] == "Test Playlist"
        assert playlist['description'] == "A test playlist for integration testing"
        assert playlist['track_count'] == 0
        playlist_id = playlist['id']

        # 2. Add tracks to the playlist
        track1_data = {
            'title': 'Track 1',
            'filename': 'track1.mp3',
            'duration_ms': 180000,
            'artist': 'Artist 1'
        }
        track1 = await track_service.add_track(playlist_id, track1_data)

        track2_data = {
            'title': 'Track 2',
            'filename': 'track2.mp3',
            'duration_ms': 200000,
            'artist': 'Artist 2'
        }
        track2 = await track_service.add_track(playlist_id, track2_data)

        # 3. Verify tracks were added
        tracks = await track_service.get_tracks(playlist_id)
        assert len(tracks) == 2
        assert tracks[0]['track_number'] == 1
        assert tracks[1]['track_number'] == 2

        # 4. Update playlist
        updated_playlist = await playlist_service.update_playlist(
            playlist_id,
            {'title': 'Updated Test Playlist'}
        )
        assert updated_playlist['title'] == 'Updated Test Playlist'

        # 5. Reorder tracks
        track_ids = [track2['id'], track1['id']]  # Reverse order
        reorder_success = await track_service.reorder_tracks(playlist_id, track_ids)
        assert reorder_success is True

        # Verify reorder
        reordered_tracks = await track_service.get_tracks(playlist_id)
        assert reordered_tracks[0]['id'] == track2['id']
        assert reordered_tracks[1]['id'] == track1['id']
        assert reordered_tracks[0]['track_number'] == 1
        assert reordered_tracks[1]['track_number'] == 2

        # 6. Test next/previous track navigation
        next_track = await track_service.get_next_track(playlist_id, track2['id'])
        assert next_track['id'] == track1['id']

        prev_track = await track_service.get_previous_track(playlist_id, track1['id'])
        assert prev_track['id'] == track2['id']

        # 7. Delete a track
        delete_success = await track_service.delete_track(track1['id'])
        assert delete_success is True

        remaining_tracks = await track_service.get_tracks(playlist_id)
        assert len(remaining_tracks) == 1
        assert remaining_tracks[0]['id'] == track2['id']

        # 8. Delete the playlist
        delete_playlist_success = await playlist_service.delete_playlist(playlist_id)
        assert delete_playlist_success is True

        # Verify playlist is gone
        deleted_playlist = await playlist_service.get_playlist(playlist_id)
        assert deleted_playlist is None

    @pytest.mark.asyncio
    async def test_nfc_tag_association(self, data_services):
        """Test NFC tag association with playlists."""
        playlist_service = data_services['playlist_service']

        # Create a playlist
        playlist = await playlist_service.create_playlist("NFC Playlist")
        playlist_id = playlist['id']

        # Associate NFC tag
        nfc_tag_id = "nfc-test-123"
        association_success = await playlist_service.associate_nfc_tag(playlist_id, nfc_tag_id)
        assert association_success is True

        # Retrieve playlist by NFC tag
        nfc_playlist = await playlist_service.get_playlist_by_nfc(nfc_tag_id)
        assert nfc_playlist is not None
        assert nfc_playlist['id'] == playlist_id
        assert nfc_playlist['title'] == "NFC Playlist"

        # Test with non-existent NFC tag
        no_playlist = await playlist_service.get_playlist_by_nfc("non-existent-nfc")
        assert no_playlist is None

    @pytest.mark.asyncio
    async def test_pagination(self, data_services):
        """Test playlist pagination functionality."""
        playlist_service = data_services['playlist_service']

        # Create multiple playlists
        playlist_names = [f"Playlist {i}" for i in range(1, 11)]  # 10 playlists
        for name in playlist_names:
            await playlist_service.create_playlist(name)

        # Test first page
        page1 = await playlist_service.get_playlists(page=1, page_size=5)
        assert len(page1['playlists']) == 5
        assert page1['total'] == 10
        assert page1['page'] == 1
        assert page1['page_size'] == 5
        assert page1['total_pages'] == 2

        # Test second page
        page2 = await playlist_service.get_playlists(page=2, page_size=5)
        assert len(page2['playlists']) == 5
        assert page2['total'] == 10
        assert page2['page'] == 2

        # Verify no overlap
        page1_ids = {p['id'] for p in page1['playlists']}
        page2_ids = {p['id'] for p in page2['playlists']}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_filesystem_sync_simulation(self, data_services):
        """Test filesystem synchronization with mock directory structure."""
        playlist_service = data_services['playlist_service']

        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create playlist directories with audio files
            playlist1_dir = Path(temp_dir) / "album-1"
            playlist1_dir.mkdir()
            (playlist1_dir / "track1.mp3").touch()
            (playlist1_dir / "track2.mp3").touch()

            playlist2_dir = Path(temp_dir) / "album-2"
            playlist2_dir.mkdir()
            (playlist2_dir / "song1.flac").touch()
            (playlist2_dir / "song2.wav").touch()
            (playlist2_dir / "song3.m4a").touch()

            # Non-audio file (should be ignored)
            (playlist2_dir / "readme.txt").touch()

            # Empty directory (should create playlist with no tracks)
            empty_dir = Path(temp_dir) / "empty-album"
            empty_dir.mkdir()

            # Sync with filesystem
            stats = await playlist_service.sync_with_filesystem(str(temp_dir))

            assert stats['playlists_scanned'] == 3
            assert stats['playlists_added'] == 3
            assert stats['tracks_added'] == 5  # 2 + 3 + 0

            # Verify playlists were created
            all_playlists = await playlist_service.get_playlists(page_size=100)
            playlist_titles = {p['title'] for p in all_playlists['playlists']}
            assert 'album-1' in playlist_titles
            assert 'album-2' in playlist_titles
            assert 'empty-album' in playlist_titles

    @pytest.mark.asyncio
    async def test_error_handling(self, data_services):
        """Test error handling in data domain."""
        playlist_service = data_services['playlist_service']
        track_service = data_services['track_service']

        # Test getting non-existent playlist
        result = await playlist_service.get_playlist("non-existent-id")
        assert result is None

        # Test updating non-existent playlist
        with pytest.raises(ValueError, match="Playlist non-existent-id not found"):
            await playlist_service.update_playlist("non-existent-id", {'title': 'New Title'})

        # Test adding track to non-existent playlist
        with pytest.raises(ValueError, match="Playlist non-existent-id not found"):
            await track_service.add_track("non-existent-id", {'title': 'Track'})

        # Test updating non-existent track
        with pytest.raises(ValueError, match="Track non-existent-id not found"):
            await track_service.update_track("non-existent-id", {'title': 'New Title'})

    @pytest.mark.asyncio
    async def test_track_sequencing(self, data_services):
        """Test track sequencing and navigation."""
        playlist_service = data_services['playlist_service']
        track_service = data_services['track_service']

        # Create playlist
        playlist = await playlist_service.create_playlist("Sequence Test")
        playlist_id = playlist['id']

        # Add tracks
        tracks = []
        for i in range(1, 6):  # 5 tracks
            track_data = {'title': f'Track {i}', 'filename': f'track{i}.mp3'}
            track = await track_service.add_track(playlist_id, track_data)
            tracks.append(track)

        # Test getting first track (no current track)
        first_track = await track_service.get_next_track(playlist_id)
        assert first_track['title'] == 'Track 1'

        # Test getting last track (no current track)
        last_track = await track_service.get_previous_track(playlist_id)
        assert last_track['title'] == 'Track 5'

        # Test navigation from middle
        middle_track_id = tracks[2]['id']  # Track 3
        next_from_middle = await track_service.get_next_track(playlist_id, middle_track_id)
        assert next_from_middle['title'] == 'Track 4'

        prev_from_middle = await track_service.get_previous_track(playlist_id, middle_track_id)
        assert prev_from_middle['title'] == 'Track 2'

        # Test edge cases
        last_track_id = tracks[4]['id']  # Track 5
        next_from_last = await track_service.get_next_track(playlist_id, last_track_id)
        assert next_from_last is None

        first_track_id = tracks[0]['id']  # Track 1
        prev_from_first = await track_service.get_previous_track(playlist_id, first_track_id)
        assert prev_from_first is None