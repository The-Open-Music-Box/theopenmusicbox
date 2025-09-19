# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Tests to verify playlist manager methods return proper boolean values."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from app.src.domain.audio.playlist.playlist_manager import PlaylistManager
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track


class TestPlaylistManagerReturnValues:
    """Tests to ensure playlist manager methods return correct boolean values."""

    def test_play_track_by_index_returns_success_true(self):
        """Test that _play_track_by_index returns True when backend succeeds."""
        # Create mock backend that succeeds
        mock_backend = Mock()
        mock_backend.play_file.return_value = True
        mock_backend.stop.return_value = True

        # Create playlist manager
        manager = PlaylistManager(mock_backend)

        # Create test playlist
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/test/path/test.mp3"
        )
        playlist = Playlist(
            name="Test Playlist",
            tracks=[track]
        )

        # Set the playlist
        manager.set_playlist(playlist)

        # Mock file existence check
        with patch.object(Path, 'exists', return_value=True):
            # Test the internal method directly
            result = manager._play_track_by_index(0)

            # This assertion would have caught the original bug
            assert result is True, "_play_track_by_index should return True when backend succeeds"
            mock_backend.play_file.assert_called_once()

    def test_play_track_by_index_returns_success_false(self):
        """Test that _play_track_by_index returns False when backend fails."""
        # Create mock backend that fails
        mock_backend = Mock()
        mock_backend.play_file.return_value = False
        mock_backend.stop.return_value = True

        # Create playlist manager
        manager = PlaylistManager(mock_backend)

        # Create test playlist
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/test/path/test.mp3"
        )
        playlist = Playlist(
            name="Test Playlist",
            tracks=[track]
        )

        # Set the playlist
        manager.set_playlist(playlist)

        # Mock file existence check
        with patch.object(Path, 'exists', return_value=True):
            # Test the internal method directly
            result = manager._play_track_by_index(0)

            # This should return False when backend fails
            assert result is False, "_play_track_by_index should return False when backend fails"
            mock_backend.play_file.assert_called_once()

    def test_set_playlist_success_depends_on_first_track_playback(self):
        """Test that set_playlist returns success/failure based on first track playback."""
        # Test with successful backend
        mock_backend_success = Mock()
        mock_backend_success.play_file.return_value = True
        mock_backend_success.stop.return_value = True

        manager_success = PlaylistManager(mock_backend_success)

        # Create test playlist
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/test/path/test.mp3"
        )
        playlist = Playlist(
            name="Test Playlist",
            tracks=[track]
        )

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(manager_success, '_start_monitoring'):
                result_success = manager_success.set_playlist(playlist)

                # Should return True when first track plays successfully
                assert result_success is True, "set_playlist should return True when first track plays"

        # Test with failing backend
        mock_backend_fail = Mock()
        mock_backend_fail.play_file.return_value = False
        mock_backend_fail.stop.return_value = True

        manager_fail = PlaylistManager(mock_backend_fail)

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(manager_fail, '_start_monitoring'):
                result_fail = manager_fail.set_playlist(playlist)

                # Should return False when first track fails to play
                assert result_fail is False, "set_playlist should return False when first track fails"

    def test_next_track_returns_boolean(self):
        """Test that next_track returns proper boolean values."""
        mock_backend = Mock()
        mock_backend.play_file.return_value = True
        mock_backend.stop.return_value = True

        manager = PlaylistManager(mock_backend)

        # Create test playlist with multiple tracks
        tracks = [
            Track(track_number=1, title="Track 1", filename="track1.mp3", file_path="/test/track1.mp3"),
            Track(track_number=2, title="Track 2", filename="track2.mp3", file_path="/test/track2.mp3")
        ]
        playlist = Playlist(name="Test Playlist", tracks=tracks)

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(manager, '_start_monitoring'):
                # Set playlist first
                manager.set_playlist(playlist)

                # Test next track (should succeed)
                result = manager.next_track()
                assert isinstance(result, bool), "next_track should return boolean"
                assert result is True, "next_track should return True when successful"

    def test_previous_track_returns_boolean(self):
        """Test that previous_track returns proper boolean values."""
        mock_backend = Mock()
        mock_backend.play_file.return_value = True
        mock_backend.stop.return_value = True

        manager = PlaylistManager(mock_backend)

        # Create test playlist with multiple tracks
        tracks = [
            Track(track_number=1, title="Track 1", filename="track1.mp3", file_path="/test/track1.mp3"),
            Track(track_number=2, title="Track 2", filename="track2.mp3", file_path="/test/track2.mp3")
        ]
        playlist = Playlist(name="Test Playlist", tracks=tracks)

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(manager, '_start_monitoring'):
                # Set playlist and move to second track
                manager.set_playlist(playlist)
                manager.next_track()

                # Test previous track (should succeed)
                result = manager.previous_track()
                assert isinstance(result, bool), "previous_track should return boolean"
                assert result is True, "previous_track should return True when successful"


class TestPlaylistManagerReturnValueConsistency:
    """Tests to ensure all methods that should return booleans actually do."""

    def test_all_playback_methods_return_booleans(self):
        """Test that all public playback methods return proper boolean types."""
        mock_backend = Mock()
        mock_backend.play_file.return_value = True
        mock_backend.pause.return_value = True
        mock_backend.resume.return_value = True
        mock_backend.stop.return_value = True

        manager = PlaylistManager(mock_backend)

        # Create test playlist
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/test/path/test.mp3"
        )
        playlist = Playlist(name="Test Playlist", tracks=[track])

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(manager, '_start_monitoring'):
                # Test set_playlist returns boolean
                result = manager.set_playlist(playlist)
                assert isinstance(result, bool), "set_playlist must return boolean"

                # Test pause returns boolean
                result = manager.pause()
                assert isinstance(result, bool), "pause must return boolean"

                # Test resume returns boolean
                result = manager.resume()
                assert isinstance(result, bool), "resume must return boolean"

                # Test stop returns boolean
                result = manager.stop()
                assert isinstance(result, bool), "stop must return boolean"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])