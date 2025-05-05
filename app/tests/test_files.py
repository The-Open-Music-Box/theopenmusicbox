import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from app.main import app

# --- List Files ---
def test_list_files():
    with TestClient(app) as client:
        response = client.get("/api/playlists/")
    assert response.status_code == 200
    # New structure: {"playlists": [...]}
    data = response.json()
    assert isinstance(data, dict)
    assert "playlists" in data
    assert isinstance(data["playlists"], list)

# --- Upload File (invalid) ---
def create_playlist_and_get_id(client):
    response = client.post("/api/playlists/", json={"title": "Test Playlist for Upload"})
    assert response.status_code == 200
    playlist_id = response.json()["id"]
    return playlist_id

def test_upload_file_no_file():
    with TestClient(app) as client:
        playlist_id = create_playlist_and_get_id(client)
        response = client.post(f"/api/playlists/{playlist_id}/upload", files={})
    assert response.status_code in (400, 422)
