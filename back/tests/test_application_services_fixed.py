# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Fixed tests for application services following Domain-Driven Design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.src.application.services.playlist_application_service import DataApplicationService as PlaylistApplicationService
from app.src.application.services.audio_application_service import AudioApplicationService
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track


class TestPlaylistApplicationService:
    """Test playlist application service use cases."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_repository = Mock()
        self.mock_file_service = Mock()
        self.service = PlaylistApplicationService(
            playlist_repository=self.mock_repository,
            file_system_service=self.mock_file_service
        )
    
    @pytest.mark.asyncio
    async def test_create_playlist_use_case_success(self):
        """Test successful playlist creation use case."""
        # Arrange
        playlist_id = "test-playlist-123"
        self.mock_repository.create_playlist = Mock(return_value=playlist_id)
        
        # Act
        result = await self.service.create_playlist_use_case("Test Playlist", "Test Description")
        
        # Assert
        assert result["status"] == "success"
        assert result["playlist_id"] == playlist_id
        
        # Verify the repository was called with correct data
        self.mock_repository.create_playlist.assert_called_once()
        call_args = self.mock_repository.create_playlist.call_args[0][0]
        assert call_args["title"] == "Test Playlist"
        assert call_args["description"] == "Test Description"
    
    @pytest.mark.asyncio
    async def test_create_playlist_use_case_validation_error(self):
        """Test playlist creation with invalid data."""
        # Act - try to create playlist with empty name
        result = await self.service.create_playlist_use_case("", "Description")
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "Invalid playlist data" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_playlist_use_case_success(self):
        """Test successful playlist retrieval."""
        # Arrange
        mock_playlist_data = {
            "id": "retrieve-123",
            "title": "Retrieved Playlist",
            "description": "Test description",
            "tracks": []
        }
        self.mock_repository.get_playlist_by_id = Mock(return_value=mock_playlist_data)
        
        # Act
        result = await self.service.get_playlist_use_case("retrieve-123")
        
        # Assert
        assert result["status"] == "success"
        assert result["playlist"]["id"] == "retrieve-123"
        assert result["playlist"]["title"] == "Retrieved Playlist"
        
        self.mock_repository.get_playlist_by_id.assert_called_once_with("retrieve-123")
    
    @pytest.mark.asyncio
    async def test_get_playlist_use_case_not_found(self):
        """Test playlist retrieval when not found."""
        # Arrange
        self.mock_repository.get_playlist_by_id = Mock(return_value=None)
        
        # Act
        result = await self.service.get_playlist_use_case("nonexistent")
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert "not found" in result["message"]


class TestAudioApplicationService:
    """Test audio application service use cases."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_audio_container = Mock()
        self.mock_playlist_service = Mock()
        self.mock_state_manager = Mock()
        self.service = AudioApplicationService(
            audio_domain_container=self.mock_audio_container,
            playlist_application_service=self.mock_playlist_service,
            state_manager=self.mock_state_manager
        )
    
    @pytest.mark.asyncio
    async def test_control_playback_use_case_play(self):
        """Test playback control - play action."""
        # Arrange
        mock_audio_engine = Mock()
        mock_audio_engine.resume = AsyncMock(return_value=True)  # Async method
        
        self.mock_audio_container.is_initialized = True
        self.mock_audio_container.audio_engine = mock_audio_engine
        
        # Act
        result = await self.service.control_playback_use_case("play")
        
        # Assert
        assert result["status"] == "success"
        mock_audio_engine.resume.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_control_playback_invalid_action(self):
        """Test playback control with invalid action."""
        # Act
        result = await self.service.control_playback_use_case("invalid_action")
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "Invalid action" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_playback_status_use_case(self):
        """Test getting playback status."""
        # Arrange
        mock_state = {
            "is_playing": True,
            "is_paused": False,
            "current_track": {"title": "Current Song"},
            "volume": 75
        }
        
        mock_audio_engine = Mock()
        mock_audio_engine.get_state_dict = AsyncMock(return_value=mock_state)  # Async method
        
        self.mock_audio_container.is_initialized = True
        self.mock_audio_container.audio_engine = mock_audio_engine
        
        # Act
        result = await self.service.get_playback_status_use_case()
        
        # Assert
        assert result["status"] == "success"
        assert result["playback_state"]["is_playing"] is True
        assert result["playback_state"]["volume"] == 75
    
    @pytest.mark.asyncio
    async def test_set_volume_use_case_success(self):
        """Test successful volume setting."""
        # Arrange
        mock_audio_engine = Mock()
        mock_audio_engine.set_volume = AsyncMock(return_value=True)  # Async method
        
        self.mock_audio_container.is_initialized = True
        self.mock_audio_container.audio_engine = mock_audio_engine
        
        # Act
        result = await self.service.set_volume_use_case(85)
        
        # Assert
        assert result["status"] == "success"
        mock_audio_engine.set_volume.assert_called_once_with(85)
    
    @pytest.mark.asyncio
    async def test_set_volume_invalid_range(self):
        """Test volume setting with invalid range."""
        # Act - volume above 100
        result = await self.service.set_volume_use_case(150)
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "Volume must be between 0 and 100" in result["message"]