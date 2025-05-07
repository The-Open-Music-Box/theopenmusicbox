"""
Specific fixtures for core module tests.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import os

from app.src.config import IConfig, TestConfig, ConfigFactory, ConfigType
from app.src.services.playlist_service import PlaylistService
from app.src.module.audio_player.audio_player import AudioPlayer
from app.src.model.track import Track


@pytest.fixture
def mock_config():
    """Fixture providing a test configuration."""
    config = MagicMock(spec=IConfig)
    config.db_file = ":memory:"  # Use in-memory SQLite
    config.upload_folder = "/tmp/test_upload"
    return config


@pytest.fixture
def real_temp_config():
    """Fixture providing a real configuration with temporary directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a test configuration with the temporary directory
        config = ConfigFactory.get_config(ConfigType.TEST, base_path=tmp_dir)
        # Create the upload folder
        os.makedirs(config.upload_folder, exist_ok=True)
        yield config
    # Reset the factory after the test
    ConfigFactory.reset()


@pytest.fixture
def mock_playlist_service():
    """Fixture for a mocked playlist service."""
    service = MagicMock(spec=PlaylistService)
    service.get_playlist_by_nfc_tag.return_value = {
        "id": "test_id",
        "title": "Test Playlist",
        "path": "/fake/path",
        "tracks": [{"id": "track1", "number": 1, "title": "Test Track"}]
    }
    service.sync_with_filesystem.return_value = {
        "playlists_added": 1,
        "playlists_updated": 0,
        "tracks_added": 1,
        "tracks_removed": 0
    }
    return service


@pytest.fixture
def mock_audio_player():
    """Fixture for a mocked audio player."""
    # Use MagicMock directly to allow adding methods
    player = MagicMock()
    player.is_playing = False
    # Manually add is_finished method
    player.is_finished = MagicMock(return_value=False)
    return player


@pytest.fixture
def mock_track():
    """Fixture for a mocked Track object."""
    track = MagicMock(spec=Track)
    track.id = "track_id_1"
    track.number = 1
    track.title = "Test Track"
    track.file_path = "/fake/path/track.mp3"
    track.duration = 180  # 3 minutes in seconds
    return track
