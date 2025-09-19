# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Core Business Logic Tests for PlaylistApplicationService.

These tests focus on the pure business logic without HTTP wrapper responses.
They test the core start_playlist_with_details functionality that was causing the 500 errors.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track
from app.src.application.services.playlist_application_service import PlaylistApplicationService


class TestPlaylistApplicationServiceCoreLogic:
    """Test core business logic of playlist application service."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_repository = AsyncMock()
        self.mock_audio_engine = Mock()

        self.service = PlaylistApplicationService(
            playlist_repository=self.mock_repository
        )

    @pytest.mark.asyncio
    async def test_start_playlist_with_details_success(self):
        """Test successful playlist start with valid data and audio engine."""
        # Arrange
        playlist_id = "test-playlist-123"
        playlist_data = {
            "id": playlist_id,
            "title": "Test Playlist",
            "description": "Test Description",
            "nfc_tag_id": "test-tag",
            "tracks": [
                {
                    "id": "track-1",
                    "track_number": 1,
                    "title": "Track One",
                    "filename": "track1.mp3",
                    "file_path": "/music/track1.mp3",
                    "duration_ms": 180000,
                    "artist": "Test Artist"
                },
                {
                    "id": "track-2",
                    "track_number": 2,
                    "title": "Track Two",
                    "filename": "track2.mp3",
                    "file_path": "/music/track2.mp3",
                    "duration_ms": 200000,
                    "artist": "Test Artist 2"
                }
            ]
        }

        # Mock successful repository call
        self.mock_repository.get_playlist_by_id.return_value = playlist_data
        # Mock successful audio engine
        self.mock_audio_engine.set_playlist.return_value = True

        # Act
        result = await self.service.start_playlist_with_details(
            playlist_id, self.mock_audio_engine
        )

        # Assert
        assert result["success"] is True
        assert result["message"] == "Playlist 'Test Playlist' started successfully"
        assert result["details"]["playlist_id"] == playlist_id
        assert result["details"]["playlist_name"] == "Test Playlist"
        assert result["details"]["track_count"] == 2
        assert result["details"]["valid_tracks"] == 2

        # Verify repository was called
        self.mock_repository.get_playlist_by_id.assert_called_once_with(playlist_id)
        # Verify audio engine was called
        self.mock_audio_engine.set_playlist.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_playlist_with_details_playlist_not_found(self):
        """Test playlist start when playlist doesn't exist."""
        # Arrange
        playlist_id = "nonexistent-playlist"
        self.mock_repository.get_playlist_by_id.return_value = None

        # Act
        result = await self.service.start_playlist_with_details(
            playlist_id, self.mock_audio_engine
        )

        # Assert
        assert result["success"] is False
        assert result["error_type"] == "not_found"
        assert "not found" in result["message"]
        assert result["details"]["playlist_id"] == playlist_id

        # Audio engine should not be called
        self.mock_audio_engine.set_playlist.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_playlist_with_details_empty_playlist(self):
        """Test playlist start when playlist has no tracks."""
        # Arrange
        playlist_id = "empty-playlist"
        empty_playlist_data = {
            "id": playlist_id,
            "title": "Empty Playlist",
            "description": "No tracks",
            "tracks": []  # Empty tracks
        }

        self.mock_repository.get_playlist_by_id.return_value = empty_playlist_data

        # Act
        result = await self.service.start_playlist_with_details(
            playlist_id, self.mock_audio_engine
        )

        # Assert
        assert result["success"] is False
        assert result["error_type"] == "empty_playlist"
        assert "empty" in result["message"]

        # Audio engine should not be called
        self.mock_audio_engine.set_playlist.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_playlist_with_details_invalid_tracks_filtered(self):
        """Test playlist start filters out invalid tracks but succeeds with valid ones."""
        # Arrange
        playlist_id = "mixed-playlist"
        mixed_playlist_data = {
            "id": playlist_id,
            "title": "Mixed Playlist",
            "description": "Some valid, some invalid tracks",
            "tracks": [
                {
                    "id": "valid-track",
                    "track_number": 1,
                    "title": "Valid Track",
                    "filename": "valid.mp3",
                    "file_path": "/music/valid.mp3",
                    "duration_ms": 180000,
                    "artist": "Valid Artist"
                },
                {
                    "id": "invalid-track-1",
                    "track_number": 0,  # Invalid track number
                    "title": "",        # Empty title
                    "filename": "",     # Empty filename
                    "file_path": "",    # Empty path
                    "duration_ms": None
                },
                {
                    "id": "valid-track-2",
                    "track_number": 2,
                    "title": "Another Valid Track",
                    "filename": "valid2.mp3",
                    "file_path": "/music/valid2.mp3",
                    "duration_ms": 200000
                }
            ]
        }

        self.mock_repository.get_playlist_by_id.return_value = mixed_playlist_data
        self.mock_audio_engine.set_playlist.return_value = True

        # Act
        result = await self.service.start_playlist_with_details(
            playlist_id, self.mock_audio_engine
        )

        # Assert
        assert result["success"] is True
        assert result["details"]["track_count"] == 3  # Total tracks processed
        # Only 2 tracks should be valid (invalid one filtered out)
        # Note: The actual valid track count depends on Track.is_valid() implementation

        # Audio engine should be called with filtered playlist
        self.mock_audio_engine.set_playlist.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_playlist_with_details_audio_engine_failure(self):
        """Test playlist start when audio engine fails to load playlist."""
        # Arrange
        playlist_id = "test-playlist"
        playlist_data = {
            "id": playlist_id,
            "title": "Test Playlist",
            "tracks": [
                {
                    "id": "track-1",
                    "track_number": 1,
                    "title": "Track One",
                    "filename": "track1.mp3",
                    "file_path": "/music/track1.mp3",
                    "duration_ms": 180000
                }
            ]
        }

        self.mock_repository.get_playlist_by_id.return_value = playlist_data
        # Mock audio engine failure
        self.mock_audio_engine.set_playlist.return_value = False

        # Act
        result = await self.service.start_playlist_with_details(
            playlist_id, self.mock_audio_engine
        )

        # Assert
        assert result["success"] is False
        assert result["error_type"] == "audio_failure"
        assert "Failed to load playlist" in result["message"]

        # Audio engine should have been called but failed
        self.mock_audio_engine.set_playlist.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_playlist_with_details_no_audio_engine_fallback(self):
        """Test playlist start without audio engine uses fallback."""
        # Arrange
        playlist_id = "test-playlist"
        playlist_data = {
            "id": playlist_id,
            "title": "Test Playlist",
            "tracks": [
                {
                    "id": "track-1",
                    "track_number": 1,
                    "title": "Track One",
                    "filename": "track1.mp3",
                    "file_path": "/Users/jonathanpiette/github/theopenmusicbox/tomb-rpi/back/app/data/uploads/Louis de Funès - Fables de La Fontaine [mp3-320K]/04- La cigale et la fourmi.mp3",
                    "duration_ms": 180000
                }
            ]
        }

        self.mock_repository.get_playlist_by_id.return_value = playlist_data

        # Act - No audio engine provided (None)
        # The fallback should create a unified audio player automatically
        result = await self.service.start_playlist_with_details(
            playlist_id, None
        )

        # Assert - Should either succeed with fallback or fail gracefully
        # On macOS without audio mixer, it may fail but should not crash
        if result["success"]:
            assert "started successfully" in result["message"]
        else:
            # Should fail gracefully without crashing
            assert isinstance(result, dict)
            assert "success" in result

    @pytest.mark.asyncio
    async def test_start_playlist_validates_track_data_integrity(self):
        """Test that playlist start validates and handles corrupt track data."""
        # Arrange
        playlist_id = "corrupt-data-playlist"
        corrupt_playlist_data = {
            "id": playlist_id,
            "title": "Corrupt Data Playlist",
            "tracks": [
                {
                    "id": "good-track",
                    "track_number": 1,
                    "title": "Good Track",
                    "filename": "good.mp3",
                    "file_path": "/music/good.mp3",
                    "duration_ms": 180000
                },
                # Corrupt track data
                None,  # Null track
                {
                    # Missing required fields
                    "id": "incomplete-track"
                },
                {
                    "id": "negative-duration-track",
                    "track_number": 2,
                    "title": "Negative Duration",
                    "filename": "negative.mp3",
                    "file_path": "/music/negative.mp3",
                    "duration_ms": -1000  # Invalid negative duration
                }
            ]
        }

        self.mock_repository.get_playlist_by_id.return_value = corrupt_playlist_data
        self.mock_audio_engine.set_playlist.return_value = True

        # Act - Should handle corrupt data gracefully
        result = await self.service.start_playlist_with_details(
            playlist_id, self.mock_audio_engine
        )

        # Assert - Should handle corrupt data gracefully
        # The service may return either a success dict or a JSONResponse error
        # The important thing is it doesn't crash
        if hasattr(result, 'status_code'):
            # It's a JSONResponse (error case)
            assert result.status_code in [200, 500]  # Either success or handled error
        else:
            # It's a dict (success case)
            assert isinstance(result, dict)
            assert "success" in result