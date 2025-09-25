# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unit tests for AudioEngine class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.src.domain.audio.engine.audio_engine import AudioEngine
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track
from app.src.domain.protocols.state_manager_protocol import PlaybackState


class TestAudioEngine:
    """Test suite for AudioEngine class."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_backend = Mock()
        self.mock_event_bus = Mock()
        self.mock_state_manager = Mock()

        # Configure state manager to have required methods
        self.mock_state_manager.set_state = Mock()
        self.mock_state_manager.get_current_state = Mock(return_value=PlaybackState.STOPPED)
        self.mock_state_manager.update_playlist_info = Mock()
        self.mock_state_manager.update_track_info = Mock()

        # Create AudioEngine instance
        self.audio_engine = AudioEngine(
            backend=self.mock_backend,
            event_bus=self.mock_event_bus,
            state_manager=self.mock_state_manager
        )

        # Set engine as running
        self.audio_engine._is_running = True

    def test_set_playlist_success(self):
        """Test successful playlist setting with synchronous playback."""
        # Arrange
        track = Track(
            track_number=1,
            title="Test Song",
            filename="test.mp3",
            file_path="/path/to/test.mp3",
            duration_ms=180000
        )
        playlist = Playlist(name="Test Playlist", tracks=[track])

        # Mock successful backend playback
        self.mock_backend.play_file.return_value = True

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is True
        self.mock_backend.play_file.assert_called_once_with("/path/to/test.mp3")
        self.mock_state_manager.set_state.assert_called_with(PlaybackState.PLAYING)
        self.mock_state_manager.update_playlist_info.assert_called_once()
        self.mock_state_manager.update_track_info.assert_called_once()

    def test_set_playlist_engine_not_running(self):
        """Test set_playlist when engine is not running."""
        # Arrange
        track = Track(
            track_number=1,
            title="Test Song",
            filename="test.mp3",
            file_path="/path/to/test.mp3"
        )
        playlist = Playlist(name="Test Playlist", tracks=[track])

        # Set engine as not running
        self.audio_engine._is_running = False

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is False
        self.mock_backend.play_file.assert_not_called()

    def test_set_playlist_empty_playlist(self):
        """Test set_playlist with empty playlist."""
        # Arrange
        playlist = Playlist(name="Empty Playlist", tracks=[])

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is False
        self.mock_backend.play_file.assert_not_called()

    def test_set_playlist_no_valid_tracks(self):
        """Test set_playlist with no valid tracks."""
        # Arrange - track without file_path
        track = Track(
            track_number=1,
            title="Invalid Track",
            filename="invalid.mp3",
            file_path="",  # Empty file path
        )
        playlist = Playlist(name="Invalid Playlist", tracks=[track])

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is False
        self.mock_backend.play_file.assert_not_called()

    def test_set_playlist_backend_failure(self):
        """Test set_playlist when backend fails to play."""
        # Arrange
        track = Track(
            track_number=1,
            title="Test Song",
            filename="test.mp3",
            file_path="/path/to/test.mp3"
        )
        playlist = Playlist(name="Test Playlist", tracks=[track])

        # Mock backend failure
        self.mock_backend.play_file.return_value = False

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is False
        self.mock_backend.play_file.assert_called_once_with("/path/to/test.mp3")
        # State should not be updated on failure
        self.mock_state_manager.set_state.assert_not_called()

    def test_set_playlist_backend_exception(self):
        """Test set_playlist when backend raises exception."""
        # Arrange
        track = Track(
            track_number=1,
            title="Test Song",
            filename="test.mp3",
            file_path="/path/to/test.mp3"
        )
        playlist = Playlist(name="Test Playlist", tracks=[track])

        # Mock backend exception
        self.mock_backend.play_file.side_effect = Exception("Backend error")

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is False
        self.mock_backend.play_file.assert_called_once_with("/path/to/test.mp3")

    def test_set_playlist_multiple_tracks_plays_first_valid(self):
        """Test set_playlist with multiple tracks plays first valid track."""
        # Arrange
        invalid_track = Track(
            track_number=1,
            title="Invalid Track",
            filename="invalid.mp3",
            file_path="",  # Invalid - no file path
        )
        valid_track = Track(
            track_number=2,
            title="Valid Track",
            filename="valid.mp3",
            file_path="/path/to/valid.mp3"
        )
        playlist = Playlist(name="Mixed Playlist", tracks=[invalid_track, valid_track])

        # Mock successful backend playback
        self.mock_backend.play_file.return_value = True

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is True
        # Should play the first valid track (second in list)
        self.mock_backend.play_file.assert_called_once_with("/path/to/valid.mp3")

    def test_set_playlist_state_updates(self):
        """Test set_playlist properly updates state manager with playlist and track info."""
        # Arrange
        track = Track(
            track_number=1,
            title="Test Song",
            filename="test.mp3",
            file_path="/path/to/test.mp3",
            artist="Test Artist",
            album="Test Album"
        )
        playlist = Playlist(name="Test Playlist", tracks=[track])

        # Mock successful backend playback
        self.mock_backend.play_file.return_value = True

        # Act
        result = self.audio_engine.set_playlist(playlist)

        # Assert
        assert result is True

        # Verify state manager calls
        self.mock_state_manager.set_state.assert_called_with(PlaybackState.PLAYING)

        # Check playlist info update
        playlist_info_call = self.mock_state_manager.update_playlist_info.call_args[0][0]
        assert playlist_info_call["playlist_title"] == "Test Playlist"
        assert playlist_info_call["track_count"] == 1

        # Check track info update
        track_info_call = self.mock_state_manager.update_track_info.call_args[0][0]
        assert track_info_call["file_path"] == "/path/to/test.mp3"
        assert track_info_call["title"] == "Test Song"
        assert track_info_call["artist"] == "Test Artist"
        assert track_info_call["album"] == "Test Album"