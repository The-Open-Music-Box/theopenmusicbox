import pytest
import asyncio
from unittest.mock import MagicMock, patch

from app.src.module.nfc.tag_detection_manager import TagDetectionManager
from app.src.services.nfc_service import NFCService


class TestTagRedetectionAfterAssociation:
    """Tests for the tag re-detection feature after mode transition."""
    
    @pytest.mark.asyncio
    async def test_force_redetect_emits_event(self):
        """Test that force_redetect properly emits an event with the tag data."""
        # Arrange
        tag_manager = TagDetectionManager()
        mock_observer = MagicMock()
        tag_manager.tag_subject.subscribe(mock_observer)
        test_tag_id = "04:76:A6:A3:DF:61:80"
        
        # Act
        result = tag_manager.force_redetect(test_tag_id)
        
        # Assert
        assert result is not None
        assert result['uid'] == test_tag_id
        assert result['new_detection'] is True
        assert result['forced'] is True
        mock_observer.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_mode_transition_triggers_redetection(self):
        """Test that transitioning from association to playback mode triggers tag re-detection."""
        # Arrange
        mock_tag_detection_manager = MagicMock()
        mock_tag_detection_manager.force_redetect.return_value = {
            'uid': '04:76:A6:A3:DF:61:80',
            'timestamp': 12345,
            'new_detection': True,
            'forced': True
        }
        
        mock_nfc_handler = MagicMock()
        mock_nfc_handler.tag_detection_manager = mock_tag_detection_manager
        
        mock_socketio = MagicMock()
        mock_socketio.emit = asyncio.coroutine(lambda *args, **kwargs: None)
        
        nfc_service = NFCService(socketio=mock_socketio, nfc_handler=mock_nfc_handler)
        nfc_service._association_mode = True
        nfc_service.waiting_for_tag = True
        nfc_service.current_playlist_id = "21223825-c1fb-4d08-9496-e1035ac6559d"
        
        # Create a mock playlist service for the association
        mock_playlist_service = MagicMock()
        mock_playlist_service.associate_nfc_tag.return_value = True
        
        # Patch the imports in the service
        with patch('app.src.services.nfc_service.PlaylistService', return_value=mock_playlist_service):
            # Act: Handle tag association which should trigger re-detection after successful association
            tag_id = '04:76:A6:A3:DF:61:80'
            result = await nfc_service.handle_tag_association(tag_id)
            
            # Allow for the small delay in the re-detection logic
            await asyncio.sleep(0.5)
            
            # Assert
            assert nfc_service._association_mode is False, "Service should exit association mode"
            assert nfc_service.waiting_for_tag is False, "Service should not be waiting for tag"
            mock_tag_detection_manager.force_redetect.assert_called_once_with(tag_id)
            
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """
        Test the complete workflow from tag association to playback without removing the tag.
        This simulates the real-world scenario where a user associates a tag and expects playback
        to start immediately without needing to remove and reapply the tag.
        """
        # Arrange
        tag_id = '04:76:A6:A3:DF:61:80'
        playlist_id = "21223825-c1fb-4d08-9496-e1035ac6559d"
        playlist_data = {
            "id": playlist_id,
            "title": "Test Playlist",
            "nfc_tag": None
        }
        
        # Mock the tag detection manager with a working force_redetect method
        mock_tag_detection_manager = MagicMock()
        mock_tag_detection_manager.force_redetect.return_value = {
            'uid': tag_id,
            'timestamp': 12345,
            'new_detection': True,
            'forced': True
        }
        
        # Mock the NFC handler
        mock_nfc_handler = MagicMock()
        mock_nfc_handler.tag_detection_manager = mock_tag_detection_manager
        
        # Mock playlist service for database operations
        mock_playlist_service = MagicMock()
        mock_playlist_service.associate_nfc_tag.return_value = True
        mock_playlist_service.get_playlist_by_nfc_tag.return_value = playlist_data
        
        # Mock the playlist controller to verify it receives the playback event
        mock_playlist_controller = MagicMock()
        
        # Setup socketio mock
        mock_socketio = MagicMock()
        mock_socketio.emit = asyncio.coroutine(lambda *args, **kwargs: None)
        
        # Create the NFC service with our mocks
        with patch('app.src.services.nfc_service.PlaylistService', return_value=mock_playlist_service):
            nfc_service = NFCService(socketio=mock_socketio, nfc_handler=mock_nfc_handler)
            nfc_service._playlist_controller = mock_playlist_controller
            nfc_service._association_mode = True
            nfc_service.waiting_for_tag = True
            nfc_service.current_playlist_id = playlist_id
            
            # Act: Simulate tag association
            result = await nfc_service.handle_tag_association(tag_id)
            
            # Allow for the small delay in the re-detection logic
            await asyncio.sleep(0.5)
            
            # Assert
            assert nfc_service._association_mode is False, "Service should exit association mode"
            assert result["status"] == "success", "Association should be successful"
            mock_tag_detection_manager.force_redetect.assert_called_once_with(tag_id)
            
            # Verify that playlist_controller.handle_tag_scanned was called 
            # with the right tag after re-detection
            mock_playlist_controller.handle_tag_scanned.assert_called_with(
                tag_id, {'new_detection': True, 'forced': True}
            )
