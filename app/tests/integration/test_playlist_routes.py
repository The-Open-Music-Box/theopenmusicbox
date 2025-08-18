# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Integration tests for playlist routes.

This module contains integration tests for the playlist API endpoints,
testing the complete request-response cycle with real service dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.tests.mocks.mock_audio_service import MockAudioService
from app.tests.mocks.mock_controls_manager import MockControlsManager


class TestPlaylistRoutesIntegration:
    """Integration test cases for playlist routes."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)
        self.mock_audio_service = MockAudioService()
        self.mock_controls_manager = MockControlsManager()

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_get_all_playlists_success(self, mock_get_controls, mock_get_audio):
        """Test successful retrieval of all playlists."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_all.return_value = [
                {"id": 1, "name": "Playlist 1"},
                {"id": 2, "name": "Playlist 2"}
            ]
            mock_get_repo.return_value = mock_repo
            
            response = self.client.get("/api/playlists")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Playlist 1"

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_get_playlist_by_id_success(self, mock_get_controls, mock_get_audio):
        """Test successful retrieval of playlist by ID."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = {"id": 1, "name": "Test Playlist"}
            mock_get_repo.return_value = mock_repo
            
            response = self.client.get("/api/playlists/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "Test Playlist"

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_get_playlist_by_id_not_found(self, mock_get_controls, mock_get_audio):
        """Test retrieval of non-existent playlist."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = None
            mock_get_repo.return_value = mock_repo
            
            response = self.client.get("/api/playlists/999")
            
            assert response.status_code == 404

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_create_playlist_success(self, mock_get_controls, mock_get_audio):
        """Test successful playlist creation."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        playlist_data = {
            "name": "New Playlist",
            "description": "Test description"
        }
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.create.return_value = {"id": 1, **playlist_data}
            mock_get_repo.return_value = mock_repo
            
            response = self.client.post("/api/playlists", json=playlist_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Playlist"

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_create_playlist_invalid_data(self, mock_get_controls, mock_get_audio):
        """Test playlist creation with invalid data."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        invalid_data = {"description": "Missing name"}
        
        response = self.client.post("/api/playlists", json=invalid_data)
        
        assert response.status_code == 400

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_update_playlist_success(self, mock_get_controls, mock_get_audio):
        """Test successful playlist update."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        update_data = {"name": "Updated Playlist"}
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = {"id": 1, "name": "Old Name"}
            mock_repo.update.return_value = {"id": 1, "name": "Updated Playlist"}
            mock_get_repo.return_value = mock_repo
            
            response = self.client.put("/api/playlists/1", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Playlist"

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_delete_playlist_success(self, mock_get_controls, mock_get_audio):
        """Test successful playlist deletion."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = {"id": 1, "name": "Test"}
            mock_repo.delete.return_value = True
            mock_get_repo.return_value = mock_repo
            
            response = self.client.delete("/api/playlists/1")
            
            assert response.status_code == 200

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_play_playlist_success(self, mock_get_controls, mock_get_audio):
        """Test successful playlist playback."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = {
                "id": 1, 
                "name": "Test Playlist",
                "tracks": [{"id": 1, "filename": "track1.mp3"}]
            }
            mock_get_repo.return_value = mock_repo
            
            response = self.client.post("/api/playlists/1/play")
            
            assert response.status_code == 200
            assert self.mock_audio_service.is_playing() is True

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_reorder_tracks_success(self, mock_get_controls, mock_get_audio):
        """Test successful track reordering."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        reorder_data = {"new_order": [3, 1, 2]}
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo, \
             patch('app.src.dependencies.get_track_repository') as mock_get_track_repo:
            
            mock_playlist_repo = Mock()
            mock_playlist_repo.get_by_id.return_value = {"id": 1, "name": "Test"}
            mock_get_repo.return_value = mock_playlist_repo
            
            mock_track_repo = Mock()
            mock_track_repo.get_by_playlist_id.return_value = [
                {"id": 1, "order": 1}, {"id": 2, "order": 2}, {"id": 3, "order": 3}
            ]
            mock_track_repo.update_order.return_value = True
            mock_get_track_repo.return_value = mock_track_repo
            
            response = self.client.post("/api/playlists/1/reorder", json=reorder_data)
            
            assert response.status_code == 200

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_delete_tracks_success(self, mock_get_controls, mock_get_audio):
        """Test successful track deletion."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        delete_data = {"track_numbers": [1, 3]}
        
        with patch('app.src.dependencies.get_playlist_repository') as mock_get_repo, \
             patch('app.src.dependencies.get_track_repository') as mock_get_track_repo, \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            
            mock_playlist_repo = Mock()
            mock_playlist_repo.get_by_id.return_value = {"id": 1, "name": "Test"}
            mock_get_repo.return_value = mock_playlist_repo
            
            mock_track_repo = Mock()
            mock_track_repo.get_by_playlist_id.return_value = [
                {"id": 1, "order": 1, "filename": "track1.mp3"},
                {"id": 2, "order": 2, "filename": "track2.mp3"},
                {"id": 3, "order": 3, "filename": "track3.mp3"}
            ]
            mock_track_repo.delete.return_value = True
            mock_get_track_repo.return_value = mock_track_repo
            
            response = self.client.delete("/api/playlists/1/tracks", json=delete_data)
            
            assert response.status_code == 200

    @patch('app.src.dependencies.get_audio')
    @patch('app.src.dependencies.get_controles_manager')
    def test_audio_control_integration(self, mock_get_controls, mock_get_audio):
        """Test audio control integration through routes."""
        mock_get_audio.return_value = self.mock_audio_service
        mock_get_controls.return_value = self.mock_controls_manager
        
        # Test play
        response = self.client.post("/api/audio/play")
        assert response.status_code == 200
        assert self.mock_audio_service.is_playing() is True
        
        # Test pause
        response = self.client.post("/api/audio/pause")
        assert response.status_code == 200
        assert self.mock_audio_service.is_playing() is False
        
        # Test volume control
        response = self.client.post("/api/audio/volume", json={"volume": 75})
        assert response.status_code == 200
        assert self.mock_audio_service.get_volume() == 75
