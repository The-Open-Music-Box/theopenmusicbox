import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from app.main import app

# --- Pause Playback (no active) ---
def test_playback_pause_no_active():
    with TestClient(app) as client:
        response = client.post("/playback/pause")
    assert response.status_code in (200, 404)

# --- Stop Playback (no active) ---
def test_playback_stop_no_active():
    with TestClient(app) as client:
        response = client.post("/playback/stop")
    assert response.status_code in (200, 404)
