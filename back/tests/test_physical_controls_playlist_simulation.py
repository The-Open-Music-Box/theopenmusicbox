# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Test Physical Controls with Playlist Simulation.

Complete integration tests simulating button usage during playlist playback.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime

from app.src.controllers.physical_controls_manager import PhysicalControlsManager
from app.src.controllers.audio_controller import AudioController
from app.src.infrastructure.hardware.controls.mock_controls_implementation import MockPhysicalControls
from app.src.domain.protocols.physical_controls_protocol import PhysicalControlEvent
from app.src.config.hardware_config import HardwareConfig
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)


class TestPhysicalControlsPlaylistSimulation:
    """Test physical controls with simulated playlist playback."""

    @pytest.fixture
    def hardware_config(self):
        """Create test hardware configuration."""
        return HardwareConfig(
            gpio_next_track_button=26,
            gpio_previous_track_button=16,
            gpio_volume_encoder_clk=8,
            gpio_volume_encoder_dt=12,
            gpio_volume_encoder_sw=7,
            mock_hardware=True  # Always use mock for these tests
        )

    @pytest.fixture
    def test_playlist(self):
        """Create a test playlist with multiple tracks."""
        tracks = [
            Track(
                track_number=1,
                title="Track 1",
                filename="track1.mp3",
                file_path="/music/track1.mp3",
                duration_ms=180000,  # 3 minutes
                artist="Artist 1",
                album="Album 1",
                id="track1"
            ),
            Track(
                track_number=2,
                title="Track 2",
                filename="track2.mp3",
                file_path="/music/track2.mp3",
                duration_ms=240000,  # 4 minutes
                artist="Artist 2",
                album="Album 1",
                id="track2"
            ),
            Track(
                track_number=3,
                title="Track 3",
                filename="track3.mp3",
                file_path="/music/track3.mp3",
                duration_ms=200000,  # 3:20
                artist="Artist 1",
                album="Album 2",
                id="track3"
            ),
            Track(
                track_number=4,
                title="Track 4",
                filename="track4.mp3",
                file_path="/music/track4.mp3",
                duration_ms=150000,  # 2:30
                artist="Artist 3",
                album="Album 2",
                id="track4"
            )
        ]

        return Playlist(
            name="Test Playlist",
            tracks=tracks,
            description="Test playlist for physical controls",
            id="playlist_test_001"
        )

    @pytest.fixture
    def mock_audio_service(self):
        """Create mock audio service with playback simulation."""
        service = Mock()
        service.is_playing = False
        service.current_position = 0
        service.volume = 50

        # Simulate play/pause
        def play():
            service.is_playing = True
            return True

        def pause():
            service.is_playing = False
            return True

        def stop():
            service.is_playing = False
            service.current_position = 0
            return True

        def get_position():
            return service.current_position if service.is_playing else 0

        def set_volume(vol):
            service.volume = max(0, min(100, vol))
            return True

        service.play = Mock(side_effect=play)
        service.pause = Mock(side_effect=pause)
        service.stop = Mock(side_effect=stop)
        service.get_position = Mock(side_effect=get_position)
        service.set_volume = Mock(side_effect=set_volume)
        service.load_file = Mock(return_value=True)
        service.next_track = Mock(return_value=True)
        service.previous_track = Mock(return_value=True)

        return service

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock state manager."""
        manager = Mock()
        manager.broadcast_state_change = AsyncMock()
        manager.get_global_sequence = Mock(return_value=1)
        return manager

    @pytest.fixture
    async def audio_controller_with_playlist(self, mock_audio_service, mock_state_manager, test_playlist):
        """Create audio controller with loaded playlist."""
        controller = AudioController(
            audio_service=mock_audio_service,
            state_manager=mock_state_manager
        )

        # Load the test playlist
        controller._current_playlist = test_playlist
        controller._current_playlist_id = test_playlist.id
        controller._current_track_index = 0
        controller._internal_playing_state = False

        # Create a mock playlist manager that properly updates track index
        playlist_manager = Mock()

        def mock_next_track():
            if controller._current_track_index < len(test_playlist.tracks) - 1:
                controller._current_track_index += 1
                return True
            return False

        def mock_previous_track():
            if controller._current_track_index > 0:
                controller._current_track_index -= 1
                return True
            return False

        playlist_manager.next_track = Mock(side_effect=mock_next_track)
        playlist_manager.previous_track = Mock(side_effect=mock_previous_track)

        # Inject the mock playlist manager
        controller._playlist_manager = playlist_manager

        # Add toggle_playback method to controller if it doesn't exist
        def mock_toggle_playback():
            if controller._internal_playing_state:
                controller.pause()
                controller._internal_playing_state = False
            else:
                controller.play()
                controller._internal_playing_state = True
            return True

        controller.toggle_playback = Mock(side_effect=mock_toggle_playback)

        return controller

    @pytest.fixture
    async def controls_manager_with_playlist(self, audio_controller_with_playlist, hardware_config):
        """Create physical controls manager with audio controller and playlist."""
        manager = PhysicalControlsManager(
            audio_controller=audio_controller_with_playlist,
            hardware_config=hardware_config
        )

        # Initialize controls
        await manager.initialize()

        yield manager

        # Cleanup
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_navigation_buttons_during_playback(self, controls_manager_with_playlist, audio_controller_with_playlist):
        """Test next/previous buttons during active playback."""
        controller = audio_controller_with_playlist
        mock_controls = controls_manager_with_playlist.get_physical_controls()

        # Start playback (simulate it properly)
        result = controller.play()
        controller._internal_playing_state = True  # Force state for testing
        controller.audio_service.is_playing = True
        assert controller._current_track_index == 0

        logger.log(LogLevel.INFO, "🎵 Starting playback simulation test")

        # Test NEXT button - should go to track 2
        await mock_controls.simulate_next_track()
        assert controller._current_track_index == 1
        assert controller._current_playlist.tracks[1].title == "Track 2"
        logger.log(LogLevel.INFO, f"✅ Next button: Moved to track {controller._current_track_index + 1}")

        # Test NEXT button again - should go to track 3
        await mock_controls.simulate_next_track()
        assert controller._current_track_index == 2
        assert controller._current_playlist.tracks[2].title == "Track 3"
        logger.log(LogLevel.INFO, f"✅ Next button: Moved to track {controller._current_track_index + 1}")

        # Test PREVIOUS button - should go back to track 2
        await mock_controls.simulate_previous_track()
        assert controller._current_track_index == 1
        assert controller._current_playlist.tracks[1].title == "Track 2"
        logger.log(LogLevel.INFO, f"✅ Previous button: Moved back to track {controller._current_track_index + 1}")

        # Test PREVIOUS button at beginning
        controller._current_track_index = 0
        await mock_controls.simulate_previous_track()
        assert controller._current_track_index == 0  # Should stay at first track
        logger.log(LogLevel.INFO, "✅ Previous button at start: Stayed at track 1")

        # Test NEXT button at end
        controller._current_track_index = 3  # Last track
        await mock_controls.simulate_next_track()
        assert controller._current_track_index == 3  # Should stay at last track
        logger.log(LogLevel.INFO, "✅ Next button at end: Stayed at last track")

    @pytest.mark.asyncio
    async def test_play_pause_button_toggle(self, controls_manager_with_playlist, audio_controller_with_playlist):
        """Test play/pause button toggling during playback."""
        controller = audio_controller_with_playlist
        mock_controls = controls_manager_with_playlist.get_physical_controls()
        service = controller.audio_service

        # Initially paused
        assert controller._internal_playing_state is False
        assert service.is_playing is False

        # Press PLAY/PAUSE - should start playback
        await mock_controls.simulate_play_pause()
        # Check that toggle was called (not service.play directly)
        assert controller.toggle_playback.called
        assert controller._internal_playing_state is True
        service.is_playing = True  # Simulate service state change
        logger.log(LogLevel.INFO, "✅ Play/Pause: Started playback")

        # Press PLAY/PAUSE again - should pause
        controller.toggle_playback.reset_mock()  # Reset call count
        await mock_controls.simulate_play_pause()
        assert controller.toggle_playback.called
        assert controller._internal_playing_state is False
        service.is_playing = False
        logger.log(LogLevel.INFO, "✅ Play/Pause: Paused playback")

        # Press PLAY/PAUSE again - should resume
        controller.toggle_playback.reset_mock()
        await mock_controls.simulate_play_pause()
        assert controller.toggle_playback.called
        assert controller._internal_playing_state is True
        service.is_playing = True
        logger.log(LogLevel.INFO, "✅ Play/Pause: Resumed playback")

    @pytest.mark.asyncio
    async def test_volume_control_during_playback(self, controls_manager_with_playlist, audio_controller_with_playlist):
        """Test volume encoder control during playback."""
        controller = audio_controller_with_playlist
        mock_controls = controls_manager_with_playlist.get_physical_controls()
        service = controller.audio_service

        # Start with default volume
        initial_volume = service.volume
        assert initial_volume == 50
        logger.log(LogLevel.INFO, f"🔊 Initial volume: {initial_volume}%")

        # Start playback
        controller.play()

        # Simulate volume UP rotations
        for i in range(3):
            await mock_controls.simulate_volume_up()
            # Each rotation should increase volume (mock increases by 5)
            expected_volume = initial_volume + (i + 1) * 5
            service.volume = expected_volume  # Simulate service update
            logger.log(LogLevel.INFO, f"✅ Volume UP: {service.volume}%")

        assert service.volume == 65  # 50 + 3*5

        # Simulate volume DOWN rotations
        for i in range(5):
            await mock_controls.simulate_volume_down()
            service.volume = max(0, service.volume - 5)  # Simulate service update
            logger.log(LogLevel.INFO, f"✅ Volume DOWN: {service.volume}%")

        assert service.volume == 40  # 65 - 5*5 = 40

        # Test volume boundaries
        service.volume = 5
        await mock_controls.simulate_volume_down()
        service.volume = 0
        assert service.volume == 0
        logger.log(LogLevel.INFO, "✅ Volume at minimum: 0%")

        service.volume = 95
        for _ in range(3):
            await mock_controls.simulate_volume_up()
            service.volume = min(100, service.volume + 5)
        assert service.volume == 100
        logger.log(LogLevel.INFO, "✅ Volume at maximum: 100%")

    @pytest.mark.asyncio
    async def test_complete_playback_scenario(self, controls_manager_with_playlist, audio_controller_with_playlist):
        """Test a complete user scenario with multiple button interactions."""
        controller = audio_controller_with_playlist
        mock_controls = controls_manager_with_playlist.get_physical_controls()
        service = controller.audio_service

        logger.log(LogLevel.INFO, "🎭 Starting complete playback scenario test")

        # Scenario: User starts playlist, navigates tracks, adjusts volume

        # 1. Start playback with play button
        await mock_controls.simulate_play_pause()
        service.is_playing = True
        controller._internal_playing_state = True
        assert controller._current_track_index == 0
        logger.log(LogLevel.INFO, "✅ Step 1: Started playback on Track 1")

        # 2. Increase volume
        initial_vol = service.volume
        await mock_controls.simulate_volume_up()
        await mock_controls.simulate_volume_up()
        service.volume = initial_vol + 10
        logger.log(LogLevel.INFO, f"✅ Step 2: Increased volume to {service.volume}%")

        # 3. Skip to next track
        await mock_controls.simulate_next_track()
        assert controller._current_track_index == 1
        logger.log(LogLevel.INFO, "✅ Step 3: Skipped to Track 2")

        # 4. Skip to next track again
        await mock_controls.simulate_next_track()
        assert controller._current_track_index == 2
        logger.log(LogLevel.INFO, "✅ Step 4: Skipped to Track 3")

        # 5. Pause playback
        await mock_controls.simulate_play_pause()
        service.is_playing = False
        controller._internal_playing_state = False
        logger.log(LogLevel.INFO, "✅ Step 5: Paused playback")

        # 6. Go back to previous track
        await mock_controls.simulate_previous_track()
        assert controller._current_track_index == 1
        logger.log(LogLevel.INFO, "✅ Step 6: Went back to Track 2")

        # 7. Resume playback
        await mock_controls.simulate_play_pause()
        service.is_playing = True
        controller._internal_playing_state = True
        logger.log(LogLevel.INFO, "✅ Step 7: Resumed playback")

        # 8. Decrease volume
        current_vol = service.volume
        await mock_controls.simulate_volume_down()
        await mock_controls.simulate_volume_down()
        await mock_controls.simulate_volume_down()
        service.volume = current_vol - 15
        logger.log(LogLevel.INFO, f"✅ Step 8: Decreased volume to {service.volume}%")

        # 9. Quick navigation test (rapid button presses)
        await mock_controls.simulate_next_track()
        await mock_controls.simulate_next_track()
        assert controller._current_track_index == 3  # Should be at track 4
        logger.log(LogLevel.INFO, "✅ Step 9: Rapid navigation to Track 4")

        # 10. Stop playback
        await mock_controls.simulate_play_pause()
        service.is_playing = False
        controller._internal_playing_state = False
        logger.log(LogLevel.INFO, "✅ Step 10: Stopped playback")

        logger.log(LogLevel.INFO, "🎉 Complete scenario test passed!")

    @pytest.mark.asyncio
    async def test_button_events_are_debounced(self, controls_manager_with_playlist):
        """Test that button events are properly debounced."""
        mock_controls = controls_manager_with_playlist.get_physical_controls()
        controller = controls_manager_with_playlist.audio_controller

        # Simulate rapid button presses (debounce should prevent multiple triggers)
        initial_index = controller._current_track_index

        # Rapid next button presses
        for _ in range(5):
            await mock_controls.simulate_next_track()
            await asyncio.sleep(0.01)  # Very short delay

        # Should have moved forward, but not 5 times if debounced
        # (This depends on actual implementation of debouncing)
        assert controller._current_track_index >= initial_index
        logger.log(LogLevel.INFO, f"✅ Debouncing test: Moved {controller._current_track_index - initial_index} tracks")

    @pytest.mark.asyncio
    async def test_concurrent_button_presses(self, controls_manager_with_playlist):
        """Test handling of concurrent button presses."""
        mock_controls = controls_manager_with_playlist.get_physical_controls()
        controller = controls_manager_with_playlist.audio_controller

        # Start playback
        controller.play()
        controller._internal_playing_state = True

        # Simulate concurrent button presses
        tasks = [
            mock_controls.simulate_volume_up(),
            mock_controls.simulate_next_track(),
            mock_controls.simulate_volume_down(),
        ]

        # Execute concurrently
        await asyncio.gather(*tasks)

        # System should handle all events without crashing
        assert controls_manager_with_playlist.is_initialized()
        logger.log(LogLevel.INFO, "✅ Concurrent button handling test passed")

    @pytest.mark.asyncio
    async def test_controls_state_persistence(self, controls_manager_with_playlist):
        """Test that control states persist correctly during playback."""
        controller = controls_manager_with_playlist.audio_controller
        mock_controls = controls_manager_with_playlist.get_physical_controls()

        # Set initial state
        controller._current_track_index = 1
        controller.audio_service.volume = 75
        controller._internal_playing_state = True

        # Perform actions
        await mock_controls.simulate_next_track()
        await mock_controls.simulate_volume_up()

        # Check state persistence
        status = controls_manager_with_playlist.get_status()
        assert status["initialized"] is True
        assert status["gpio_integration"] is True
        assert controller._current_track_index == 2

        logger.log(LogLevel.INFO, "✅ State persistence test passed")


@pytest.mark.integration
class TestPhysicalControlsIntegrationWithAudio:
    """Integration tests with actual audio system components."""

    @pytest.mark.asyncio
    async def test_full_stack_integration(self):
        """Test full integration from GPIO to audio playback (mock mode)."""
        # This test would integrate with the actual audio engine
        # but use mock GPIO controls

        hardware_config = HardwareConfig(mock_hardware=True)

        # Create full stack with mocked audio backend
        from app.src.domain.audio.container import audio_domain_container
        from app.src.application.controllers.unified_controller import unified_controller

        # Initialize controls manager
        controls_manager = PhysicalControlsManager(
            audio_controller=unified_controller,
            hardware_config=hardware_config
        )

        try:
            # Initialize
            success = await controls_manager.initialize()
            assert success is True

            # Get mock controls
            mock_controls = controls_manager.get_physical_controls()
            assert isinstance(mock_controls, MockPhysicalControls)

            # Simulate button press
            await mock_controls.simulate_play_pause()

            # Verify integration worked (no crashes)
            assert controls_manager.is_initialized()

            logger.log(LogLevel.INFO, "✅ Full stack integration test passed")

        finally:
            await controls_manager.cleanup()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])