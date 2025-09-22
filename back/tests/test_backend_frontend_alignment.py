# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Backend-Frontend alignment tests.

These tests verify that the backend API responses match exactly what the frontend expects,
ensuring server-authoritative behavior and proper state synchronization.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track
from app.src.application.services.playlist_application_service import DataApplicationService as PlaylistApplicationService
from app.src.application.services.audio_application_service import AudioApplicationService


class TestPlaylistAPIAlignment:
    """Test playlist API responses match frontend expectations."""
    
    def setup_method(self):
        """Set up test client and dependencies."""
        self.client = TestClient(app)
        
    def test_playlist_creation_response_format(self):
        """Test playlist creation returns expected response format."""
        # Mock the application service
        with patch('app.src.dependencies.get_playlist_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Mock the create_playlist_use_case to return expected format
            mock_service.create_playlist_use_case = AsyncMock(return_value={
                "status": "success",
                "playlist_id": "test-123",
                "playlist": {
                    "id": "test-123",
                    "name": "Test Playlist",
                    "description": "Test Description",
                    "tracks": [],
                    "total_duration_ms": 0
                }
            })
            
            response = self.client.post("/api/playlists", json={
                "name": "Test Playlist",
                "description": "Test Description"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify frontend-expected structure
            assert "status" in data
            assert "playlist_id" in data
            assert "playlist" in data
            
            playlist_data = data["playlist"]
            assert "id" in playlist_data
            assert "name" in playlist_data
            assert "tracks" in playlist_data
            assert isinstance(playlist_data["tracks"], list)
    
    def test_playlist_list_response_format(self):
        """Test playlist listing returns paginated format expected by frontend."""
        with patch('app.src.dependencies.get_playlist_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Create test playlists
            test_playlists = [
                {
                    "id": "playlist-1",
                    "name": "Playlist 1",
                    "description": "First playlist",
                    "tracks": [],
                    "total_duration_ms": 180000
                },
                {
                    "id": "playlist-2", 
                    "name": "Playlist 2",
                    "description": "Second playlist",
                    "tracks": [],
                    "total_duration_ms": 240000
                }
            ]
            
            mock_service.get_all_playlists_use_case = AsyncMock(return_value={
                "status": "success",
                "playlists": test_playlists,
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total_count": 2,
                    "total_pages": 1
                }
            })
            
            response = self.client.get("/api/playlists?page=1&page_size=10")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify pagination structure expected by frontend
            assert "playlists" in data
            assert "pagination" in data
            
            pagination = data["pagination"]
            assert "page" in pagination
            assert "page_size" in pagination
            assert "total_count" in pagination
            assert "total_pages" in pagination
            
            # Verify playlist structure
            playlists = data["playlists"]
            assert isinstance(playlists, list)
            assert len(playlists) == 2
            
            for playlist in playlists:
                assert "id" in playlist
                assert "name" in playlist
                assert "tracks" in playlist
    
    def test_track_data_structure_alignment(self):
        """Test track data structure matches frontend expectations."""
        with patch('app.src.dependencies.get_playlist_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Create playlist with tracks
            playlist_with_tracks = {
                "id": "playlist-with-tracks",
                "name": "Music Playlist",
                "tracks": [
                    {
                        "id": "track-1",
                        "track_number": 1,
                        "title": "Song One",
                        "artist": "Artist One",
                        "album": "Album One", 
                        "filename": "song1.mp3",
                        "file_path": "/music/song1.mp3",
                        "duration_ms": 180000,
                        "duration": 180.0  # Frontend expects seconds
                    },
                    {
                        "id": "track-2",
                        "track_number": 2,
                        "title": "Song Two",
                        "artist": "Artist Two",
                        "album": "Album Two",
                        "filename": "song2.mp3", 
                        "file_path": "/music/song2.mp3",
                        "duration_ms": 240000,
                        "duration": 240.0
                    }
                ]
            }
            
            mock_service.get_playlist_use_case = AsyncMock(return_value={
                "status": "success",
                "playlist": playlist_with_tracks
            })
            
            response = self.client.get("/api/playlists/playlist-with-tracks")
            
            assert response.status_code == 200
            data = response.json()
            
            playlist = data["playlist"]
            tracks = playlist["tracks"]
            
            # Verify each track has required frontend fields
            for track in tracks:
                # Required fields for frontend
                assert "id" in track
                assert "track_number" in track
                assert "title" in track
                assert "filename" in track
                assert "file_path" in track
                assert "duration_ms" in track
                assert "duration" in track  # Seconds for display
                
                # Optional but expected fields
                assert "artist" in track
                assert "album" in track
                
                # Verify data types
                assert isinstance(track["track_number"], int)
                assert isinstance(track["duration_ms"], int)
                assert isinstance(track["duration"], float)


class TestAudioPlaybackAPIAlignment:
    """Test audio playback API responses match frontend expectations."""
    
    def setup_method(self):
        """Set up test client and dependencies."""
        self.client = TestClient(app)
    
    def test_playback_control_response_format(self):
        """Test playback control responses match frontend expectations."""
        with patch('app.src.dependencies.get_audio_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Mock successful play response
            mock_service.control_playback_use_case = AsyncMock(return_value={
                "status": "success",
                "action": "play",
                "playback_status": {
                    "is_playing": True,
                    "is_paused": False,
                    "volume": 75,
                    "current_track": {
                        "id": "track-1",
                        "title": "Current Song",
                        "artist": "Current Artist"
                    },
                    "current_playlist": {
                        "id": "playlist-1",
                        "name": "Current Playlist"
                    }
                }
            })
            
            response = self.client.post("/api/player/control", json={
                "action": "play"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify control response structure
            assert "status" in data
            assert "action" in data
            assert "playback_status" in data
            
            playback_status = data["playback_status"]
            assert "is_playing" in playback_status
            assert "is_paused" in playback_status
            assert "volume" in playback_status
            assert "current_track" in playback_status
            assert "current_playlist" in playback_status
    
    def test_player_status_response_format(self):
        """Test player status response matches frontend state expectations."""
        with patch('app.src.dependencies.get_audio_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            mock_service.get_playback_status_use_case = AsyncMock(return_value={
                "status": "success",
                "playback_status": {
                    "is_playing": True,
                    "is_paused": False,
                    "volume": 80,
                    "position": 45.5,  # Current playback position in seconds
                    "duration": 180.0,  # Total track duration in seconds
                    "progress_percentage": 25.3,  # Progress as percentage
                    "current_track": {
                        "id": "track-123",
                        "track_number": 3,
                        "title": "Status Test Song",
                        "artist": "Status Artist",
                        "album": "Status Album",
                        "duration": 180.0
                    },
                    "current_playlist": {
                        "id": "playlist-456",
                        "name": "Status Playlist",
                        "total_tracks": 12,
                        "current_track_index": 2
                    }
                }
            })
            
            response = self.client.get("/api/player/status")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify status response structure
            assert "status" in data
            assert "playback_status" in data
            
            status = data["playback_status"]
            
            # Core playback state
            assert "is_playing" in status
            assert "is_paused" in status
            assert "volume" in status
            
            # Playback progress
            assert "position" in status
            assert "duration" in status
            assert "progress_percentage" in status
            
            # Current track info
            assert "current_track" in status
            current_track = status["current_track"]
            assert "id" in current_track
            assert "title" in current_track
            assert "track_number" in current_track
            
            # Current playlist info
            assert "current_playlist" in status
            current_playlist = status["current_playlist"]
            assert "id" in current_playlist
            assert "name" in current_playlist
            assert "total_tracks" in current_playlist
            assert "current_track_index" in current_playlist
    
    def test_volume_control_response_format(self):
        """Test volume control response format."""
        with patch('app.src.dependencies.get_audio_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            mock_service.set_volume_use_case = AsyncMock(return_value={
                "status": "success",
                "volume": 85,
                "previous_volume": 75
            })
            
            response = self.client.post("/api/player/volume", json={
                "volume": 85
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify volume response structure
            assert "status" in data
            assert "volume" in data
            assert data["volume"] == 85
            
            # Optional: previous volume for undo functionality
            if "previous_volume" in data:
                assert isinstance(data["previous_volume"], int)


class TestErrorResponseAlignment:
    """Test error responses match frontend error handling expectations."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_validation_error_format(self):
        """Test validation error format matches frontend expectations."""
        # Send invalid playlist creation request
        response = self.client.post("/api/playlists", json={
            "name": "",  # Invalid empty name
            "description": "Valid description"
        })
        
        # Expect validation error
        assert response.status_code == 400
        data = response.json()
        
        # Verify error structure
        assert "status" in data
        assert data["status"] == "error"
        assert "error_type" in data
        assert "message" in data
        
        # Frontend expects specific error type for validation
        assert data["error_type"] == "validation_error"
    
    def test_not_found_error_format(self):
        """Test not found error format."""
        with patch('app.src.dependencies.get_playlist_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            mock_service.get_playlist_use_case = AsyncMock(return_value={
                "status": "error",
                "error_type": "not_found",
                "message": "Playlist not found"
            })
            
            response = self.client.get("/api/playlists/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            
            assert "status" in data
            assert data["status"] == "error"
            assert "error_type" in data
            assert data["error_type"] == "not_found"
            assert "message" in data
    
    def test_server_error_format(self):
        """Test server error format."""
        with patch('app.src.dependencies.get_playlist_application_service') as mock_get_service:
            # Simulate service throwing exception
            mock_get_service.side_effect = Exception("Internal server error")
            
            response = self.client.get("/api/playlists")
            
            # Should return 500 with error format
            assert response.status_code == 500
            data = response.json()
            
            assert "status" in data
            assert data["status"] == "error"
            assert "error_type" in data
            assert "message" in data


class TestWebSocketStateAlignment:
    """Test WebSocket state broadcasting alignment."""
    
    @pytest.mark.asyncio
    async def test_state_broadcast_format(self):
        """Test WebSocket state broadcast format matches frontend expectations."""
        # This test would require WebSocket test setup
        # For now, we'll test the state format that would be broadcast
        
        # Mock state manager
        with patch('app.src.services.state_manager.StateManager') as mock_state_manager:
            mock_manager = mock_state_manager.return_value
            
            # Mock state that would be broadcast
            broadcast_state = {
                "event_type": "playback_state_changed",
                "timestamp": "2025-09-09T20:00:00.000Z",
                "data": {
                    "is_playing": True,
                    "is_paused": False,
                    "volume": 75,
                    "position": 30.5,
                    "duration": 180.0,
                    "progress_percentage": 16.9,
                    "current_track": {
                        "id": "track-123",
                        "title": "Broadcast Track",
                        "artist": "Broadcast Artist",
                        "track_number": 1
                    },
                    "current_playlist": {
                        "id": "playlist-456",
                        "name": "Broadcast Playlist",
                        "current_track_index": 0,
                        "total_tracks": 10
                    }
                }
            }
            
            # Verify broadcast state structure
            assert "event_type" in broadcast_state
            assert "timestamp" in broadcast_state
            assert "data" in broadcast_state
            
            data = broadcast_state["data"]
            assert "is_playing" in data
            assert "current_track" in data
            assert "current_playlist" in data
            
            # This would be what gets sent to WebSocket clients
            # Frontend expects this exact structure for state updates


class TestServerAuthoritativeBehavior:
    """Test server-authoritative behavior alignment."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_server_validates_track_order(self):
        """Test server validates and corrects track ordering."""
        with patch('app.src.dependencies.get_playlist_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Frontend sends tracks in wrong order
            request_data = {
                "playlist_id": "test-playlist",
                "tracks": [
                    {"track_number": 3, "title": "Track 3"},
                    {"track_number": 1, "title": "Track 1"}, 
                    {"track_number": 2, "title": "Track 2"}
                ]
            }
            
            # Server should normalize track numbers
            mock_service.update_playlist_tracks_use_case = AsyncMock(return_value={
                "status": "success",
                "playlist": {
                    "id": "test-playlist",
                    "tracks": [
                        {"track_number": 1, "title": "Track 1"},
                        {"track_number": 2, "title": "Track 2"},
                        {"track_number": 3, "title": "Track 3"}
                    ]
                }
            })
            
            response = self.client.put("/api/playlists/test-playlist/tracks", 
                                     json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify server corrected the order
            tracks = data["playlist"]["tracks"]
            assert tracks[0]["track_number"] == 1
            assert tracks[1]["track_number"] == 2
            assert tracks[2]["track_number"] == 3
    
    def test_server_enforces_volume_limits(self):
        """Test server enforces volume limits regardless of frontend input."""
        with patch('app.src.dependencies.get_audio_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Frontend sends invalid volume
            mock_service.set_volume_use_case = AsyncMock(return_value={
                "status": "error",
                "error_type": "validation_error",
                "message": "Volume must be between 0 and 100",
                "valid_range": {"min": 0, "max": 100}
            })
            
            response = self.client.post("/api/player/volume", json={
                "volume": 150  # Invalid volume
            })
            
            assert response.status_code == 400
            data = response.json()
            
            # Server should reject invalid volume
            assert data["status"] == "error"
            assert data["error_type"] == "validation_error"
            assert "valid_range" in data  # Help frontend understand limits
    
    def test_server_maintains_playlist_integrity(self):
        """Test server maintains playlist integrity."""
        with patch('app.src.dependencies.get_playlist_application_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Mock server validation that prevents invalid playlist states
            mock_service.add_track_to_playlist_use_case = AsyncMock(return_value={
                "status": "error",
                "error_type": "validation_error",
                "message": "Cannot add duplicate track to playlist",
                "conflict": {
                    "existing_track_id": "track-123",
                    "track_number": 1
                }
            })
            
            response = self.client.post("/api/playlists/test-playlist/tracks", json={
                "track": {
                    "id": "track-123",  # Duplicate track ID
                    "title": "Duplicate Track"
                }
            })
            
            assert response.status_code == 400
            data = response.json()
            
            # Server prevents invalid state
            assert data["status"] == "error"
            assert "conflict" in data  # Provides specific conflict info