import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.src.dependencies import get_config, get_audio
import os

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

# Fixture mock playlist (une seule fois, à la fin)
@pytest.fixture
def mock_playlist_with_tracks(test_client_with_mock_db):
    """Crée une playlist mock avec des pistes dans la DB de test et retourne son id."""
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

# Fixture mock playlist (une seule fois, à la fin)

from app.main import app

from app.src.dependencies import get_config, get_audio

import os



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

