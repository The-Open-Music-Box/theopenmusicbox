# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for application services following Domain-Driven Design principles.

These tests verify that application services correctly coordinate domain operations
and implement use cases without containing business logic.
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
        
        # Mock the actual method used by the service
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
        
        # Verify repository was not called for invalid data
        assert not hasattr(self.mock_repository, 'create_playlist') or \
               not self.mock_repository.create_playlist.called
    
    @pytest.mark.asyncio
    async def test_create_playlist_use_case_repository_error(self):
        """Test handling repository errors during playlist creation."""
        # Arrange
        self.mock_repository.create_playlist = Mock(side_effect=Exception("Database error"))
        
        # Act
        result = await self.service.create_playlist_use_case("Test Playlist", "Description")
        
        # Assert
        assert result["status"] == "error"
        assert "error_type" in result
        assert "Database error" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_playlist_use_case_success(self):
        """Test successful playlist retrieval."""
        # Arrange
        mock_playlist_data = {
            "id": "retrieve-123",
            "title": "Retrieved Playlist",
            "description": "Test description",
            "tracks": [
                {
                    "track_number": 1,
                    "title": "Track 1", 
                    "filename": "t1.mp3",
                    "file_path": "/t1.mp3"
                }
            ]
        }
        
        self.mock_repository.get_playlist_by_id = Mock(return_value=mock_playlist_data)
        
        # Act
        result = await self.service.get_playlist_use_case("retrieve-123")
        
        # Assert
        assert result["status"] == "success"
        assert result["playlist"]["id"] == "retrieve-123"
        assert result["playlist"]["name"] == "Retrieved Playlist"
        assert len(result["playlist"]["tracks"]) == 1
        
        self.mock_repository.find_by_id.assert_called_once_with("retrieve-123")
    
    @pytest.mark.asyncio
    async def test_get_playlist_use_case_not_found(self):
        """Test playlist retrieval when not found."""
        # Arrange
        self.mock_repository.find_by_id = AsyncMock(return_value=None)
        
        # Act
        result = await self.service.get_playlist_use_case("nonexistent")
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert "Playlist not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_add_track_to_playlist_use_case_success(self):
        """Test successful track addition."""
        # Arrange
        with patch.object(self.service, 'get_playlist_use_case') as mock_get_playlist:
            mock_get_playlist.return_value = {
                "status": "success",
                "playlist": {"id": "playlist-123", "name": "Test"}
            }
            
            with patch('app.src.services.playlist_service.PlaylistService') as mock_legacy:
                mock_instance = Mock()
                mock_legacy.return_value = mock_instance
                mock_instance.add_track_to_playlist.return_value = {"success": True}
                
                track_data = {
                    "track_number": 1,
                    "title": "New Track",
                    "filename": "new.mp3",
                    "file_path": "/music/new.mp3"
                }
                
                # Act
                result = await self.service.add_track_to_playlist_use_case("playlist-123", track_data)
                
                # Assert
                assert result["status"] == "success"
                assert result["playlist_id"] == "playlist-123"
                mock_instance.add_track_to_playlist.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_track_invalid_data(self):
        """Test adding invalid track data."""
        # Arrange
        with patch.object(self.service, 'get_playlist_use_case') as mock_get_playlist:
            mock_get_playlist.return_value = {
                "status": "success",
                "playlist": {"id": "playlist-123"}
            }
            
            # Invalid track data (negative track number)
            invalid_track_data = {
                "track_number": -1,
                "title": "",
                "filename": "",
                "file_path": ""
            }
            
            # Act
            result = await self.service.add_track_to_playlist_use_case("playlist-123", invalid_track_data)
            
            # Assert
            assert result["status"] == "error"
            assert result["error_type"] == "validation_error"
    
    @pytest.mark.asyncio
    async def test_get_all_playlists_use_case(self):
        """Test retrieving all playlists with pagination."""
        # Arrange
        playlists = [
            Playlist(name="Playlist 1", id="p1"),
            Playlist(name="Playlist 2", id="p2")
        ]
        
        self.mock_repository.find_all = AsyncMock(return_value=playlists)
        self.mock_repository.count = AsyncMock(return_value=2)
        
        # Act
        result = await self.service.get_all_playlists_use_case(page=1, page_size=10)
        
        # Assert
        assert result["status"] == "success"
        assert len(result["playlists"]) == 2
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total_count"] == 2
        
        self.mock_repository.find_all.assert_called_once_with(limit=10, offset=0)


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
    async def test_play_playlist_use_case_success(self):
        """Test successful playlist playback."""
        # Arrange
        playlist_data = {
            "id": "playlist-123",
            "name": "Test Playlist",
            "tracks": [
                {
                    "track_number": 1,
                    "title": "Track 1",
                    "filename": "t1.mp3",
                    "file_path": "/music/t1.mp3"
                }
            ]
        }
        
        mock_audio_engine = AsyncMock()
        mock_audio_engine.set_playlist.return_value = True
        
        self.mock_audio_container.is_initialized = True
        self.mock_audio_container.audio_engine = mock_audio_engine
        
        with patch('app.src.application.services.playlist_application_service.PlaylistApplicationService') as mock_playlist_service:
            mock_instance = Mock()
            mock_playlist_service.return_value = mock_instance
            mock_instance.get_playlist_use_case = AsyncMock(return_value={
                "status": "success",
                "playlist": playlist_data
            })
            
            # Act
            result = await self.service.play_playlist_use_case("playlist-123")
            
            # Assert
            assert result["status"] == "success"
            assert result["playlist_id"] == "playlist-123"
            assert result["track_count"] == 1
            
            mock_audio_engine.set_playlist.assert_called_once()
            # Verify playlist domain entity was created
            call_args = mock_audio_engine.set_playlist.call_args[0][0]
            assert isinstance(call_args, Playlist)
            assert call_args.name == "Test Playlist"
    
    @pytest.mark.asyncio
    async def test_play_playlist_empty_playlist_error(self):
        """Test playing empty playlist returns validation error."""
        # Arrange
        empty_playlist_data = {
            "id": "empty-123",
            "name": "Empty Playlist",
            "tracks": []
        }
        
        with patch('app.src.application.services.playlist_application_service.PlaylistApplicationService') as mock_playlist_service:
            mock_instance = Mock()
            mock_playlist_service.return_value = mock_instance
            mock_instance.get_playlist_use_case = AsyncMock(return_value={
                "status": "success",
                "playlist": empty_playlist_data
            })
            
            # Act
            result = await self.service.play_playlist_use_case("empty-123")
            
            # Assert
            assert result["status"] == "error"
            assert result["error_type"] == "validation_error"
            assert "Cannot play empty playlist" in result["message"]
    
    @pytest.mark.asyncio
    async def test_control_playback_use_case_play(self):
        """Test playback control - play action."""
        # Arrange
        mock_audio_engine = AsyncMock()
        mock_audio_engine.resume.return_value = True
        
        self.mock_audio_container.is_initialized = True
        self.mock_audio_container.audio_engine = mock_audio_engine
        
        # Act
        result = await self.service.control_playback_use_case("play")
        
        # Assert
        assert result["status"] == "success"
        assert result["action"] == "play"
        mock_audio_engine.resume.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_control_playback_invalid_action(self):
        """Test invalid playback action."""
        # Act
        result = await self.service.control_playback_use_case("invalid_action")
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "Unknown playback action" in result["message"]
    
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
        mock_audio_engine.get_state_dict.return_value = mock_state
        
        self.mock_audio_container.is_initialized = True
        self.mock_audio_container.audio_engine = mock_audio_engine
        
        # Act
        result = await self.service.get_playback_status_use_case()
        
        # Assert
        assert result["status"] == "success"
        assert result["playback_status"]["is_playing"] is True
        assert result["playback_status"]["volume"] == 75
    
    @pytest.mark.asyncio
    async def test_set_volume_use_case_success(self):
        """Test successful volume setting."""
        # Arrange
        mock_audio_engine = AsyncMock()
        mock_audio_engine.set_volume.return_value = True
        
        self.mock_audio_container.is_initialized = True
        self.mock_audio_container.audio_engine = mock_audio_engine
        
        # Act
        result = await self.service.set_volume_use_case(85)
        
        # Assert
        assert result["status"] == "success"
        assert result["volume"] == 85
        mock_audio_engine.set_volume.assert_called_once_with(85)
    
    @pytest.mark.asyncio
    async def test_set_volume_invalid_range(self):
        """Test volume setting with invalid range."""
        # Act - test volume over 100
        result = await self.service.set_volume_use_case(150)
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "Volume must be between 0 and 100" in result["message"]
        
        # Act - test negative volume
        result = await self.service.set_volume_use_case(-10)
        
        # Assert
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"