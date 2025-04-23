# tests/src/core/test_application.py

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import os

from app.src.core.application import Application
from app.src.core.container import Container
from app.src.config import Config
from app.src.services.playlist_service import PlaylistService

class TestApplication(unittest.TestCase):
    def setUp(self):
        # Create mock container
        self.container_mock = Mock(spec=Container)

        # Create mock config with proper path attributes
        self.config_mock = Mock(spec=Config)
        self.config_mock.upload_folder = "/tmp/uploads"
        self.config_mock.db_file = "/tmp/test.db"
        self.container_mock.config = self.config_mock

        # Create mock playlist service
        self.playlist_service_mock = Mock(spec=PlaylistService)

        # Create mock audio player
        self.audio_player_mock = Mock()
        self.audio_player_mock.get_current_track = Mock(return_value=None)
        self.audio_player_mock.get_playlist = Mock(return_value=None)
        self.audio_player_mock.set_playlist = Mock()
        self.container_mock.audio = self.audio_player_mock

        # Create mock NFC reader
        self.nfc_mock = Mock()
        self.nfc_mock.tag_subject = Mock()
        self.nfc_mock.tag_subject.subscribe = Mock()
        self.container_mock.nfc = self.nfc_mock

        # Create mock LED hat
        self.led_hat_mock = Mock()
        self.led_hat_mock.start_animation = Mock()
        self.container_mock.led_hat = self.led_hat_mock

        # Create application instance
        self.application = Application(self.container_mock)

    def test_application_initialization(self):
        """Test that application initializes correctly"""
        self.assertIsNotNone(self.application)
        self.assertEqual(self.application._container, self.container_mock)
        self.assertEqual(self.application._config, self.config_mock)

    @patch('app.src.core.application.PlaylistService')
    def test_playlist_service_initialization(self, mock_playlist_service):
        """Test that playlist service is properly initialized"""
        mock_playlist_service.return_value = self.playlist_service_mock
        application = Application(self.container_mock)
        self.assertEqual(application._playlists, self.playlist_service_mock)
        mock_playlist_service.assert_called_once_with(self.config_mock)

    def test_setup_led(self):
        """Test LED setup"""
        self.application._setup_led()
        self.led_hat_mock.start_animation.assert_called_with('rotating_circle', color=(10, 50, 10))

    def test_setup_nfc(self):
        """Test NFC setup"""
        # Create a new mock for this test to avoid double initialization
        nfc_mock = Mock()
        nfc_mock.tag_subject = Mock()
        nfc_mock.tag_subject.subscribe = Mock()
        nfc_mock.start_nfc_reader = Mock()
        self.container_mock.nfc = nfc_mock

        self.application._setup_nfc()
        nfc_mock.start_nfc_reader.assert_called_once()
        nfc_mock.tag_subject.subscribe.assert_called_once()

    def test_setup_audio(self):
        """Test audio setup"""
        self.application._setup_audio()
        self.audio_player_mock.register_status_callback.assert_called()

    def test_cleanup(self):
        """Test application cleanup"""
        self.application.cleanup()
        self.container_mock.cleanup.assert_called_once()

    @patch('app.src.core.application.threading.Thread')
    def test_sync_playlists(self, mock_thread):
        """Test playlist synchronization"""
        # Mock the thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # Create new application to test sync
        application = Application(self.container_mock)

        # Verify that Thread was called with a sync_worker function
        mock_thread.assert_has_calls([
            call(target=mock_thread.call_args_list[0][1]['target']),
            call().start()
        ], any_order=True)

if __name__ == '__main__':
    unittest.main()