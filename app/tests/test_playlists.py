import uuid
import pytest

# Fixtures are defined in conftest.py

def test_list_playlists_empty(test_client_with_mock_db):
    client = test_client_with_mock_db
    response = client.get("/playlists/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_and_get_playlist(test_client_with_mock_db):
    client = test_client_with_mock_db
    playlist_title = f"Test Playlist {uuid.uuid4()}"
    # Create
    response = client.post("/playlists/", json={"title": playlist_title})
    assert response.status_code in (200, 201)
    playlist = response.json()
    assert playlist["title"] == playlist_title
    playlist_id = playlist["id"]
    # Get
    response = client.get(f"/playlists/{playlist_id}")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["id"] == playlist_id
    assert fetched["title"] == playlist_title

def test_delete_playlist(test_client_with_mock_db):
    client = test_client_with_mock_db
    playlist_title = f"Delete Playlist {uuid.uuid4()}"
    # Create
    response = client.post("/playlists/", json={"title": playlist_title})
    assert response.status_code in (200, 201)
    playlist_id = response.json()["id"]
    # Delete
    response = client.delete(f"/playlists/{playlist_id}")
    assert response.status_code == 200
    # Confirm Gone
    response = client.get(f"/playlists/{playlist_id}")
    assert response.status_code == 404


def test_playback_track_switch(test_client_with_mock_db, dummy_audio, mock_playlist_with_tracks):
    client = test_client_with_mock_db
    audio = dummy_audio
    playlist_id = mock_playlist_with_tracks
    # Simulate playing track 1
    client.post(f"/playlists/{playlist_id}/play/1")
    # Simulate a 'next' action
    client.post("/playlists/control", json={"action": "next"})
    # Check that the correct audio calls were made
    assert audio.calls[0][0] == 'play'
    assert audio.calls[1][0] == 'next'


def test_playback_pause_resume(test_client_with_mock_db, dummy_audio, mock_playlist_with_tracks):
    client = test_client_with_mock_db
    audio = dummy_audio
    playlist_id = mock_playlist_with_tracks
    client.post(f"/playlists/{playlist_id}/play/1")
    client.post("/playlists/control", json={"action": "pause"})
    client.post("/playlists/control", json={"action": "resume"})
    assert audio.calls[0][0] == 'play'
    assert audio.calls[1][0] == 'pause'
    assert audio.calls[2][0] == 'resume'


def test_playback_stop(test_client_with_mock_db, dummy_audio, mock_playlist_with_tracks):
    client = test_client_with_mock_db
    audio = dummy_audio
    playlist_id = mock_playlist_with_tracks
    client.post(f"/playlists/{playlist_id}/play/1")
    client.post("/playlists/control", json={"action": "stop"})
    assert audio.calls[0][0] == 'play'
    assert audio.calls[1][0] == 'stop'


def test_playback_previous(test_client_with_mock_db, dummy_audio, mock_playlist_with_tracks):
    client = test_client_with_mock_db
    audio = dummy_audio
    playlist_id = mock_playlist_with_tracks
    client.post(f"/playlists/{playlist_id}/play/2")  # Simulate playing track 2
    client.post("/playlists/control", json={"action": "previous"})
    assert audio.calls[0][0] == 'play'
    assert audio.calls[1][0] == 'previous'
