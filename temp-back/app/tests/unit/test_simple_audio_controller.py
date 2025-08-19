# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Simple unit tests for AudioController.

This module contains basic unit tests for the AudioController class
that work with the current implementation.
"""

import pytest
from unittest.mock import Mock

from app.src.controllers.audio_controller import AudioController


class TestSimpleAudioController:
    """Simple test cases for AudioController functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_audio_service = Mock()
        self.mock_audio_service.is_playing = False
        
        self.audio_controller = AudioController(self.mock_audio_service)

    def test_initialization(self):
        """Test AudioController initialization."""
        assert self.audio_controller._audio_service == self.mock_audio_service
        assert hasattr(self.audio_controller, '_current_volume')
        assert hasattr(self.audio_controller, '_last_pause_toggle_time')

    def test_set_audio_service(self):
        """Test setting audio service."""
        new_service = Mock()
        new_service._volume = 75
        
        self.audio_controller.set_audio_service(new_service)
        
        assert self.audio_controller._audio_service == new_service
        assert self.audio_controller._current_volume == 75

    def test_get_audio_service(self):
        """Test getting audio service."""
        result = self.audio_controller.get_audio_service()
        assert result == self.mock_audio_service

    def test_is_audio_available_true(self):
        """Test audio availability check when service is available."""
        result = self.audio_controller.is_audio_available()
        assert result is True

    def test_is_audio_available_false(self):
        """Test audio availability check when service is not available."""
        self.audio_controller.set_audio_service(None)
        result = self.audio_controller.is_audio_available()
        assert result is False

    def test_toggle_playback_no_service(self):
        """Test toggle playback when no audio service is available."""
        self.audio_controller.set_audio_service(None)
        result = self.audio_controller.toggle_playback()
        assert result is False

    def test_initialization_without_service(self):
        """Test AudioController initialization without service."""
        controller = AudioController()
        assert controller._audio_service is None
        assert hasattr(controller, '_current_volume')
        assert hasattr(controller, '_last_pause_toggle_time')
