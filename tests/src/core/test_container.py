# tests/src/core/test_container.py

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os

from app.src.core.container import Container, EventPublisher
from app.src.config import Config
from app.src.services.notification_service import PlaybackSubject

class MockEventPublisher(EventPublisher):
    def __init__(self):
        self.events = []

    def publish_event(self, event_type: str, data: dict):
        self.events.append((event_type, data))

class TestContainer(unittest.TestCase):
    def setUp(self):
        # Create mock config with proper path attributes
        self.config_mock = Mock(spec=Config)
        self.config_mock.db_file = "/tmp/test.db"
        self.config_mock.upload_folder = "/tmp/uploads"

        # Create mock event publisher
        self.event_publisher = MockEventPublisher()

        # Set up mock handlers
        self.mock_gpio = Mock()
        self.mock_gpio.cleanup_all = Mock()

        self.mock_nfc = Mock()
        self.mock_nfc.cleanup = Mock()

        self.mock_audio = Mock()
        self.mock_audio.cleanup = Mock()
        self.mock_audio.get_current_track = Mock(return_value=None)
        self.mock_audio.get_playlist = Mock(return_value=None)
        self.mock_audio.set_playlist = Mock()

        self.mock_led = Mock()
        self.mock_led.cleanup = Mock()
        self.mock_led.clear = Mock()
        self.mock_led.start_animation = Mock()
        self.mock_led.stop_animation = Mock()

        # Create container instance with patched handlers
        with patch('app.src.core.container.get_gpio_controller', return_value=self.mock_gpio), \
             patch('app.src.core.container.get_nfc_handler', return_value=self.mock_nfc), \
             patch('app.src.core.container.get_audio_player', return_value=self.mock_audio), \
             patch('app.src.core.container.get_led_hat', return_value=self.mock_led):

            self.container = Container(self.config_mock, self.event_publisher)

            # Set up container resources for cleanup testing
            self.container._gpio = self.mock_gpio
            self.container._nfc = self.mock_nfc
            self.container._audio = self.mock_audio
            self.container._led_hat = self.mock_led

    def test_container_initialization(self):
        """Test that container initializes correctly with dependencies"""
        self.assertIsNotNone(self.container)
        self.assertEqual(self.container.config, self.config_mock)
        self.assertEqual(self.container.event_publisher, self.event_publisher)
        # Check if it's an instance of PlaybackSubject without checking the exact import path
        self.assertTrue('PlaybackSubject' in self.container.playback_subject.__class__.__name__)

    def test_gpio_property(self):
        """Test that GPIO property is properly initialized"""
        gpio = self.container.gpio
        self.assertEqual(gpio, self.mock_gpio)

    def test_nfc_property(self):
        """Test that NFC property is properly initialized"""
        nfc = self.container.nfc
        self.assertEqual(nfc, self.mock_nfc)

    def test_audio_property(self):
        """Test that audio player property is properly initialized"""
        audio = self.container.audio
        self.assertEqual(audio, self.mock_audio)

    def test_playlist_service_property(self):
        """Test that playlist service is properly initialized"""
        playlist_service = self.container.playlist_service
        self.assertIsNotNone(playlist_service)
        self.assertEqual(playlist_service.config, self.config_mock)

    def test_cleanup(self):
        """Test that cleanup properly closes all resources"""
        # Call cleanup
        self.container.cleanup()

        # Verify cleanup was called on all resources
        self.mock_gpio.cleanup_all.assert_called_once()
        self.mock_nfc.cleanup.assert_called_once()
        self.mock_audio.cleanup.assert_called_once()
        self.mock_led.cleanup.assert_called_once()

if __name__ == '__main__':
    unittest.main()