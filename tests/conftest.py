# tests/conftest.py
# Merged fixture file combining fixtures from app/tests/conftest.py and tests/conftest.py

import sys
import os
import pathlib
import warnings
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.src.dependencies import get_config, get_audio

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv is not installed, skip loading .env

# Filter out specific deprecation warnings from rx library
warnings.filterwarnings('ignore', category=DeprecationWarning,
                       message='datetime.datetime.utcfromtimestamp.*',
                       module='rx.internal.constants')
warnings.filterwarnings('ignore', category=DeprecationWarning,
                       message='datetime.datetime.utcnow.*',
                       module='rx.internal.basic')

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the app directory to the Python path
app_dir = os.path.join(project_root, 'app')
sys.path.insert(0, app_dir)

# Add the tests directory to the Python path
tests_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tests_dir)

# === API Test Fixtures (from app/tests/conftest.py) ===

class DummyAudio:
    def __init__(self):
        self.calls = []
    def play_track(self, track_number):
        self.calls.append(('play', track_number))
    def next_track(self):
        self.calls.append(('next',))
    def pause(self):
        self.calls.append(('pause',))
    def resume(self):
        self.calls.append(('resume',))
    def stop(self):
        self.calls.append(('stop',))
    def previous_track(self):
        self.calls.append(('previous',))

@pytest.fixture
def tmp_db_file(tmp_path):
    db_file = tmp_path / "test.db"
    yield str(db_file)
    if os.path.exists(db_file):
        os.remove(db_file)

@pytest.fixture
def test_client_with_mock_db(tmp_db_file):
    def get_test_config():
        from app.src.config import Config
        old_db_file = os.environ.get('DB_FILE')
        os.environ['DB_FILE'] = tmp_db_file
        config = Config()
        if old_db_file is not None:
            os.environ['DB_FILE'] = old_db_file
        else:
            del os.environ['DB_FILE']
        return config
    app.dependency_overrides[get_config] = get_test_config
    return TestClient(app)

@pytest.fixture
def dummy_audio():
    audio = DummyAudio()
    app.dependency_overrides[get_audio] = lambda: audio
    return audio

@pytest.fixture
def mock_playlist_with_tracks(test_client_with_mock_db):
    """Creates a mock playlist with tracks in the test DB and returns its id."""
    from app.src.config import Config
    from app.src.data.playlist_repository import PlaylistRepository
    import uuid
    config = Config()
    repo = PlaylistRepository(config)
    playlist_id = str(uuid.uuid4())
    playlist_data = {
        'id': playlist_id,
        'type': 'playlist',
        'title': 'Mock Playlist',
        'path': 'mock_playlist',
        'created_at': '2025-01-01T00:00:00Z',
        'tracks': [
            {"number": 1, "title": "Mock Song 1", "filename": "mock1.mp3", "duration": "3:00", "artist": "Mock Artist", "album": "Mock Album", "play_counter": 0},
            {"number": 2, "title": "Mock Song 2", "filename": "mock2.mp3", "duration": "2:30", "artist": "Mock Artist", "album": "Mock Album", "play_counter": 0}
        ]
    }
    repo.create_playlist(playlist_data)
    return playlist_id

