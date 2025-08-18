# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unit tests for mock services.

This module tests the mock implementations to ensure they work correctly
for testing hardware dependencies.
"""

import pytest

from app.tests.mocks.mock_audio_service import MockAudioService
from app.tests.mocks.mock_controls_manager import MockControlsManager
from app.tests.mocks.mock_nfc_service import MockNfcService
from app.src.enums.control_event_type import ControlEventType


class TestMockAudioService:
    """Test cases for MockAudioService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = MockAudioService()

    def test_initialization(self):
        """Test mock audio service initialization."""
        assert self.service.is_available() is True
        assert self.service.is_playing() is False
        assert self.service.get_volume() == 50

    def test_play_pause_cycle(self):
        """Test play/pause functionality."""
        # Initially not playing
        assert self.service.is_playing() is False
        
        # Start playing
        result = self.service.play()
        assert result is True
        assert self.service.is_playing() is True
        
        # Pause
        result = self.service.pause()
        assert result is True
        assert self.service.is_playing() is False

    def test_volume_control(self):
        """Test volume control functionality."""
        # Set valid volume
        result = self.service.set_volume(75)
        assert result is True
        assert self.service.get_volume() == 75
        
        # Test invalid volume
        result = self.service.set_volume(150)
        assert result is False
        assert self.service.get_volume() == 75  # Unchanged

    def test_playlist_loading(self):
        """Test playlist loading functionality."""
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}]}
        result = self.service.load_playlist(playlist_data)
        assert result is True
        assert self.service.get_track_count() == 2

    def test_track_navigation(self):
        """Test track navigation."""
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}, {"id": 3}]}
        self.service.load_playlist(playlist_data)
        
        # Next track
        result = self.service.next_track()
        assert result is True
        assert self.service.get_current_track() == 1
        
        # Previous track
        result = self.service.previous_track()
        assert result is True
        assert self.service.get_current_track() == 0


class TestMockControlsManager:
    """Test cases for MockControlsManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MockControlsManager()

    def test_initialization(self):
        """Test mock controls manager initialization."""
        assert self.manager.is_initialized() is False
        assert self.manager.has_handlers() is False

    def test_initialization_cycle(self):
        """Test initialization and cleanup."""
        result = self.manager.initialize()
        assert result is True
        assert self.manager.is_initialized() is True
        
        self.manager.cleanup()
        assert self.manager.is_initialized() is False

    def test_event_subscription(self):
        """Test event subscription and handling."""
        handler_called = []
        
        def test_handler(event_type):
            handler_called.append(event_type)
        
        # Subscribe to event
        self.manager.subscribe_to_event(ControlEventType.PLAY_PAUSE, test_handler)
        assert self.manager.get_event_handler_count(ControlEventType.PLAY_PAUSE) == 1
        
        # Simulate event
        self.manager.simulate_play_pause()
        assert len(handler_called) == 1
        assert handler_called[0] == ControlEventType.PLAY_PAUSE

    def test_event_simulation(self):
        """Test event simulation methods."""
        self.manager.simulate_volume_up()
        self.manager.simulate_next_track()
        
        events = self.manager.get_simulated_events()
        assert ControlEventType.VOLUME_UP in events
        assert ControlEventType.NEXT_TRACK in events
        assert len(events) == 2


class TestMockNfcService:
    """Test cases for MockNfcService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = MockNfcService()

    def test_initialization(self):
        """Test mock NFC service initialization."""
        assert self.service.is_available() is True
        assert self.service.is_listening() is False
        assert self.service.get_tag_count() == 0

    def test_listening_cycle(self):
        """Test listening start/stop."""
        result = self.service.start_listening()
        assert result is True
        assert self.service.is_listening() is True
        
        result = self.service.stop_listening()
        assert result is True
        assert self.service.is_listening() is False

    def test_tag_simulation(self):
        """Test tag simulation."""
        self.service.simulate_tag_detection("test_tag_123", {"type": "test"})
        
        # Check tag was stored
        assert self.service.get_tag_count() == 1
        tag_info = self.service.get_tag_info("test_tag_123")
        assert tag_info is not None
        assert tag_info["tag_id"] == "test_tag_123"
        assert tag_info["type"] == "test"

    def test_playlist_tag_simulation(self):
        """Test playlist tag simulation."""
        self.service.simulate_playlist_tag("playlist_tag_456", 42)
        
        tag_info = self.service.get_tag_info("playlist_tag_456")
        assert tag_info["playlist_id"] == 42
        assert tag_info["type"] == "playlist"

    def test_tag_management(self):
        """Test tag management operations."""
        # Add tags
        self.service.simulate_tag_detection("tag1", {"data": "test1"})
        self.service.simulate_tag_detection("tag2", {"data": "test2"})
        assert self.service.get_tag_count() == 2
        
        # Remove tag
        result = self.service.remove_simulated_tag("tag1")
        assert result is True
        assert self.service.get_tag_count() == 1
        
        # Clear all tags
        self.service.clear_simulated_tags()
        assert self.service.get_tag_count() == 0
