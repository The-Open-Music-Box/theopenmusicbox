import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from app.main import app
from app.src.routes.nfc_routes import get_nfc_service
import uuid

# --- NFC Association Initiate ---
def test_initiate_nfc_association_missing_playlist():
    # Use a dummy NFC for all tests
    class DummyNFC:
        def start_association_mode(self, playlist_id):
            return True
    def dummy_get_nfc_service():
        return DummyNFC()
    app.dependency_overrides = {}
    from app.src.routes.nfc_routes import get_nfc_service
    app.dependency_overrides[get_nfc_service] = dummy_get_nfc_service
    with TestClient(app) as client:
        response = client.post("/nfc/associate/initiate", json={})
    assert response.status_code == 400
    assert "playlist_id" in response.json().get("error", "")

def test_initiate_nfc_association_success():
    class DummyNFC:
        def start_association_mode(self, playlist_id):
            return True
    def dummy_get_nfc_service():
        return DummyNFC()
    app.dependency_overrides = {}
    from app.src.routes.nfc_routes import get_nfc_service
    app.dependency_overrides[get_nfc_service] = dummy_get_nfc_service
    playlist_id = str(uuid.uuid4())
    with TestClient(app) as client:
        response = client.post("/nfc/associate/initiate", json={"playlist_id": playlist_id})
    assert response.status_code == 200
    assert response.json()["status"] == "association_initiated"

# --- NFC Simulate Tag Detection ---
def test_simulate_tag_detection_missing_tag():
    with TestClient(app) as client:
        response = client.post("/nfc/simulate_tag", json={})
    assert response.status_code == 400
    assert "tag_id missing" in response.json().get("message", "")

# --- NFC Disassociate Tag ---
def test_disassociate_nfc_tag_missing_fields():
    with TestClient(app) as client:
        response = client.post("/nfc/disassociate", json={})
    assert response.status_code == 400
    assert "playlist_id and nfc_tag" in response.json().get("error", "")
