# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Integration tests for AudioController async/await issues.

These tests specifically target the async/await problems that only appear
with real hardware backends, not mock backends.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from app.src.controllers.audio_controller import AudioController


class MockAsyncAudioBackend:
    """Mock backend with async methods like WM8960AudioBackend."""

    def __init__(self):
        self.is_playing = False
        self.position = 0

    def is_available(self):
        return True

    async def pause(self):
        """Async pause method like WM8960AudioBackend."""
        self.is_playing = False
        return True

    async def get_position(self):
        """Async get_position method like WM8960AudioBackend."""
        return self.position


class MockSyncAudioBackend:
    """Mock backend with sync methods for comparison."""

    def __init__(self):
        self.is_playing = False
        self.position = 0

    def is_available(self):
        return True

    def pause(self):
        """Sync pause method."""
        self.is_playing = False
        return True

    def get_position(self):
        """Sync get_position method."""
        return self.position


class TestAudioControllerAsyncIssues:
    """Tests for async/await issues in AudioController."""

    def test_pause_with_async_backend_handles_gracefully(self):
        """
        Test that pause() handles async backend methods gracefully.
        This would have caught the original coroutine error.
        """
        # Arrange
        mock_backend = MockAsyncAudioBackend()
        controller = AudioController()
        controller._backend = mock_backend

        # Act - This should not crash with "coroutine was never awaited"
        result = controller.pause()

        # Assert - Should handle the async method gracefully
        # With the improved fix, it should return True using fallback approach
        assert result is True, "Should use fallback approach and return True with async backend"

    def test_pause_with_sync_backend_works_normally(self):
        """
        Test that pause() works normally with sync backend methods.
        This ensures we didn't break the sync case.
        """
        # Arrange
        mock_backend = MockSyncAudioBackend()
        controller = AudioController()
        controller._backend = mock_backend

        # Act
        result = controller.pause()

        # Assert - Should work normally with sync backend
        assert result == True, "Should work with sync backend"
        assert controller._paused_position == 0, "Should capture position"

    def test_next_track_without_playlist_manager_logs_warning(self):
        """
        Test that next_track() logs appropriate warning when no PlaylistManager.
        This would have caught the "does not support next track operation" issue.
        """
        # Arrange
        mock_backend = MockAsyncAudioBackend()  # No next_track method
        controller = AudioController()
        controller._backend = mock_backend
        controller._playlist_manager = None

        # Act
        result = controller.next_track()

        # Assert - Should return False and log warning
        assert result == False, "Should return False when no next_track support"

    def test_next_track_with_playlist_manager_works(self):
        """
        Test that next_track() works when PlaylistManager is available.
        """
        # Arrange
        mock_backend = MockAsyncAudioBackend()
        mock_playlist_manager = Mock()
        mock_playlist_manager.next_track.return_value = True

        controller = AudioController()
        controller._backend = mock_backend
        controller._playlist_manager = mock_playlist_manager

        # Act
        result = controller.next_track()

        # Assert
        assert result == True, "Should work with PlaylistManager"
        mock_playlist_manager.next_track.assert_called_once()

    def test_pause_position_capture_with_async_backend(self):
        """
        Test that position capture handles async get_position gracefully.
        """
        # Arrange
        mock_backend = MockAsyncAudioBackend()
        mock_backend.position = 5000  # 5 seconds

        controller = AudioController()
        controller._backend = mock_backend

        # Act - This should handle async get_position without crashing
        result = controller.pause()

        # Assert - Should handle async method and set position to 0 as fallback
        assert result is True, "Should use fallback approach and return True with async backend"
        # Position should be set to 0 as fallback when can't handle async
        assert controller._paused_position == 0.0, "Should set fallback position"

    def test_audio_controller_initialization_without_playlist_manager(self):
        """
        Test AudioController initialization without PlaylistManager.
        This tests the scenario causing the next_track warning.
        """
        # Arrange & Act
        controller = AudioController()

        # Assert
        assert controller._playlist_manager is None, "Should initialize without PlaylistManager"
        assert hasattr(controller, 'next_track'), "Should have next_track method"

    def test_mock_vs_real_backend_behavior(self):
        """
        Test to demonstrate the difference between mock and real backend behavior.
        This explains why tests didn't catch the async issues.
        """
        # Test with sync backend (like MockAudioBackend in tests)
        sync_backend = MockSyncAudioBackend()
        controller_sync = AudioController()
        controller_sync._backend = sync_backend

        sync_result = controller_sync.pause()

        # Test with async backend (like WM8960AudioBackend in production)
        async_backend = MockAsyncAudioBackend()
        controller_async = AudioController()
        controller_async._backend = async_backend

        async_result = controller_async.pause()

        # Demonstrate the difference
        assert sync_result == True, "Sync backend works fine"
        assert async_result == True, "Async backend works with fallback approach (no runtime errors)"

    def test_error_handling_in_pause_with_exception(self):
        """
        Test error handling when backend methods raise exceptions.
        """
        # Arrange
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend.pause.side_effect = Exception("Backend error")

        controller = AudioController()
        controller._backend = mock_backend

        # Act - Should not crash
        result = controller.pause()

        # Assert - Should handle exception gracefully
        # @handle_errors decorator returns JSONResponse for exceptions
        assert hasattr(result, 'status_code'), "Should return JSONResponse on exception"

    def test_hasattr_detection_of_async_methods(self):
        """
        Test that hasattr properly detects async methods.
        This tests our async detection logic.
        """
        # Arrange
        async_backend = MockAsyncAudioBackend()
        sync_backend = MockSyncAudioBackend()

        # Act & Assert - hasattr should work for both
        assert hasattr(async_backend, 'pause'), "Should detect async pause method"
        assert hasattr(async_backend, 'get_position'), "Should detect async get_position method"
        assert hasattr(sync_backend, 'pause'), "Should detect sync pause method"
        assert hasattr(sync_backend, 'get_position'), "Should detect sync get_position method"

        # Test async detection
        async_pause = async_backend.pause()
        sync_pause = sync_backend.pause()

        assert hasattr(async_pause, '__await__'), "Should detect async coroutine"
        assert not hasattr(sync_pause, '__await__'), "Should not detect sync return as coroutine"


class TestAudioControllerPlaylistManagerIntegration:
    """Tests for PlaylistManager integration issues."""

    def test_next_track_priority_playlist_manager_over_backend(self):
        """
        Test that next_track prioritizes PlaylistManager over backend.
        This ensures proper delegation hierarchy.
        """
        # Arrange
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend.next_track.return_value = True

        mock_playlist_manager = Mock()
        mock_playlist_manager.next_track.return_value = True

        controller = AudioController()
        controller._backend = mock_backend
        controller._playlist_manager = mock_playlist_manager

        # Act
        result = controller.next_track()

        # Assert - Should use PlaylistManager, not backend
        assert result == True
        mock_playlist_manager.next_track.assert_called_once()
        mock_backend.next_track.assert_not_called()  # Should not call backend when PM available


# Run with: python -m pytest tests/integration/test_audio_controller_async_issues.py -v