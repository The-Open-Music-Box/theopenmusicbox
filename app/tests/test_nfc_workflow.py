import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from app.main import app
import uuid

# --- NFC Association Workflow Tests ---
# --- NFC Association Workflow Tests ---
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from app.main import app
import uuid
from app.src.routes.nfc_routes import get_nfc_service

class DummyNFCService:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.mapping = None
        self.last_listen_playlist = None
        class DummySocketIO:
            def emit(self, *args, **kwargs):
                pass
        self.socketio = DummySocketIO()
    def start_listening(self, playlist_id):
        self.started = True
        self.last_listen_playlist = playlist_id
    def stop_listening(self):
        self.stopped = True
    def load_mapping(self, mapping):
        self.mapping = mapping

# Patch dependency for all tests

def setup_nfc_override():
    app.dependency_overrides[get_nfc_service] = lambda: DummyNFCService()

def teardown_nfc_override():
    app.dependency_overrides = {}

def test_observe_nfc_missing_playlist():
    setup_nfc_override()
    with TestClient(app) as client:
        response = client.post("/api/nfc/observe", json={})
    assert response.status_code == 400
    assert "playlist_id" in response.json().get("error", "")
    teardown_nfc_override()

def test_observe_nfc_playlist_not_found():
    setup_nfc_override()
    with TestClient(app) as client:
        playlist_id = str(uuid.uuid4())
        response = client.post("/api/nfc/observe", json={"playlist_id": playlist_id})
    assert response.status_code == 404
    assert "Playlist not found" in response.json().get("error", "")
    teardown_nfc_override()

def test_link_nfc_missing_fields():
    setup_nfc_override()
    with TestClient(app) as client:
        response = client.post("/api/nfc/link", json={})
    assert response.status_code == 400
    assert "playlist_id and tag_id" in response.json().get("error", "")
    teardown_nfc_override()

def test_cancel_nfc_observation():
    setup_nfc_override()
    with TestClient(app) as client:
        response = client.post("/api/nfc/cancel", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    teardown_nfc_override()

# For full workflow, you need to mock both PlaylistService and NFCService

def test_full_nfc_workflow(monkeypatch):
    playlist_id = "test-playlist-1"
    tag_id = "nfc-tag-xyz"
    playlist_obj = {"id": playlist_id, "title": "Test Playlist", "nfc_tag_id": None}
    playlists = [playlist_obj]

    class DummyPlaylistService:
        def __init__(self, config): pass
        def get_playlist_by_id(self, pid):
            return playlist_obj if pid == playlist_id else None
        def get_all_playlists(self):
            return playlists
        def get_playlist_by_nfc_tag(self, tid):
            return playlist_obj if playlist_obj["nfc_tag_id"] == tid else None
        def associate_nfc_tag(self, pid, tid):
            if pid == playlist_id:
                playlist_obj["nfc_tag_id"] = tid
                return True
            for p in playlists:
                if p["id"] == pid:
                    p["nfc_tag_id"] = tid
                    return True
            return False
        def disassociate_nfc_tag(self, pid):
            for p in playlists:
                if p["id"] == pid:
                    p["nfc_tag_id"] = None
                    return True
            return False

    from app.src.routes import nfc_routes
    monkeypatch.setattr(nfc_routes, "PlaylistService", DummyPlaylistService)
    app.dependency_overrides[get_nfc_service] = lambda: DummyNFCService()

    with TestClient(app) as client:
        # Step 1: Observe NFC
        res = client.post("/api/nfc/observe", json={"playlist_id": playlist_id})
        assert res.status_code == 200
        # Step 2: Link tag (first time, should succeed)
        res = client.post("/api/nfc/link", json={"playlist_id": playlist_id, "tag_id": tag_id})
        assert res.status_code == 200
        assert res.json()["status"] == "association_complete"
        # Step 3: Try to link same tag to same playlist (should be already_linked)
        res = client.post("/api/nfc/link", json={"playlist_id": playlist_id, "tag_id": tag_id})
        assert res.status_code == 200
        assert res.json()["status"] == "already_linked"
        # Step 4: Try to link to a different playlist (should require override)
        other_playlist_id = "test-playlist-2"
        other_playlist_obj = {"id": other_playlist_id, "title": "Other Playlist", "nfc_tag_id": None}
        playlists.append(other_playlist_obj)
        res = client.post("/api/nfc/link", json={"playlist_id": other_playlist_id, "tag_id": tag_id})
        assert res.status_code == 409
        # Step 5: Override
        res = client.post("/api/nfc/link", json={"playlist_id": other_playlist_id, "tag_id": tag_id, "override": True})
        assert res.status_code == 200
        assert res.json()["status"] == "association_complete"
        # Step 6: Cancel observation
        res = client.post("/api/nfc/cancel", json={})
        assert res.status_code == 200
        assert res.json()["status"] == "cancelled"
    teardown_nfc_override()
