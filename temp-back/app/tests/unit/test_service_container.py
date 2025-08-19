# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unit tests for ServiceContainer.

This module contains comprehensive unit tests for the ServiceContainer class,
testing dependency injection, singleton management, and service creation.
"""

import pytest
from unittest.mock import Mock, patch

from app.src.core.service_container import ServiceContainer
from app.src.controllers.audio_controller import AudioController
from app.src.controllers.physical_controls_manager import PhysicalControlsManager
from app.src.services.playlist_crud_service import PlaylistCrudService


class TestServiceContainer:
    """Test cases for ServiceContainer functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_config = Mock()
        self.mock_config.playlists_directory = "/test/playlists"
        self.mock_config.volume_default = 50
        
        self.container = ServiceContainer(self.mock_config)

    def test_initialization(self):
        """Test ServiceContainer initialization."""
        assert self.container.config == self.mock_config
        assert isinstance(self.container._services, dict)
        assert isinstance(self.container._singletons, dict)
        
        # Check that singleton services are registered
        assert AudioController in self.container._singletons
        assert PhysicalControlsManager in self.container._singletons
        assert PlaylistCrudService in self.container._singletons

    def test_get_singleton_service_creates_once(self):
        """Test that singleton services are created only once."""
        with patch.object(self.container, '_create_service_instance') as mock_create:
            mock_instance = Mock()
            mock_create.return_value = mock_instance
            
            # First call should create instance
            result1 = self.container.get_service(PlaylistCrudService)
            assert result1 == mock_instance
            mock_create.assert_called_once_with(PlaylistCrudService)
            
            # Second call should return same instance
            mock_create.reset_mock()
            result2 = self.container.get_service(PlaylistCrudService)
            assert result2 == mock_instance
            mock_create.assert_not_called()

    def test_get_non_singleton_service_creates_each_time(self):
        """Test that non-singleton services are created each time."""
        from app.src.services.upload_service import UploadService
        
        with patch.object(self.container, '_create_service_instance') as mock_create:
            mock_instance1 = Mock()
            mock_instance2 = Mock()
            mock_create.side_effect = [mock_instance1, mock_instance2]
            
            # Each call should create new instance
            result1 = self.container.get_service(UploadService)
            result2 = self.container.get_service(UploadService)
            
            assert result1 == mock_instance1
            assert result2 == mock_instance2
            assert mock_create.call_count == 2

    @patch('app.src.core.service_container.get_audio')
    def test_create_audio_controller_instance(self, mock_get_audio):
        """Test creation of AudioController instance with dependencies."""
        mock_audio_service = Mock()
        mock_get_audio.return_value = mock_audio_service
        
        result = self.container._create_service_instance(AudioController)
        
        assert isinstance(result, AudioController)
        mock_get_audio.assert_called_once()

    def test_create_physical_controls_manager_instance(self):
        """Test creation of PhysicalControlsManager instance with dependencies."""
        mock_audio_controller = Mock()
        
        with patch.object(self.container, 'get_service') as mock_get_service:
            mock_get_service.return_value = mock_audio_controller
            
            result = self.container._create_service_instance(PhysicalControlsManager)
            
            assert isinstance(result, PhysicalControlsManager)
            mock_get_service.assert_called_once_with(AudioController)

    def test_create_service_instance_with_config(self):
        """Test creation of service instance that requires config."""
        result = self.container._create_service_instance(PlaylistCrudService)
        
        assert isinstance(result, PlaylistCrudService)
        assert result.config_obj == self.mock_config

    def test_create_service_instance_error_handling(self):
        """Test error handling in service instance creation."""
        class FailingService:
            def __init__(self):
                raise Exception("Creation failed")
        
        with pytest.raises(Exception, match="Creation failed"):
            self.container._create_service_instance(FailingService)

    def test_register_service(self):
        """Test manual service registration."""
        mock_service = Mock()
        
        self.container.register_service(PlaylistCrudService, mock_service)
        
        result = self.container.get_service(PlaylistCrudService)
        assert result == mock_service

    def test_clear_singletons(self):
        """Test clearing singleton instances."""
        # Create a singleton instance
        self.container.get_service(PlaylistCrudService)
        assert self.container._singletons[PlaylistCrudService] is not None
        
        # Clear singletons
        self.container.clear_singletons()
        assert self.container._singletons[PlaylistCrudService] is None

    def test_get_audio_controller_convenience_method(self):
        """Test convenience method for getting audio controller."""
        with patch.object(self.container, 'get_service') as mock_get_service:
            mock_controller = Mock()
            mock_get_service.return_value = mock_controller
            
            result = self.container.get_audio_controller()
            
            assert result == mock_controller
            mock_get_service.assert_called_once_with(AudioController)

    def test_get_physical_controls_manager_convenience_method(self):
        """Test convenience method for getting physical controls manager."""
        with patch.object(self.container, 'get_service') as mock_get_service:
            mock_manager = Mock()
            mock_get_service.return_value = mock_manager
            
            result = self.container.get_physical_controls_manager()
            
            assert result == mock_manager
            mock_get_service.assert_called_once_with(PhysicalControlsManager)

    def test_get_playlist_crud_service_convenience_method(self):
        """Test convenience method for getting playlist CRUD service."""
        with patch.object(self.container, 'get_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            result = self.container.get_playlist_crud_service()
            
            assert result == mock_service
            mock_get_service.assert_called_once_with(PlaylistCrudService)

    def test_get_upload_service_convenience_method(self):
        """Test convenience method for getting upload service."""
        from app.src.services.upload_service import UploadService
        
        with patch.object(self.container, 'get_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            result = self.container.get_upload_service()
            
            assert result == mock_service
            mock_get_service.assert_called_once_with(UploadService)
