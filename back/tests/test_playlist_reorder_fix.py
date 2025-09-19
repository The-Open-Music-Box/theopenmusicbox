#!/usr/bin/env python3
"""
Test suite for playlist track reordering functionality.
Validates the complete DDD implementation of track reordering.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.src.domain.controllers.unified_controller import UnifiedPlaylistController
from app.src.domain.services.track_reordering_service import (
    TrackReorderingService,
    ReorderingStrategy,
    ReorderingCommand
)
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track


@pytest.mark.asyncio
async def test_update_track_numbers_method_exists():
    """Test that update_track_numbers method exists in repository adapter."""
    from app.src.infrastructure.adapters.pure_playlist_repository_adapter import (
        PurePlaylistRepositoryAdapter
    )

    adapter = PurePlaylistRepositoryAdapter()
    assert hasattr(adapter, 'update_track_numbers'), "update_track_numbers method should exist"
    assert callable(adapter.update_track_numbers), "update_track_numbers should be callable"


@pytest.mark.asyncio
async def test_reorder_tracks_with_valid_playlist():
    """Test reordering tracks in a playlist with tracks."""
    # Create test tracks
    tracks = [
        Track(track_number=1, title="Track 1", filename="track1.mp3", file_path="/music/track1.mp3", id="t1"),
        Track(track_number=2, title="Track 2", filename="track2.mp3", file_path="/music/track2.mp3", id="t2"),
        Track(track_number=3, title="Track 3", filename="track3.mp3", file_path="/music/track3.mp3", id="t3")
    ]

    # Create service and command
    service = TrackReorderingService()
    command = ReorderingCommand(
        playlist_id="test-playlist",
        strategy=ReorderingStrategy.BULK_REORDER,
        track_numbers=[3, 1, 2]  # New order
    )

    # Execute reordering
    result = service.execute_reordering(command, tracks)

    assert result.success == True
    assert len(result.affected_tracks) == 3
    assert result.affected_tracks[0].title == "Track 3"  # Was #3, now #1
    assert result.affected_tracks[1].title == "Track 1"  # Was #1, now #2
    assert result.affected_tracks[2].title == "Track 2"  # Was #2, now #3


@pytest.mark.asyncio
async def test_reorder_tracks_empty_playlist_validation():
    """Test that reordering an empty playlist fails with proper validation."""
    service = TrackReorderingService()
    command = ReorderingCommand(
        playlist_id="empty-playlist",
        strategy=ReorderingStrategy.BULK_REORDER,
        track_numbers=[]
    )

    # Execute with empty track list
    result = service.execute_reordering(command, [])

    assert result.success == False
    assert "Cannot reorder tracks in empty playlist" in result.validation_errors


@pytest.mark.asyncio
async def test_reorder_tracks_invalid_track_numbers():
    """Test validation of invalid track numbers."""
    tracks = [
        Track(track_number=1, title="Track 1", filename="track1.mp3", file_path="/music/track1.mp3"),
        Track(track_number=2, title="Track 2", filename="track2.mp3", file_path="/music/track2.mp3")
    ]

    service = TrackReorderingService()
    command = ReorderingCommand(
        playlist_id="test-playlist",
        strategy=ReorderingStrategy.BULK_REORDER,
        track_numbers=[1, 2, 5]  # Track 5 doesn't exist
    )

    result = service.execute_reordering(command, tracks)

    assert result.success == False
    assert any("do not exist" in error for error in result.validation_errors)


@pytest.mark.asyncio
async def test_controller_reorder_integration():
    """Test the complete reorder flow through the controller."""
    from app.src.dependencies import get_playlist_repository_adapter

    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.get_playlist_by_id = AsyncMock(return_value={
        "id": "test-playlist",
        "title": "Test Playlist",
        "tracks": [
            {"track_number": 1, "title": "Track 1", "filename": "track1.mp3",
             "file_path": "/music/track1.mp3", "id": "t1"},
            {"track_number": 2, "title": "Track 2", "filename": "track2.mp3",
             "file_path": "/music/track2.mp3", "id": "t2"}
        ]
    })
    mock_repo.update_track_numbers = MagicMock(return_value=True)

    # Patch the dependency
    import app.src.dependencies as deps
    original_get_repo = deps.get_playlist_repository_adapter
    deps.get_playlist_repository_adapter = lambda: mock_repo

    try:
        controller = UnifiedPlaylistController()
        result = await controller.reorder_tracks("test-playlist", [2, 1])

        assert result["status"] == "success"
        assert mock_repo.update_track_numbers.called

    finally:
        # Restore original
        deps.get_playlist_repository_adapter = original_get_repo


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])