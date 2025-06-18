from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "ok"
    # Vérifier que la structure NFC existe maintenant dans la réponse
    assert "nfc" in json_response
    assert "available" in json_response["nfc"]
    assert "code" in json_response["nfc"]
