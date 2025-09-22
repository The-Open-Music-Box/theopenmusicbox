# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Test Physical Controls User Scenario.

Complete end-to-end test simulating a realistic user scenario with physical controls.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import random

from app.src.controllers.physical_controls_manager import PhysicalControlsManager
from app.src.infrastructure.hardware.controls.mock_controls_implementation import MockPhysicalControls
from app.src.config.hardware_config import HardwareConfig
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)


class TestUserScenario:
    """Test complete user scenario with physical controls."""

    @pytest.mark.asyncio
    async def test_complete_user_listening_session(self):
        """
        Simulate a complete user listening session:
        1. User turns on the device
        2. Starts playing a playlist
        3. Adjusts volume to comfortable level
        4. Skips a track they don't like
        5. Pauses to answer a phone call
        6. Resumes playback
        7. Goes back to replay a favorite track
        8. Increases volume for a good song
        9. Lets playlist play to the end
        10. Turns off device
        """

        logger.log(LogLevel.INFO, "=" * 60)
        logger.log(LogLevel.INFO, "🎭 STARTING COMPLETE USER SCENARIO TEST")
        logger.log(LogLevel.INFO, "=" * 60)

        # Setup hardware configuration
        hardware_config = HardwareConfig(mock_hardware=True)

        # Create test playlist
        playlist = Playlist(
            name="Favorites Mix",
            tracks=[
                Track(track_number=1, title="Morning Coffee", filename="track1.mp3", file_path="/music/track1.mp3", duration_ms=180000, artist="Chill Vibes", id="t1"),
                Track(track_number=2, title="Commercial Jingle", filename="track2.mp3", file_path="/music/track2.mp3", duration_ms=30000, artist="Ad Agency", id="t2"),
                Track(track_number=3, title="Summer Memories", filename="track3.mp3", file_path="/music/track3.mp3", duration_ms=240000, artist="Nostalgia", id="t3"),
                Track(track_number=4, title="Epic Anthem", filename="track4.mp3", file_path="/music/track4.mp3", duration_ms=300000, artist="Power Band", id="t4"),
                Track(track_number=5, title="Goodnight Lullaby", filename="track5.mp3", file_path="/music/track5.mp3", duration_ms=150000, artist="Sleepy Time", id="t5"),
            ],
            id="playlist_favorites"
        )

        # Setup mock audio controller
        audio_controller = Mock()
        audio_controller._current_playlist = playlist
        audio_controller._current_track_index = 0
        audio_controller._internal_playing_state = False
        audio_controller.audio_service = Mock()
        audio_controller.audio_service.volume = 30  # Start with low volume

        # Track playback state
        playback_log = []

        def log_action(action):
            """Log user actions for verification."""
            playback_log.append(action)
            logger.log(LogLevel.INFO, f"📝 {action}")

        # Setup mock methods with logging
        def mock_toggle():
            if audio_controller._internal_playing_state:
                audio_controller._internal_playing_state = False
                log_action(f"⏸️ PAUSED at track {audio_controller._current_track_index + 1}: {playlist.tracks[audio_controller._current_track_index].title}")
            else:
                audio_controller._internal_playing_state = True
                log_action(f"▶️ PLAYING track {audio_controller._current_track_index + 1}: {playlist.tracks[audio_controller._current_track_index].title}")
            return True

        def mock_next():
            if audio_controller._current_track_index < len(playlist.tracks) - 1:
                audio_controller._current_track_index += 1
                log_action(f"⏭️ SKIPPED to track {audio_controller._current_track_index + 1}: {playlist.tracks[audio_controller._current_track_index].title}")
                return True
            log_action("🔚 END of playlist reached")
            return False

        def mock_previous():
            if audio_controller._current_track_index > 0:
                audio_controller._current_track_index -= 1
                log_action(f"⏮️ BACK to track {audio_controller._current_track_index + 1}: {playlist.tracks[audio_controller._current_track_index].title}")
                return True
            log_action("🔝 START of playlist reached")
            return False

        def mock_volume_up():
            old_volume = audio_controller.audio_service.volume
            audio_controller.audio_service.volume = min(100, old_volume + 10)
            log_action(f"🔊 VOLUME UP: {old_volume}% → {audio_controller.audio_service.volume}%")
            return True

        def mock_volume_down():
            old_volume = audio_controller.audio_service.volume
            audio_controller.audio_service.volume = max(0, old_volume - 10)
            log_action(f"🔉 VOLUME DOWN: {old_volume}% → {audio_controller.audio_service.volume}%")
            return True

        audio_controller.toggle_playback = mock_toggle
        audio_controller.next_track = mock_next
        audio_controller.previous_track = mock_previous
        audio_controller.increase_volume = mock_volume_up
        audio_controller.decrease_volume = mock_volume_down

        # Initialize physical controls
        controls_manager = PhysicalControlsManager(
            audio_controller=audio_controller,
            hardware_config=hardware_config
        )

        try:
            # Initialize controls
            await controls_manager.initialize()
            mock_controls = controls_manager.get_physical_controls()
            assert isinstance(mock_controls, MockPhysicalControls)

            logger.log(LogLevel.INFO, "\n🎬 SCENARIO START: User listening session\n")

            # Step 1: Turn on device (simulated)
            logger.log(LogLevel.INFO, "📱 Step 1: User turns on the device")
            await asyncio.sleep(0.1)  # Simulate startup time

            # Step 2: Start playing playlist
            logger.log(LogLevel.INFO, "🎵 Step 2: User starts playing the playlist")
            await mock_controls.simulate_play_pause()
            assert audio_controller._internal_playing_state is True
            assert audio_controller._current_track_index == 0

            # Step 3: Adjust volume to comfortable level
            logger.log(LogLevel.INFO, "🎚️ Step 3: User adjusts volume")
            await mock_controls.simulate_volume_up()
            await mock_controls.simulate_volume_up()
            assert audio_controller.audio_service.volume == 50

            # Simulate some listening time
            await asyncio.sleep(0.1)

            # Step 4: Skip the commercial jingle
            logger.log(LogLevel.INFO, "⏭️ Step 4: User skips to next track (doesn't like commercials)")
            await mock_controls.simulate_next_track()
            assert audio_controller._current_track_index == 1
            # Skip the commercial
            await mock_controls.simulate_next_track()
            assert audio_controller._current_track_index == 2

            # Step 5: Phone rings, pause playback
            await asyncio.sleep(0.1)
            logger.log(LogLevel.INFO, "📞 Step 5: Phone rings - user pauses")
            await mock_controls.simulate_play_pause()
            assert audio_controller._internal_playing_state is False

            # Simulate phone call duration
            await asyncio.sleep(0.2)

            # Step 6: Resume playback after call
            logger.log(LogLevel.INFO, "📵 Step 6: Call ended - user resumes")
            await mock_controls.simulate_play_pause()
            assert audio_controller._internal_playing_state is True

            # Step 7: Go back to replay favorite track
            logger.log(LogLevel.INFO, "💝 Step 7: User wants to replay previous track")
            await mock_controls.simulate_previous_track()
            assert audio_controller._current_track_index == 1
            # Skip commercial again
            await mock_controls.simulate_previous_track()
            assert audio_controller._current_track_index == 0

            # Step 8: Increase volume for favorite song
            logger.log(LogLevel.INFO, "🎸 Step 8: User increases volume for favorite song")
            await mock_controls.simulate_volume_up()
            await mock_controls.simulate_volume_up()
            await mock_controls.simulate_volume_up()
            assert audio_controller.audio_service.volume == 80

            # Step 9: Navigate through rest of playlist
            logger.log(LogLevel.INFO, "🎼 Step 9: User navigates through playlist")
            await mock_controls.simulate_next_track()  # To track 2
            await mock_controls.simulate_next_track()  # To track 3
            await mock_controls.simulate_next_track()  # To track 4
            await mock_controls.simulate_next_track()  # To track 5
            assert audio_controller._current_track_index == 4

            # Try to go past the end
            await mock_controls.simulate_next_track()
            assert audio_controller._current_track_index == 4  # Should stay at last track

            # Step 10: Lower volume before turning off
            logger.log(LogLevel.INFO, "🔇 Step 10: User lowers volume and stops")
            await mock_controls.simulate_volume_down()
            await mock_controls.simulate_volume_down()
            await mock_controls.simulate_volume_down()
            await mock_controls.simulate_volume_down()
            assert audio_controller.audio_service.volume == 40

            # Stop playback
            await mock_controls.simulate_play_pause()
            assert audio_controller._internal_playing_state is False

            logger.log(LogLevel.INFO, "\n🎬 SCENARIO END: Session completed successfully\n")

            # Verify the playback log
            logger.log(LogLevel.INFO, "📊 Session Summary:")
            logger.log(LogLevel.INFO, f"  Total actions: {len(playback_log)}")
            logger.log(LogLevel.INFO, f"  Final track: {playlist.tracks[audio_controller._current_track_index].title}")
            logger.log(LogLevel.INFO, f"  Final volume: {audio_controller.audio_service.volume}%")
            logger.log(LogLevel.INFO, f"  Final state: {'Playing' if audio_controller._internal_playing_state else 'Stopped'}")

            # Verify expected actions occurred
            assert any("PLAYING track 1" in action for action in playback_log)
            assert any("PAUSED" in action for action in playback_log)
            assert any("VOLUME UP" in action for action in playback_log)
            assert any("SKIPPED" in action for action in playback_log)
            assert any("BACK" in action for action in playback_log)

            logger.log(LogLevel.INFO, "✅ All user scenario steps completed successfully!")

        finally:
            # Cleanup
            await controls_manager.cleanup()
            logger.log(LogLevel.INFO, "🧹 Cleanup completed")

    @pytest.mark.asyncio
    async def test_rapid_button_interaction(self):
        """Test rapid button presses simulating excited user interaction."""
        logger.log(LogLevel.INFO, "\n🎮 TESTING RAPID BUTTON INTERACTIONS\n")

        hardware_config = HardwareConfig(mock_hardware=True)
        audio_controller = Mock()
        audio_controller._current_track_index = 0
        audio_controller._internal_playing_state = False
        audio_controller.audio_service = Mock(volume=50)

        # Simple mock implementations
        audio_controller.next_track = Mock(return_value=True)
        audio_controller.previous_track = Mock(return_value=True)
        audio_controller.toggle_playback = Mock(return_value=True)
        audio_controller.increase_volume = Mock(return_value=True)
        audio_controller.decrease_volume = Mock(return_value=True)

        controls_manager = PhysicalControlsManager(
            audio_controller=audio_controller,
            hardware_config=hardware_config
        )

        try:
            await controls_manager.initialize()
            mock_controls = controls_manager.get_physical_controls()

            # Simulate rapid random button presses
            button_actions = [
                mock_controls.simulate_next_track,
                mock_controls.simulate_previous_track,
                mock_controls.simulate_play_pause,
                mock_controls.simulate_volume_up,
                mock_controls.simulate_volume_down,
            ]

            logger.log(LogLevel.INFO, "🔥 Simulating 20 rapid random button presses...")

            for i in range(20):
                action = random.choice(button_actions)
                await action()
                await asyncio.sleep(0.01)  # Very short delay

            # System should handle all without crashing
            assert controls_manager.is_initialized()
            logger.log(LogLevel.INFO, "✅ Rapid interaction test passed - no crashes!")

        finally:
            await controls_manager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])