"""
Unit tests for the PlaylistController class.
"""
import pytest
from unittest.mock import MagicMock, patch
import time

from app.src.core.playlist_controller import PlaylistController


class TestPlaylistController:
    """Tests for the PlaylistController class."""

    def test_init(self, mock_audio_player, mock_playlist_service):
        """Test the controller initialization."""
        # Act
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        
        # Assert
        assert controller._audio == mock_audio_player
        assert controller._playlist_service == mock_playlist_service
        assert controller._current_tag is None
        assert controller._tag_last_seen == 0
        assert controller._pause_threshold > 0
        assert controller._monitor_thread is not None

    def test_handle_tag_scanned_new_tag(self, mock_audio_player, mock_playlist_service):
        """Test handling of a new NFC tag."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_tag_uid = "01:02:03:04"
        
        # Act
        controller.handle_tag_scanned(test_tag_uid)
        
        # Assert
        assert controller._current_tag == test_tag_uid
        mock_playlist_service.get_playlist_by_nfc_tag.assert_called_once_with(test_tag_uid)
        mock_playlist_service.play_playlist_with_validation.assert_called_once()

    def test_handle_tag_scanned_same_tag_paused(self, mock_audio_player, mock_playlist_service):
        """Test resuming playback for an already scanned tag that was paused."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_tag_uid = "01:02:03:04"
        
        # Simulate first scan
        controller.handle_tag_scanned(test_tag_uid)
        
        # Reset mocks for clean test
        mock_playlist_service.get_playlist_by_nfc_tag.reset_mock()
        mock_playlist_service.play_playlist_with_validation.reset_mock()
        
        # Set as paused
        mock_audio_player.is_playing = False
        
        # Act - scan same tag again
        controller.handle_tag_scanned(test_tag_uid)
        
        # Assert
        mock_audio_player.resume.assert_called_once()
        assert not mock_playlist_service.play_playlist_with_validation.called

    def test_handle_tag_scanned_finished_playlist(self, mock_audio_player, mock_playlist_service):
        """Test resuming with the same tag when the playlist has finished."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_tag_uid = "01:02:03:04"
        
        # Simulate first scan
        controller.handle_tag_scanned(test_tag_uid)
        
        # Reset mocks
        mock_playlist_service.get_playlist_by_nfc_tag.reset_mock()
        mock_playlist_service.play_playlist_with_validation.reset_mock()
        
        # Set as finished
        mock_audio_player.is_finished.return_value = True
        
        # Act - scan same tag again
        controller.handle_tag_scanned(test_tag_uid)
        
        # Assert
        mock_playlist_service.get_playlist_by_nfc_tag.assert_called_once_with(test_tag_uid)
        mock_playlist_service.play_playlist_with_validation.assert_called_once()

    def test_handle_tag_scanned_exception(self, mock_audio_player, mock_playlist_service):
        """Test exception handling when scanning a tag."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_tag_uid = "01:02:03:04"
        
        # Set up the mock to raise an exception
        mock_playlist_service.get_playlist_by_nfc_tag.side_effect = Exception("Test exception")
        
        # Act - This should not raise an exception
        controller.handle_tag_scanned(test_tag_uid)
        
        # Assert - The exception should have been caught internally
        assert controller._current_tag == test_tag_uid  # This should still be set

    def test_process_new_tag_found(self, mock_audio_player, mock_playlist_service):
        """Test processing a new tag with a found playlist."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_tag_uid = "01:02:03:04"
        test_playlist = {"id": "test_id", "title": "Test Playlist"}
        mock_playlist_service.get_playlist_by_nfc_tag.return_value = test_playlist
        
        # Act
        controller._process_new_tag(test_tag_uid)
        
        # Assert
        mock_playlist_service.get_playlist_by_nfc_tag.assert_called_once_with(test_tag_uid)
        mock_playlist_service.play_playlist_with_validation.assert_called_once_with(test_playlist, mock_audio_player)

    def test_process_new_tag_not_found(self, mock_audio_player, mock_playlist_service):
        """Test processing a new tag without an associated playlist."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_tag_uid = "01:02:03:04"
        mock_playlist_service.get_playlist_by_nfc_tag.return_value = None
        
        # Act
        controller._process_new_tag(test_tag_uid)
        
        # Assert
        mock_playlist_service.get_playlist_by_nfc_tag.assert_called_once_with(test_tag_uid)
        assert not mock_playlist_service.play_playlist_with_validation.called

    def test_play_playlist_success(self, mock_audio_player, mock_playlist_service):
        """Test successful playlist playback."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_playlist = {"id": "test_id", "title": "Test Playlist"}
        mock_playlist_service.play_playlist_with_validation.return_value = True
        
        # Act
        controller._play_playlist(test_playlist)
        
        # Assert
        mock_playlist_service.play_playlist_with_validation.assert_called_once_with(test_playlist, mock_audio_player)

    def test_play_playlist_failure(self, mock_audio_player, mock_playlist_service):
        """Test failed playlist playback."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_playlist = {"id": "test_id", "title": "Test Playlist"}
        mock_playlist_service.play_playlist_with_validation.return_value = False
        
        # Act - This should not raise an exception
        controller._play_playlist(test_playlist)
        
        # Assert
        mock_playlist_service.play_playlist_with_validation.assert_called_once_with(test_playlist, mock_audio_player)

    @patch('time.sleep', return_value=None)  # Patch sleep to speed up test
    def test_start_tag_monitor(self, mock_sleep, mock_audio_player, mock_playlist_service):
        """Test starting the tag monitoring thread."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        
        # Act - Thread is started in __init__, so just check it's there
        
        # Assert
        assert controller._monitor_thread is not None
        assert controller._monitor_thread.daemon is True
        assert controller._monitor_thread.is_alive()

    def test_update_playback_status_callback(self, mock_audio_player, mock_playlist_service, mock_track):
        """Test updating the playback counter when status changes."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        test_tag_uid = "01:02:03:04"
        controller._current_tag = test_tag_uid
        
        # Configure mock repository for update_track_counter
        mock_repository = MagicMock()
        mock_playlist_service.repository = mock_repository
        
        # Act
        controller.update_playback_status_callback(mock_track, "playing")
        
        # Assert
        mock_playlist_service.get_playlist_by_nfc_tag.assert_called_once_with(test_tag_uid)
        mock_repository.update_track_counter.assert_called_once_with(
            mock_playlist_service.get_playlist_by_nfc_tag.return_value["id"], 
            mock_track.number
        )

    def test_update_playback_status_callback_no_tag(self, mock_audio_player, mock_playlist_service, mock_track):
        """Test that nothing happens if there is no current tag."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        controller._current_tag = None
        
        # Configure mock repository for update_track_counter
        mock_repository = MagicMock()
        mock_playlist_service.repository = mock_repository
        
        # Act
        controller.update_playback_status_callback(mock_track, "playing")
        
        # Assert
        assert not mock_playlist_service.get_playlist_by_nfc_tag.called
        assert not mock_repository.update_track_counter.called

    def test_update_playback_status_callback_not_playing(self, mock_audio_player, mock_playlist_service, mock_track):
        """Test que rien ne se passe si le statut n'est pas 'playing'."""
        # Arrange
        controller = PlaylistController(mock_audio_player, mock_playlist_service)
        controller._current_tag = "01:02:03:04"
        
        # Configure mock repository for update_track_counter
        mock_repository = MagicMock()
        mock_playlist_service.repository = mock_repository
        
        # Act
        controller.update_playback_status_callback(mock_track, "paused")
        
        # Assert
        assert not mock_playlist_service.get_playlist_by_nfc_tag.called
        assert not mock_repository.update_track_counter.called
