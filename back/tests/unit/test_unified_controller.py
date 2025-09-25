"""Tests for UnifiedPlaylistController class."""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from app.src.application.controllers.unified_controller import UnifiedPlaylistController
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track


class TestUnifiedPlaylistController:
    """Test suite for UnifiedPlaylistController class."""

    @pytest.fixture
    def mock_audio_engine(self):
        """Mock audio engine."""
        mock = Mock()
        mock.start = AsyncMock(return_value=True)
        mock.stop = AsyncMock(return_value=True)
        mock.play_playlist = AsyncMock(return_value=True)
        mock.play_track = AsyncMock(return_value=True)
        mock.pause = AsyncMock(return_value=True)
        mock.resume = AsyncMock(return_value=True)
        mock.stop_playback = AsyncMock(return_value=True)
        mock.next_track = AsyncMock(return_value=True)
        mock.previous_track = AsyncMock(return_value=True)
        mock.set_volume = AsyncMock(return_value=True)
        mock.set_playlist = Mock(return_value=True)  # Synchronous method
        # Add _playlist_manager mock for set_playlist compatibility
        mock._playlist_manager = Mock()
        mock._playlist_manager.set_playlist = Mock(return_value=True)
        mock.get_state.return_value = {"is_playing": False, "volume": 50}
        return mock

    @pytest.fixture
    def mock_playlist_service(self):
        """Mock playlist service."""
        mock = Mock()
        mock.get_playlist_by_id = Mock()
        mock.get_all_playlists = Mock()
        mock.create_playlist = Mock()
        mock.update_playlist = Mock()
        mock.delete_playlist = Mock()
        return mock

    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager."""
        mock = Mock()
        mock.broadcast_state = Mock()
        mock.get_current_state = Mock(return_value={})
        mock.update_state = Mock()
        mock.emit_playback_state_changed = AsyncMock()  # Add missing async method
        return mock

    @pytest.fixture
    def mock_player_state_service(self):
        """Mock player state service."""
        mock = Mock()
        mock.get_current_playlist.return_value = None
        mock.get_current_track.return_value = None
        mock.get_current_track_index.return_value = 0
        mock.set_current_playlist = Mock()
        mock.set_current_track = Mock()
        return mock

    @pytest.fixture
    def mock_audio_controller(self):
        """Mock audio controller."""
        mock = Mock()
        mock.play = Mock(return_value=True)
        mock.pause = Mock(return_value=True)
        mock.stop = Mock(return_value=True)
        mock.set_volume = Mock(return_value=True)
        mock.is_playing = Mock(return_value=False)
        return mock

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {"audio": {"default_volume": 50}}

    @pytest.fixture
    def controller(
        self,
        mock_audio_engine,
        mock_playlist_service,
        mock_config,
        mock_state_manager,
        mock_player_state_service,
        mock_audio_controller,
    ):
        """Create UnifiedPlaylistController instance with mocked dependencies."""
        return UnifiedPlaylistController(
            audio_engine=mock_audio_engine,
            playlist_service=mock_playlist_service,
            config=mock_config,
            state_manager=mock_state_manager,
            player_state_service=mock_player_state_service,
            audio_controller=mock_audio_controller,
        )

    @pytest.fixture
    def sample_playlist(self):
        """Sample playlist for testing."""
        track1 = Track(
            track_number=1,
            title="Track 1",
            filename="track1.mp3",
            file_path="/test/track1.mp3",
            id="track1",
            artist="Artist 1",
            duration_ms=180000  # Convert seconds to milliseconds
        )
        track2 = Track(
            track_number=2,
            title="Track 2",
            filename="track2.mp3",
            file_path="/test/track2.mp3",
            id="track2",
            artist="Artist 2",
            duration_ms=200000  # Convert seconds to milliseconds
        )
        return Playlist(
            id="test_playlist",
            name="Test Playlist",
            description="A test playlist",
            tracks=[track1, track2]
        )

    def test_init(self, mock_audio_engine, mock_playlist_service, mock_config, mock_state_manager):
        """Test UnifiedPlaylistController initialization."""
        controller = UnifiedPlaylistController(
            audio_engine=mock_audio_engine,
            playlist_service=mock_playlist_service,
            config=mock_config,
            state_manager=mock_state_manager,
        )

        assert controller._audio_engine == mock_audio_engine
        assert controller._playlist_service == mock_playlist_service
        assert controller._config == mock_config
        assert controller._state_manager == mock_state_manager

    def test_init_minimal(self):
        """Test UnifiedPlaylistController initialization with minimal parameters."""
        controller = UnifiedPlaylistController()

        assert controller._audio_engine is None
        assert controller._playlist_service is None
        assert controller._config is None
        assert controller._state_manager is None

    @patch('app.src.application.controllers.unified_controller.audio_domain_container')
    def test_ensure_initialized_with_container(self, mock_container, controller):
        """Test ensure_initialized method using container when no audio engine."""
        controller._audio_engine = None
        mock_audio_engine = Mock()

        # Configure container properties (not methods)
        mock_container.is_initialized = True
        mock_container.audio_engine = mock_audio_engine

        controller.ensure_initialized()

        assert controller._audio_engine == mock_audio_engine

    def test_ensure_initialized_with_existing_engine(self, controller, mock_audio_engine):
        """Test ensure_initialized method when audio engine already exists."""
        controller._audio_engine = mock_audio_engine

        controller.ensure_initialized()

        assert controller._audio_engine == mock_audio_engine

    @pytest.mark.asyncio
    async def test_start(self, controller, mock_audio_engine):
        """Test start method."""
        await controller.start()

        mock_audio_engine.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self, controller, mock_audio_engine):
        """Test stop method."""
        await controller.stop()

        mock_audio_engine.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_play_playlist_from_nfc_success(self, controller, mock_playlist_service, sample_playlist):
        """Test play_playlist_from_nfc with successful NFC tag association."""
        nfc_tag_uid = "test_nfc_uid"
        mock_playlist_service.get_playlist_by_nfc_tag = AsyncMock(return_value=sample_playlist)

        result = await controller.play_playlist_from_nfc(nfc_tag_uid)

        assert result is True
        mock_playlist_service.get_playlist_by_nfc_tag.assert_called_once_with(nfc_tag_uid)

    @pytest.mark.asyncio
    async def test_play_playlist_from_nfc_not_found(self, controller, mock_playlist_service):
        """Test play_playlist_from_nfc when NFC tag is not associated."""
        nfc_tag_uid = "unknown_nfc_uid"
        mock_playlist_service.get_playlist_by_nfc_tag = AsyncMock(return_value=None)

        result = await controller.play_playlist_from_nfc(nfc_tag_uid)

        assert result is False

    def test_register_playback_callback(self, controller):
        """Test register_playback_callback method."""
        callback = Mock()

        controller.register_playback_callback(callback)

        assert callback in controller._playback_callbacks

    @pytest.mark.asyncio
    async def test_load_playlist(self, controller, sample_playlist, mock_player_state_service):
        """Test load_playlist method."""
        result = await controller.load_playlist(sample_playlist)

        assert result is True
        mock_player_state_service.set_current_playlist.assert_called_once_with(sample_playlist)

    @pytest.mark.asyncio
    async def test_play_playlist(self, controller, sample_playlist, mock_audio_engine):
        """Test play_playlist method."""
        result = await controller.play_playlist(sample_playlist, track_index=1)

        assert result is True
        mock_audio_engine.play_playlist.assert_called_once_with(sample_playlist, track_index=1)

    @pytest.mark.asyncio
    async def test_play_playlist_default_index(self, controller, sample_playlist, mock_audio_engine):
        """Test play_playlist method with default track index."""
        result = await controller.play_playlist(sample_playlist)

        assert result is True
        mock_audio_engine.play_playlist.assert_called_once_with(sample_playlist, track_index=0)

    def test_set_playlist(self, controller, sample_playlist, mock_audio_engine):
        """Test set_playlist method."""
        result = controller.set_playlist(sample_playlist)

        assert result is True
        # Check that audio engine's playlist manager was called
        mock_audio_engine._playlist_manager.set_playlist.assert_called_once_with(sample_playlist)

    @pytest.mark.asyncio
    async def test_play_track_by_index_success(self, controller, mock_audio_engine, mock_player_state_service, sample_playlist):
        """Test play_track_by_index with valid index."""
        mock_player_state_service.get_current_playlist.return_value = sample_playlist

        result = await controller.play_track_by_index(1)

        assert result is True
        mock_audio_engine.play_track.assert_called_once_with(sample_playlist.tracks[1])
        mock_player_state_service.set_current_track.assert_called_once_with(sample_playlist.tracks[1])

    @pytest.mark.asyncio
    async def test_play_track_by_index_no_playlist(self, controller, mock_player_state_service):
        """Test play_track_by_index when no playlist is loaded."""
        mock_player_state_service.get_current_playlist.return_value = None

        result = await controller.play_track_by_index(0)

        assert result is False

    @pytest.mark.asyncio
    async def test_play_track_by_index_invalid_index(self, controller, mock_player_state_service, sample_playlist):
        """Test play_track_by_index with invalid index."""
        mock_player_state_service.get_current_playlist.return_value = sample_playlist

        result = await controller.play_track_by_index(10)  # Invalid index

        assert result is False

    @pytest.mark.asyncio
    async def test_next_track(self, controller, mock_audio_engine):
        """Test next_track method."""
        result = await controller.next_track()

        assert result is True
        mock_audio_engine.next_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_previous_track(self, controller, mock_audio_engine):
        """Test previous_track method."""
        result = await controller.previous_track()

        assert result is True
        mock_audio_engine.previous_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause(self, controller, mock_audio_engine):
        """Test pause method."""
        result = await controller.pause()

        assert result is True
        mock_audio_engine.pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume(self, controller, mock_audio_engine):
        """Test resume method."""
        result = await controller.resume()

        assert result is True
        mock_audio_engine.resume.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self, controller, mock_audio_engine):
        """Test stop method."""
        result = await controller.stop()

        assert result is True
        mock_audio_engine.stop_playback.assert_called_once()

    def test_toggle_playback_when_playing(self, controller, mock_audio_engine):
        """Test toggle_playback when currently playing."""
        mock_state = {"is_playing": True}
        mock_audio_engine.get_state.return_value = mock_state

        result = controller.toggle_playback()

        assert result is True

    def test_toggle_playback_when_not_playing(self, controller, mock_audio_engine):
        """Test toggle_playback when not currently playing."""
        mock_state = {"is_playing": False}
        mock_audio_engine.get_state.return_value = mock_state

        result = controller.toggle_playback()

        assert result is True

    def test_next_track_sync(self, controller, mock_audio_engine):
        """Test next_track_sync method."""
        result = controller.next_track_sync()

        assert result is True

    def test_previous_track_sync(self, controller, mock_audio_engine):
        """Test previous_track_sync method."""
        result = controller.previous_track_sync()

        assert result is True

    @pytest.mark.asyncio
    async def test_set_volume(self, controller, mock_audio_engine):
        """Test set_volume method."""
        volume = 75

        result = await controller.set_volume(volume)

        assert result is True
        mock_audio_engine.set_volume.assert_called_once_with(volume)

    @pytest.mark.asyncio
    async def test_set_volume_bounds(self, controller, mock_audio_engine):
        """Test set_volume with boundary values."""
        # Test minimum volume
        result = await controller.set_volume(0)
        assert result is True
        mock_audio_engine.set_volume.assert_called_with(0)

        # Test maximum volume
        result = await controller.set_volume(100)
        assert result is True
        mock_audio_engine.set_volume.assert_called_with(100)

    def test_get_state(self, controller, mock_audio_engine):
        """Test get_state method."""
        expected_state = {"is_playing": True, "volume": 75, "current_track": "track1"}
        mock_audio_engine.get_state.return_value = expected_state

        result = controller.get_state()

        assert result == expected_state
        mock_audio_engine.get_state.assert_called_once()

    def test_get_state_no_audio_engine(self, controller):
        """Test get_state when no audio engine is available."""
        controller._audio_engine = None

        result = controller.get_state()

        assert result == {}

    @pytest.mark.asyncio
    async def test_exception_handling_in_async_methods(self, controller, mock_audio_engine):
        """Test exception handling in async methods."""
        mock_audio_engine.play_playlist.side_effect = Exception("Test exception")

        # Should not raise exception, but return False
        result = await controller.play_playlist(Mock())

        assert result is False

    def test_multiple_callback_registration(self, controller):
        """Test registering multiple playback callbacks."""
        callback1 = Mock()
        callback2 = Mock()

        controller.register_playback_callback(callback1)
        controller.register_playback_callback(callback2)

        assert callback1 in controller._playback_callbacks
        assert callback2 in controller._playback_callbacks
        assert len(controller._playback_callbacks) == 2

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, controller, mock_audio_engine, sample_playlist):
        """Test concurrent operations on the controller."""
        # Simulate concurrent calls
        tasks = [
            controller.play_playlist(sample_playlist),
            controller.set_volume(50),
            controller.pause(),
            controller.resume(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should complete without exceptions
        for result in results:
            assert not isinstance(result, Exception)

    def test_state_consistency(self, controller, mock_player_state_service, sample_playlist):
        """Test that state remains consistent across operations."""
        # Set playlist
        controller.set_playlist(sample_playlist)

        # Verify state
        mock_player_state_service.set_current_playlist.assert_called_once_with(sample_playlist)

        # Get state should reflect current state
        state = controller.get_state()
        assert isinstance(state, dict)

    @pytest.mark.asyncio
    async def test_error_recovery(self, controller, mock_audio_engine):
        """Test error recovery in async operations."""
        # First call fails
        mock_audio_engine.pause.side_effect = [Exception("Network error"), True]

        # First call should handle exception
        result1 = await controller.pause()
        assert result1 is False

        # Reset side effect for successful call
        mock_audio_engine.pause.side_effect = None
        mock_audio_engine.pause.return_value = True

        # Second call should succeed
        result2 = await controller.pause()
        assert result2 is True

    def test_legacy_compatibility(self, controller, mock_playlist_service, mock_audio_controller):
        """Test compatibility with legacy components."""
        # Controller should work with legacy playlist service
        assert controller._playlist_service == mock_playlist_service

        # Controller should work with legacy audio controller
        assert controller._audio_controller == mock_audio_controller

        # Legacy state should be accessible
        state = controller.get_state()
        assert isinstance(state, dict)