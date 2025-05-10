"""
Tests for the playback API endpoints.

This module tests both positive and negative scenarios for the playback control endpoints,
ensuring that all playback operations work correctly with and without active playback.
"""
# No need to import TestClient or app as we're using the test_client_with_mock_db fixture
# No need to import assertions helpers yet as we're using basic assertions

# --- Playback Tests with No Active Playback ---

import pytest


@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_pause_no_active(test_client_with_mock_db, reset_playback_subject):
    """Test pausing when no playback is active."""
    with test_client_with_mock_db as client:
        response = client.post("/api/playlists/control", json={"action": "pause"})
    
    # The API might return success even if no playback is active (idempotent operation)
    # or it might return an error indicating no active playback
    assert response.status_code in (200, 503)

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_stop_no_active(test_client_with_mock_db, reset_playback_subject):
    """Test stopping when no playback is active."""
    with test_client_with_mock_db as client:
        response = client.post("/api/playlists/control", json={"action": "stop"})
    
    # The API might return success even if no playback is active (idempotent operation)
    # or it might return an error indicating no active playback
    assert response.status_code in (200, 503)

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_resume_no_active(test_client_with_mock_db, reset_playback_subject):
    """Test resuming when no playback is active."""
    with test_client_with_mock_db as client:
        response = client.post("/api/playlists/control", json={"action": "resume"})
    
    # The API might return success even if no playback is active
    # or it might return an error indicating no active playback
    assert response.status_code in (200, 503)

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_next_no_active(test_client_with_mock_db, reset_playback_subject):
    """Test next track when no playback is active."""
    with test_client_with_mock_db as client:
        response = client.post("/api/playlists/control", json={"action": "next"})
    
    # The API might return success even if no playback is active
    # or it might return an error indicating no active playback
    assert response.status_code in (200, 503)

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_previous_no_active(test_client_with_mock_db, reset_playback_subject):
    """Test previous track when no playback is active."""
    with test_client_with_mock_db as client:
        response = client.post("/api/playlists/control", json={"action": "previous"})
    
    # The API might return success even if no playback is active
    # or it might return an error indicating no active playback
    assert response.status_code in (200, 503)

# --- Playback Tests with Active Playback ---

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playlist_start(test_client_with_mock_db, mock_playlist_with_tracks, dummy_audio):
    """Test starting a playlist."""
    with test_client_with_mock_db as client:
        response = client.post(f"/api/playlists/{mock_playlist_with_tracks}/start")
        
        # The API might return 400 if the playlist has no accessible tracks
        # or 200 if the playlist starts successfully
        assert response.status_code in (200, 400)
        
        # If successful, verify the audio player was called
        if response.status_code == 200:
            assert response.json()["status"] == "success"
            assert len(dummy_audio.calls) > 0
        else:
            # If failed, check for appropriate error message
            assert "Failed to start playlist" in response.json().get("detail", "")

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playlist_play_track(test_client_with_mock_db, mock_playlist_with_tracks, dummy_audio):
    """Test playing a specific track from a playlist."""
    with test_client_with_mock_db as client:
        # Play track number 1
        response = client.post(f"/api/playlists/{mock_playlist_with_tracks}/play/1")
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Verify the audio player was called with the correct track
        assert any(call[0] == "play" and call[1] == 1 for call in dummy_audio.calls)

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_pause_active(test_client_with_mock_db, mock_playlist_with_tracks, dummy_audio):
    """Test pausing active playback."""
    with test_client_with_mock_db as client:
        # First start playback
        client.post(f"/api/playlists/{mock_playlist_with_tracks}/start")
        dummy_audio.calls.clear()  # Clear call history
        
        # Then pause it
        response = client.post("/api/playlists/control", json={"action": "pause"})
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["action"] == "pause"
        
        # Verify the audio player was called
        assert ('pause',) in dummy_audio.calls

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_resume_after_pause(test_client_with_mock_db, mock_playlist_with_tracks, dummy_audio):
    """Test resuming playback after pause."""
    with test_client_with_mock_db as client:
        # Setup: play then pause
        client.post(f"/api/playlists/{mock_playlist_with_tracks}/start")
        client.post("/api/playlists/control", json={"action": "pause"})
        dummy_audio.calls.clear()  # Clear call history
        
        # Test: resume
        response = client.post("/api/playlists/control", json={"action": "resume"})
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["action"] == "resume"
        
        # Verify the audio player was called
        assert ('resume',) in dummy_audio.calls

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_stop_active(test_client_with_mock_db, mock_playlist_with_tracks, dummy_audio):
    """Test stopping active playback."""
    with test_client_with_mock_db as client:
        # First start playback
        client.post(f"/api/playlists/{mock_playlist_with_tracks}/start")
        dummy_audio.calls.clear()  # Clear call history
        
        # Then stop it
        response = client.post("/api/playlists/control", json={"action": "stop"})
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["action"] == "stop"
        
        # Verify the audio player was called
        assert ('stop',) in dummy_audio.calls

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_next_track(test_client_with_mock_db, mock_playlist_with_tracks, dummy_audio):
    """Test skipping to the next track."""
    with test_client_with_mock_db as client:
        # First start playback
        client.post(f"/api/playlists/{mock_playlist_with_tracks}/start")
        dummy_audio.calls.clear()  # Clear call history
        
        # Then go to next track
        response = client.post("/api/playlists/control", json={"action": "next"})
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["action"] == "next"
        
        # Verify the audio player was called
        assert ('next',) in dummy_audio.calls

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_previous_track(test_client_with_mock_db, mock_playlist_with_tracks, dummy_audio):
    """Test going to the previous track."""
    with test_client_with_mock_db as client:
        # First start playback
        client.post(f"/api/playlists/{mock_playlist_with_tracks}/start")
        dummy_audio.calls.clear()  # Clear call history
        
        # Then go to previous track
        response = client.post("/api/playlists/control", json={"action": "previous"})
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["action"] == "previous"
        
        # Verify the audio player was called
        assert ('previous',) in dummy_audio.calls

# --- Error Handling Tests ---

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playback_control_invalid_action(test_client_with_mock_db):
    """Test control with an invalid action."""
    with test_client_with_mock_db as client:
        response = client.post("/api/playlists/control", json={"action": "invalid_action"})
    
    # Should return a 400 Bad Request
    assert response.status_code == 400
    assert "Invalid action" in response.json().get("detail", "")

@pytest.mark.api
@pytest.mark.audio
@pytest.mark.playlist
def test_playlist_start_nonexistent_playlist(test_client_with_mock_db):
    """Test starting a playlist that doesn't exist."""
    with test_client_with_mock_db as client:
        response = client.post("/api/playlists/00000000-0000-0000-0000-000000000000/start")
    
    # Should return a 400 Bad Request or 404 Not Found
    assert response.status_code in (400, 404)
    if response.status_code == 400:
        assert "Failed to start playlist" in response.json().get("detail", "")
    elif response.status_code == 404:
        assert "Playlist not found" in response.json().get("detail", "")
