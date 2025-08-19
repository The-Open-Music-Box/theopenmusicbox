# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unit tests for TrackManagementService.

This module contains comprehensive unit tests for the TrackManagementService class,
testing track reordering, deletion, and management operations.
"""

import pytest
from unittest.mock import Mock, patch

from app.src.services.track_management_service import TrackManagementService


class TestTrackManagementService:
    """Test cases for TrackManagementService functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_config = Mock()
        self.mock_config.playlists_directory = "/test/playlists"
        
        self.mock_playlist_repository = Mock()
        self.mock_track_repository = Mock()
        
        with patch('app.src.services.track_management_service.get_playlist_repository') as mock_get_playlist_repo:
            mock_get_playlist_repo.return_value = self.mock_playlist_repository
            self.service = TrackManagementService(self.mock_config)

    def test_initialization(self):
        """Test TrackManagementService initialization."""
        assert self.service.config == self.mock_config
        assert self.service.repository == self.mock_playlist_repository

    def test_reorder_tracks_success(self):
        """Test successful track reordering."""
        playlist_id = 1
        new_order = [3, 1, 2]
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"},
            {"id": 3, "order": 3, "filename": "track3.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        self.mock_track_repository.update_order.return_value = True
        
        result = self.service.reorder_tracks(playlist_id, new_order)
        
        assert result is True
        self.mock_track_repository.update_order.assert_called()

    def test_reorder_tracks_playlist_not_found(self):
        """Test track reordering when playlist doesn't exist."""
        playlist_id = 999
        new_order = [1, 2, 3]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Playlist with ID 999 not found"):
            self.service.reorder_tracks(playlist_id, new_order)

    def test_reorder_tracks_invalid_track_ids(self):
        """Test track reordering with invalid track IDs."""
        playlist_id = 1
        new_order = [1, 2, 999]  # 999 doesn't exist
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        
        with pytest.raises(ValueError, match="Invalid track IDs in new order"):
            self.service.reorder_tracks(playlist_id, new_order)

    def test_delete_tracks_success(self):
        """Test successful track deletion."""
        playlist_id = 1
        track_numbers = [1, 3]
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"},
            {"id": 3, "order": 3, "filename": "track3.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        self.mock_playlist_repository.delete_tracks.return_value = True
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            result = self.service.delete_tracks(playlist_id, track_numbers)
            
            assert result is True
            assert self.mock_track_repository.delete.call_count == 2
            assert mock_remove.call_count == 2

    def test_delete_tracks_playlist_not_found(self):
        """Test track deletion when playlist doesn't exist."""
        playlist_id = 999
        track_numbers = [1, 2]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Playlist with ID 999 not found"):
            self.service.delete_tracks(playlist_id, track_numbers)

    def test_delete_tracks_invalid_numbers(self):
        """Test track deletion with invalid track numbers."""
        playlist_id = 1
        track_numbers = [1, 999]  # 999 is out of range
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        
        with pytest.raises(ValueError, match="Invalid track number: 999"):
            self.service.delete_tracks(playlist_id, track_numbers)

    def test_get_tracks_by_playlist_success(self):
        """Test successful retrieval of tracks by playlist."""
        playlist_id = 1
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"}
        ]
        
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        
        result = self.service.get_tracks_by_playlist(playlist_id)
        
        assert result == mock_tracks
        self.mock_playlist_repository.get_tracks_by_playlist.assert_called_once_with(playlist_id)

    def test_get_tracks_by_playlist_empty(self):
        """Test retrieval when playlist has no tracks."""
        playlist_id = 1
        
        self.mock_track_repository.get_by_playlist_id.return_value = []
        
        result = self.service.get_tracks_by_playlist(playlist_id)
        
        assert result == []
        self.mock_playlist_repository.get_tracks_by_playlist.assert_called_once_with(playlist_id)

    def test_get_track_count_success(self):
        """Test getting track count for a playlist."""
        playlist_id = 1
        mock_tracks = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        
        result = self.service.get_track_count(playlist_id)
        
        assert result == 3
        self.mock_playlist_repository.get_tracks_by_playlist.assert_called_once_with(playlist_id)

    def test_get_track_count_empty_playlist(self):
        """Test getting track count for empty playlist."""
        playlist_id = 1
        
        self.mock_track_repository.get_by_playlist_id.return_value = []
        
        result = self.service.get_track_count(playlist_id)
        
        assert result == 0
        self.mock_playlist_repository.get_tracks_by_playlist.assert_called_once_with(playlist_id)

    def test_validate_track_numbers_valid(self):
        """Test validation of valid track numbers."""
        track_numbers = [1, 2, 3]
        total_tracks = 5
        
        # Should not raise any exception
        self.service._validate_track_numbers(track_numbers, total_tracks)

    def test_validate_track_numbers_out_of_range(self):
        """Test validation with out-of-range track numbers."""
        track_numbers = [1, 2, 6]  # 6 is out of range
        total_tracks = 5
        
        with pytest.raises(ValueError, match="Invalid track number: 6"):
            self.service._validate_track_numbers(track_numbers, total_tracks)

    def test_validate_track_numbers_zero(self):
        """Test validation with zero track number."""
        track_numbers = [0, 1, 2]  # 0 is invalid
        total_tracks = 5
        
        with pytest.raises(ValueError, match="Invalid track number: 0"):
            self.service._validate_track_numbers(track_numbers, total_tracks)

    def test_validate_track_numbers_negative(self):
        """Test validation with negative track number."""
        track_numbers = [1, -1, 2]  # -1 is invalid
        total_tracks = 5
        
        with pytest.raises(ValueError, match="Invalid track number: -1"):
            self.service._validate_track_numbers(track_numbers, total_tracks)

    def test_move_track_up_success(self):
        """Test successful move track up operation."""
        playlist_id = 1
        track_number = 2
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"},
            {"id": 3, "order": 3, "filename": "track3.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        self.mock_track_repository.update_order.return_value = True
        
        result = self.service.move_track_up(playlist_id, track_number)
        
        assert result is True

    def test_move_track_up_first_track(self):
        """Test move up when track is already first."""
        playlist_id = 1
        track_number = 1  # Already first
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        
        result = self.service.move_track_up(playlist_id, track_number)
        
        assert result is False

    def test_move_track_down_success(self):
        """Test successful move track down operation."""
        playlist_id = 1
        track_number = 2
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"},
            {"id": 3, "order": 3, "filename": "track3.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        self.mock_track_repository.update_order.return_value = True
        
        result = self.service.move_track_down(playlist_id, track_number)
        
        assert result is True

    def test_move_track_down_last_track(self):
        """Test move down when track is already last."""
        playlist_id = 1
        track_number = 2  # Last track
        
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        mock_tracks = [
            {"id": 1, "order": 1, "filename": "track1.mp3"},
            {"id": 2, "order": 2, "filename": "track2.mp3"}
        ]
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        self.mock_playlist_repository.get_tracks_by_playlist.return_value = mock_tracks
        
        result = self.service.move_track_down(playlist_id, track_number)
        
        assert result is False
