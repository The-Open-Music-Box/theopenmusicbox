import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

def test_list_playlists_empty():
    with TestClient(app) as client:
        response = client.get("/playlists/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_and_get_playlist():
    playlist_title = f"Test Playlist {uuid.uuid4()}"
    # Create
    with TestClient(app) as client:
        response = client.post("/playlists/", json={"title": playlist_title})
    assert response.status_code in (200, 201)
    playlist = response.json()
    assert playlist["title"] == playlist_title
    playlist_id = playlist["id"]
    # Get
    with TestClient(app) as client:
        response = client.get(f"/playlists/{playlist_id}")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["id"] == playlist_id
    assert fetched["title"] == playlist_title

def test_delete_playlist():
    playlist_title = f"Delete Playlist {uuid.uuid4()}"
    # Create
    with TestClient(app) as client:
        response = client.post("/playlists/", json={"title": playlist_title})
    assert response.status_code in (200, 201)
    playlist_id = response.json()["id"]
    # Delete
    with TestClient(app) as client:
        response = client.delete(f"/playlists/{playlist_id}")
    assert response.status_code == 200
    # Confirm Gone
    with TestClient(app) as client:
        response = client.get(f"/playlists/{playlist_id}")
    assert response.status_code == 404
