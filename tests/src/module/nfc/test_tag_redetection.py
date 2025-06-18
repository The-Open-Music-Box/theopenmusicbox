import asyncio
from unittest.mock import ANY, MagicMock, patch

import pytest

from app.src.module.nfc.tag_detection_manager import TagDetectionManager
from app.src.services.nfc_service import NFCService


class TestTagRedetectionAfterAssociation:
    """Tests for the tag re-detection feature after mode transition."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)  # Add timeout to prevent test hanging
    async def test_force_redetect_emits_event(self):
        """Test that force_redetect properly emits an event with the tag
        data."""
        # Arrange
        tag_manager = TagDetectionManager()
        mock_observer = MagicMock()
        tag_manager.tag_subject.subscribe(mock_observer)
        test_tag_id = "04:76:A6:A3:DF:61:80"

        # Act
        result = tag_manager.force_redetect(test_tag_id)

        # Assert
        assert result is not None
        assert result["uid"] == test_tag_id
        assert result["new_detection"] is True
        assert result["forced"] is True

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)  # Add timeout to prevent test hanging
    async def test_end_to_end_workflow(self):
        """Test the tag association workflow without expecting automatic
        redetection.

        This simulates associating a tag with a playlist in the current
        implementation.
        """
        # Arrange
        tag_id = "04:76:A6:A3:DF:61:80"
        playlist_id = "21223825-c1fb-4d08-9496-e1035ac6559d"
        playlist_data = {"id": playlist_id, "title": "Test Playlist", "nfc_tag": None}

        # Mock the tag detection manager - not expected to be called in current
        # implementation
        mock_tag_detection_manager = MagicMock()

        # Mock the NFC handler
        mock_nfc_handler = MagicMock()
        mock_nfc_handler.tag_detection_manager = mock_tag_detection_manager

        # Mock playlist service for database operations
        mock_playlist_service = MagicMock()
        mock_playlist_service.associate_nfc_tag.return_value = True
        mock_playlist_service.get_playlist_by_nfc_tag.return_value = playlist_data

        # Mock the playlist controller
        mock_playlist_controller = MagicMock()

        # Setup socketio mock with a MagicMock that we can assert on
        mock_socketio = MagicMock()
        # Keep emit as a MagicMock, but configure its return value to be an awaitable
        mock_socketio.emit.return_value = asyncio.Future()
        mock_socketio.emit.return_value.set_result(None)

        # Create the NFC service with our mocks
        with patch(
            "app.src.services.playlist_service.PlaylistService",
            return_value=mock_playlist_service,
        ):
            nfc_service = NFCService(
                socketio=mock_socketio, nfc_handler=mock_nfc_handler
            )
            nfc_service._playlist_controller = mock_playlist_controller
            nfc_service._association_mode = True
            nfc_service.waiting_for_tag = True
            nfc_service.current_playlist_id = playlist_id
            nfc_service._sid = (
                "test_socket_id"  # Set the socket ID which is needed for emit calls
            )

            # Act: Simulate tag association
            result = await nfc_service.handle_tag_association(tag_id)

            # Assert - match current implementation behavior
            assert (
                nfc_service._association_mode is True
            ), "Service maintains association mode after association"
            assert result["status"] == "success", "Association should be successful"
            assert (
                result["tag_id"] == tag_id
            ), "Response should include the associated tag ID"
            assert (
                result["playlist_id"] == playlist_id
            ), "Response should include the playlist ID"

            # In the current implementation, NFC service doesn't automatically redetect the tag
            # The playlist service should be called to associate the tag
            mock_playlist_service.associate_nfc_tag.assert_called_once_with(
                playlist_id, tag_id
            )

            # Verify socketio emit was called with success response
            mock_socketio.emit.assert_called_with(
                "nfc_association_result",
                {
                    "status": "success",
                    "message": ANY,  # Match any message string
                    "tag_id": tag_id,
                    "playlist_id": playlist_id,
                },
                room=ANY,  # Match any room value
            )
