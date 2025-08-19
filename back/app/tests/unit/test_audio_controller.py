# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unit tests for AudioController.

This module contains comprehensive unit tests for the AudioController class,
testing audio playback control, volume management, and state synchronization.
"""

import pytest
from unittest.mock import Mock, patch

from app.src.controllers.audio_controller import AudioController
from app.tests.mocks.mock_audio_service import MockAudioService


class TestAudioController:
    """Test cases for AudioController functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_audio_service = MockAudioService()
        
        self.audio_controller = AudioController(self.mock_audio_service)

    def test_initialization(self):
        """Test AudioController initialization."""
        assert self.audio_controller._audio_service == self.mock_audio_service
        assert self.audio_controller._config == self.mock_config
        assert self.audio_controller._current_volume == 50
        assert self.audio_controller._last_volume_change == 0

    def test_play_success(self):
        """Test successful play operation."""
        result = self.audio_controller.play()
        assert result is True
        assert self.mock_audio_service.is_playing() is True

    def test_play_unavailable_service(self):
        """Test play operation when audio service is unavailable."""
        self.mock_audio_service.set_availability(False)
        result = self.audio_controller.play()
        assert result is False

    def test_pause_success(self):
        """Test successful pause operation."""
        self.mock_audio_service.play()
        result = self.audio_controller.pause()
        assert result is True
        assert self.mock_audio_service.is_playing() is False

    def test_pause_unavailable_service(self):
        """Test pause operation when audio service is unavailable."""
        self.mock_audio_service.set_availability(False)
        result = self.audio_controller.pause()
        assert result is False

    def test_stop_success(self):
        """Test successful stop operation."""
        self.mock_audio_service.play()
        result = self.audio_controller.stop()
        assert result is True
        assert self.mock_audio_service.is_playing() is False

    def test_toggle_play_pause_when_playing(self):
        """Test toggle play/pause when currently playing."""
        self.mock_audio_service.play()
        result = self.audio_controller.toggle_play_pause()
        assert result is True
        assert self.mock_audio_service.is_playing() is False

    def test_toggle_play_pause_when_paused(self):
        """Test toggle play/pause when currently paused."""
        result = self.audio_controller.toggle_play_pause()
        assert result is True
        assert self.mock_audio_service.is_playing() is True

    def test_set_volume_valid_range(self):
        """Test setting volume within valid range."""
        result = self.audio_controller.set_volume(75)
        assert result is True
        assert self.audio_controller._current_volume == 75
        assert self.mock_audio_service.get_volume() == 75

    def test_set_volume_below_minimum(self):
        """Test setting volume below minimum."""
        result = self.audio_controller.set_volume(-10)
        assert result is False
        assert self.audio_controller._current_volume == 50  # Unchanged

    def test_set_volume_above_maximum(self):
        """Test setting volume above maximum."""
        result = self.audio_controller.set_volume(150)
        assert result is False
        assert self.audio_controller._current_volume == 50  # Unchanged

    def test_get_current_volume_sync(self):
        """Test getting current volume syncs with audio service."""
        # Change volume directly in audio service
        self.mock_audio_service.set_volume(80)
        
        # Get volume should sync the state
        volume = self.audio_controller.get_current_volume()
        assert volume == 80
        assert self.audio_controller._current_volume == 80

    @patch('time.time')
    def test_volume_up_with_debouncing(self, mock_time):
        """Test volume up with debouncing."""
        mock_time.return_value = 1000.0
        
        # First volume up should work
        result = self.audio_controller.volume_up()
        assert result is True
        assert self.audio_controller._current_volume == 55
        
        # Immediate second call should be debounced
        mock_time.return_value = 1000.1  # 100ms later
        result = self.audio_controller.volume_up()
        assert result is False
        assert self.audio_controller._current_volume == 55  # Unchanged

    @patch('time.time')
    def test_volume_down_with_debouncing(self, mock_time):
        """Test volume down with debouncing."""
        mock_time.return_value = 1000.0
        
        # First volume down should work
        result = self.audio_controller.volume_down()
        assert result is True
        assert self.audio_controller._current_volume == 45
        
        # Immediate second call should be debounced
        mock_time.return_value = 1000.1  # 100ms later
        result = self.audio_controller.volume_down()
        assert result is False
        assert self.audio_controller._current_volume == 45  # Unchanged

    def test_volume_up_at_maximum(self):
        """Test volume up when already at maximum."""
        self.audio_controller.set_volume(100)
        result = self.audio_controller.volume_up()
        assert result is False
        assert self.audio_controller._current_volume == 100

    def test_volume_down_at_minimum(self):
        """Test volume down when already at minimum."""
        self.audio_controller.set_volume(0)
        result = self.audio_controller.volume_down()
        assert result is False
        assert self.audio_controller._current_volume == 0

    def test_next_track_success(self):
        """Test successful next track operation."""
        # Load a playlist with multiple tracks
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}, {"id": 3}]}
        self.mock_audio_service.load_playlist(playlist_data)
        
        result = self.audio_controller.next_track()
        assert result is True

    def test_next_track_no_playlist(self):
        """Test next track when no playlist is loaded."""
        result = self.audio_controller.next_track()
        assert result is False

    def test_previous_track_success(self):
        """Test successful previous track operation."""
        # Load a playlist and advance to second track
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}, {"id": 3}]}
        self.mock_audio_service.load_playlist(playlist_data)
        self.mock_audio_service.next_track()
        
        result = self.audio_controller.previous_track()
        assert result is True

    def test_previous_track_no_playlist(self):
        """Test previous track when no playlist is loaded."""
        result = self.audio_controller.previous_track()
        assert result is False

    def test_play_track_success(self):
        """Test successful play track operation."""
        # Load a playlist
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}, {"id": 3}]}
        self.mock_audio_service.load_playlist(playlist_data)
        
        result = self.audio_controller.play_track(2)
        assert result is True

    def test_play_track_invalid_number(self):
        """Test play track with invalid track number."""
        # Load a playlist
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}, {"id": 3}]}
        self.mock_audio_service.load_playlist(playlist_data)
        
        result = self.audio_controller.play_track(5)
        assert result is False

    def test_load_playlist_success(self):
        """Test successful playlist loading."""
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}]}
        result = self.audio_controller.load_playlist(playlist_data)
        assert result is True

    def test_load_playlist_unavailable_service(self):
        """Test playlist loading when service is unavailable."""
        self.mock_audio_service.set_availability(False)
        playlist_data = {"tracks": [{"id": 1}, {"id": 2}]}
        result = self.audio_controller.load_playlist(playlist_data)
        assert result is False

    def test_is_playing(self):
        """Test is_playing status check."""
        assert self.audio_controller.is_playing() is False
        
        self.mock_audio_service.play()
        assert self.audio_controller.is_playing() is True

    def test_is_available(self):
        """Test is_available status check."""
        assert self.audio_controller.is_available() is True
        
        self.mock_audio_service.set_availability(False)
        assert self.audio_controller.is_available() is False
