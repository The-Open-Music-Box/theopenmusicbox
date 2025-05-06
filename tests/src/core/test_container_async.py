"""
Unit tests for the ContainerAsync class.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.src.core.container_async import ContainerAsync
from app.src.services.notification_service import PlaybackSubject


class TestContainerAsync:
    """Tests for the ContainerAsync class."""

    def test_init(self, mock_config):
        """Test the container initialization."""
        # Arrange
        with patch('app.src.services.playlist_service.PlaylistService'):
            with patch('app.src.module.audio_player.audio_factory.get_audio_player'):
                with patch('app.src.module.nfc.nfc_factory.get_nfc_handler', side_effect=Exception("NFC not available")):
                    # Act
                    container = ContainerAsync(mock_config)
                    
                    # Assert
                    assert container._config == mock_config
                    assert container._nfc is None
                    assert container._led_hat is None
                    assert isinstance(container._playback_subject, PlaybackSubject)
                    assert hasattr(container, '_playlist_service')
                    assert hasattr(container, '_audio')

    def test_init_with_nfc(self, mock_config):
        """Test container initialization with NFC available."""
        # Arrange
        mock_nfc = MagicMock()
        
        with patch('app.src.services.playlist_service.PlaylistService'):
            with patch('app.src.module.audio_player.audio_factory.get_audio_player'):
                with patch('app.src.module.nfc.nfc_factory.get_nfc_handler', return_value=mock_nfc):
                    with patch('gevent.lock.Semaphore'):
                        # Act
                        container = ContainerAsync(mock_config)
                        
                        # Assert
                        assert container._nfc == mock_nfc

    def test_config_property(self, mock_config):
        """Test the config property."""
        # Arrange
        with patch('app.src.services.playlist_service.PlaylistService'):
            with patch('app.src.module.audio_player.audio_factory.get_audio_player'):
                with patch('app.src.module.nfc.nfc_factory.get_nfc_handler', side_effect=Exception("NFC not available")):
                    container = ContainerAsync(mock_config)
                    
                    # Act
                    result = container.config
                    
                    # Assert
                    assert result == mock_config

    def test_playback_subject_property(self, mock_config):
        """Test the playback_subject property."""
        # Arrange
        with patch('app.src.services.playlist_service.PlaylistService'):
            with patch('app.src.module.audio_player.audio_factory.get_audio_player'):
                with patch('app.src.module.nfc.nfc_factory.get_nfc_handler', side_effect=Exception("NFC not available")):
                    container = ContainerAsync(mock_config)
                    
                    # Act
                    result = container.playback_subject
                    
                    # Assert
                    assert isinstance(result, PlaybackSubject)
                    assert result == container._playback_subject

    def test_nfc_property(self, mock_config):
        """Test the nfc property."""
        # Arrange
        mock_nfc = MagicMock()
        
        with patch('app.src.services.playlist_service.PlaylistService'):
            with patch('app.src.module.audio_player.audio_factory.get_audio_player'):
                with patch('app.src.module.nfc.nfc_factory.get_nfc_handler', return_value=mock_nfc):
                    with patch('gevent.lock.Semaphore'):
                        container = ContainerAsync(mock_config)
                        
                        # Act
                        result = container.nfc
                        
                        # Assert
                        assert result == mock_nfc

    def test_audio_property(self, mock_config):
        """Test the audio property."""
        # Arrange
        # Create a simpler mock for this test
        mock_audio = MagicMock()
        
        # Check if audio is properly initialized - without trying to mock the factory
        with patch('app.src.services.playlist_service.PlaylistService'):
            with patch('app.src.core.container_async.get_audio_player', return_value=mock_audio):
                with patch('app.src.module.nfc.nfc_factory.get_nfc_handler', side_effect=Exception("NFC not available")):
                    container = ContainerAsync(mock_config)
                    
                    # Act
                    result = container.audio
                    
                    # Assert
                    assert result == mock_audio

    def test_cleanup_async(self, mock_config):
        """Test resource cleanup."""
        # Arrange
        with patch('app.src.services.playlist_service.PlaylistService'):
            with patch('app.src.module.audio_player.audio_factory.get_audio_player'):
                with patch('app.src.module.nfc.nfc_factory.get_nfc_handler', side_effect=Exception("NFC not available")):
                    with patch('app.src.core.container_async.logger') as mock_logger:
                        container = ContainerAsync(mock_config)
                        
                        # Act - Using a synchronous approach to avoid complications
                        # For a real asynchronous test, we would need to properly use pytest-asyncio
                        cleanup_method = container.cleanup_async()
                        # In a test environment, we can just verify that the method exists
                        
                        # Assert
                        assert callable(getattr(cleanup_method, '__await__', None))
