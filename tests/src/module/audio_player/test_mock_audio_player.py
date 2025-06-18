"""Tests for the MockAudioPlayer class.

These tests verify the functionality of the mock audio player
implementation that simulates audio playback for testing and development
environments.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.src.model.playlist import Playlist
from app.src.model.track import Track
from app.src.module.audio_player.audio_mock import MockAudioPlayer
from app.src.services.notification_service import PlaybackSubject


@pytest.fixture
def mock_playback_subject():
    """Create a mock playback subject."""
    subject = MagicMock(spec=PlaybackSubject)
    subject.notify_playback_status = MagicMock()
    subject.notify_track_progress = MagicMock()
    return subject


@pytest.fixture
def audio_player(mock_playback_subject):
    """Create a MockAudioPlayer instance with a mock playback subject."""
    # Create a player with a mock subject but without starting the progress thread
    with patch.object(MockAudioPlayer, "_start_progress_thread"):
        player = MockAudioPlayer(playback_subject=mock_playback_subject)
    return player


@pytest.fixture
def sample_playlist():
    """Create a sample playlist with tracks for testing."""
    tracks = [
        Track(
            number=1,
            title="Track 1",
            filename="track1.mp3",
            path=Path("/tmp/track1.mp3"),
        ),
        Track(
            number=2,
            title="Track 2",
            filename="track2.mp3",
            path=Path("/tmp/track2.mp3"),
        ),
        Track(
            number=3,
            title="Track 3",
            filename="track3.mp3",
            path=Path("/tmp/track3.mp3"),
        ),
    ]
    return Playlist(name="Test Playlist", tracks=tracks)


@pytest.mark.audio
def test_mock_audio_player_init(mock_playback_subject):
    """Test initialization of MockAudioPlayer."""
    # Patch the _start_progress_thread method to avoid threading issues in tests
    with patch.object(MockAudioPlayer, "_start_progress_thread"):
        player = MockAudioPlayer(playback_subject=mock_playback_subject)

    # Verify initial state
    assert not player.is_playing
    assert not player.is_paused
    assert player._volume == 50
    assert player._playback_subject == mock_playback_subject


@pytest.mark.audio
def test_mock_audio_player_play(audio_player):
    """Test the play method."""
    # Play a track
    track_path = "/tmp/test_track.mp3"
    audio_player.play(track_path)

    # Verify the player state
    assert audio_player.is_playing
    assert not audio_player.is_paused
    assert audio_player._current_track is not None
    assert audio_player._current_track.filename == "test_track.mp3"

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "playing",
        {"name": "Single Track", "track_count": 1},
        {
            "number": 1,
            "title": "test_track",
            "filename": "test_track.mp3",
            "duration": 180.0,
        },
    )


@pytest.mark.audio
def test_mock_audio_player_set_playlist(audio_player, sample_playlist):
    """Test setting a playlist and starting playback."""
    # Set the playlist
    result = audio_player.set_playlist(sample_playlist)

    # Verify the result
    assert result

    # Verify the player state
    assert audio_player.is_playing
    assert audio_player._playlist == sample_playlist
    assert audio_player._current_track == sample_playlist.tracks[0]

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "playing",
        {"name": "Test Playlist", "track_count": 3},
        {"number": 1, "title": "Track 1", "filename": "track1.mp3", "duration": 180.0},
    )


@pytest.mark.audio
def test_mock_audio_player_set_empty_playlist(audio_player):
    """Test setting an empty playlist."""
    # Create an empty playlist
    empty_playlist = Playlist(name="Empty Playlist", tracks=[])

    # Set the empty playlist
    result = audio_player.set_playlist(empty_playlist)

    # Verify the result
    assert not result

    # Verify the player state
    assert not audio_player.is_playing
    assert audio_player._playlist == empty_playlist
    assert audio_player._current_track is None


@pytest.mark.audio
def test_mock_audio_player_play_track(audio_player, sample_playlist):
    """Test playing a specific track from the playlist."""
    # Set the playlist first
    audio_player._playlist = sample_playlist

    # Play track 2
    result = audio_player.play_track(2)

    # Verify the result
    assert result

    # Verify the player state
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[1]

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "playing",
        {"name": "Test Playlist", "track_count": 3},
        {"number": 2, "title": "Track 2", "filename": "track2.mp3", "duration": 180.0},
    )


@pytest.mark.audio
def test_mock_audio_player_play_nonexistent_track(audio_player, sample_playlist):
    """Test playing a track that doesn't exist in the playlist."""
    # Set the playlist first
    audio_player._playlist = sample_playlist

    # Play a nonexistent track (track 5)
    result = audio_player.play_track(5)

    # Verify the result
    assert result  # The mock player creates a fake track even if it doesn't exist

    # Verify the player state
    assert audio_player.is_playing
    assert audio_player._current_track is not None
    assert audio_player._current_track.number == 5  # A mock track was created

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called()


@pytest.mark.audio
def test_mock_audio_player_play_track_no_playlist(audio_player):
    """Test playing a track when no playlist is set."""
    # Try to play a track without a playlist
    result = audio_player.play_track(1)

    # Verify the result
    assert not result

    # Verify the player state
    assert not audio_player.is_playing
    assert audio_player._current_track is None


@pytest.mark.audio
def test_mock_audio_player_pause_resume(audio_player, sample_playlist):
    """Test pausing and resuming playback."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Verify the player is playing
    assert audio_player.is_playing

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Pause playback
    audio_player.pause()

    # Verify the player state
    assert not audio_player.is_playing
    assert audio_player.is_paused

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "paused",
        {"name": "Test Playlist", "track_count": 3},
        {"number": 1, "title": "Track 1", "filename": "track1.mp3", "duration": 180.0},
    )

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Resume playback
    audio_player.resume()

    # Verify the player state
    assert audio_player.is_playing
    assert not audio_player.is_paused

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "playing",
        {"name": "Test Playlist", "track_count": 3},
        {"number": 1, "title": "Track 1", "filename": "track1.mp3", "duration": 180.0},
    )


@pytest.mark.audio
def test_mock_audio_player_pause_not_playing(audio_player):
    """Test pausing when not playing."""
    # Verify the player is not playing
    assert not audio_player.is_playing

    # Pause playback
    audio_player.pause()

    # Verify the player state is unchanged
    assert not audio_player.is_playing
    assert not audio_player.is_paused

    # Verify that the playback status was not notified
    audio_player._playback_subject.notify_playback_status.assert_not_called()


@pytest.mark.audio
def test_mock_audio_player_resume_not_paused(audio_player):
    """Test resuming when not paused."""
    # Verify the player is not playing and not paused
    assert not audio_player.is_playing
    assert not audio_player.is_paused

    # Resume playback
    audio_player.resume()

    # Verify the player state is unchanged
    assert not audio_player.is_playing
    assert not audio_player.is_paused

    # Verify that the playback status was not notified
    audio_player._playback_subject.notify_playback_status.assert_not_called()


@pytest.mark.audio
def test_mock_audio_player_stop(audio_player, sample_playlist):
    """Test stopping playback."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Verify the player is playing
    assert audio_player.is_playing

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Stop playback
    audio_player.stop()

    # Verify the player state
    assert not audio_player.is_playing
    assert not audio_player.is_paused
    assert audio_player._current_track is None
    assert audio_player._playlist is None  # stop() clears the playlist by default

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "stopped", None, None
    )


@pytest.mark.audio
def test_mock_audio_player_stop_preserve_playlist(audio_player, sample_playlist):
    """Test stopping playback while preserving the playlist."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Verify the player is playing
    assert audio_player.is_playing

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Stop playback without clearing the playlist
    audio_player.stop(clear_playlist=False)

    # Verify the player state
    assert not audio_player.is_playing
    assert not audio_player.is_paused
    assert audio_player._current_track is None
    assert audio_player._playlist == sample_playlist  # Playlist is preserved

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "stopped", None, None
    )


@pytest.mark.audio
def test_mock_audio_player_next_track(audio_player, sample_playlist):
    """Test moving to the next track."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Verify the player is playing track 1
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[0]

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Move to the next track
    audio_player.next_track()

    # Verify the player state
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[1]

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "playing",
        {"name": "Test Playlist", "track_count": 3},
        {"number": 2, "title": "Track 2", "filename": "track2.mp3", "duration": 180.0},
    )


@pytest.mark.audio
def test_mock_audio_player_next_track_at_end(audio_player, sample_playlist):
    """Test moving to the next track when at the end of the playlist."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Play the last track
    audio_player.play_track(3)

    # Verify the player is playing the last track
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[2]

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Try to move to the next track (should stop at the end)
    audio_player.next_track()

    # Verify the player state
    assert not audio_player.is_playing
    assert audio_player._current_track is None

    # Verify that the playback status was notified with 'stopped'
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "stopped", None, None
    )


@pytest.mark.audio
def test_mock_audio_player_previous_track(audio_player, sample_playlist):
    """Test moving to the previous track."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Play track 2
    audio_player.play_track(2)

    # Verify the player is playing track 2
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[1]

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Move to the previous track
    audio_player.previous_track()

    # Verify the player state
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[0]

    # Verify that the playback status was notified
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "playing",
        {"name": "Test Playlist", "track_count": 3},
        {"number": 1, "title": "Track 1", "filename": "track1.mp3", "duration": 180.0},
    )


@pytest.mark.audio
def test_mock_audio_player_previous_track_at_start(audio_player, sample_playlist):
    """Test moving to the previous track when at the start of the playlist."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Verify the player is playing the first track
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[0]

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Try to move to the previous track (should stay on the first track)
    audio_player.previous_track()

    # Verify the player state is unchanged
    assert audio_player.is_playing
    assert audio_player._current_track == sample_playlist.tracks[0]

    # Verify that the playback status was not notified (no change)
    audio_player._playback_subject.notify_playback_status.assert_not_called()


@pytest.mark.audio
def test_mock_audio_player_set_volume(audio_player):
    """Test setting the volume."""
    # Set the volume to 75%
    result = audio_player.set_volume(75)

    # Verify the result
    assert result

    # Verify the volume was set
    assert audio_player._volume == 75


@pytest.mark.audio
def test_mock_audio_player_set_volume_out_of_range(audio_player):
    """Test setting the volume with values out of range."""
    # Set the volume to a value below 0
    result = audio_player.set_volume(-10)

    # Verify the result
    assert result

    # Verify the volume was clamped to 0
    assert audio_player._volume == 0

    # Set the volume to a value above 100
    result = audio_player.set_volume(110)

    # Verify the result
    assert result

    # Verify the volume was clamped to 100
    assert audio_player._volume == 100


@pytest.mark.audio
def test_mock_audio_player_cleanup(audio_player, sample_playlist):
    """Test cleaning up resources."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Create a mock for the progress thread
    mock_thread = MagicMock()
    mock_thread.join = MagicMock()
    audio_player._progress_thread = mock_thread

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Clean up resources
    audio_player.cleanup()

    # Verify the player state
    assert not audio_player.is_playing
    assert audio_player._current_track is None
    assert audio_player._playlist is None
    assert audio_player._stop_progress is True

    # Verify that join was called on the progress thread
    mock_thread.join.assert_called_once()

    # Verify that the playback status was notified with 'stopped'
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "stopped", None, None
    )


@pytest.mark.audio
def test_mock_audio_player_notify_playback_status(audio_player, sample_playlist):
    """Test notifying playback status changes."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Reset the mock to clear previous calls
    audio_player._playback_subject.notify_playback_status.reset_mock()

    # Call the _notify_playback_status method directly with 'paused'
    audio_player._notify_playback_status("paused")

    # Verify that the playback status was notified with the correct information
    audio_player._playback_subject.notify_playback_status.assert_called_with(
        "paused",
        {"name": "Test Playlist", "track_count": 3},
        {"number": 1, "title": "Track 1", "filename": "track1.mp3", "duration": 180.0},
    )


@pytest.mark.audio
def test_mock_audio_player_handle_track_end(audio_player, sample_playlist):
    """Test handling the end of a track."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Mock the play_track method to verify it's called
    audio_player.play_track = MagicMock(wraps=audio_player.play_track)

    # Call the _handle_track_end method directly
    audio_player._handle_track_end()

    # Verify that play_track was called with the next track number
    audio_player.play_track.assert_called_once_with(2)


@pytest.mark.audio
def test_mock_audio_player_handle_track_end_at_end_of_playlist(
    audio_player, sample_playlist
):
    """Test handling the end of a track when at the end of the playlist."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Play the last track
    audio_player.play_track(3)

    # Mock the stop method to verify it's called
    audio_player.stop = MagicMock(wraps=audio_player.stop)

    # Call the _handle_track_end method directly
    audio_player._handle_track_end()

    # Verify that stop was called
    audio_player.stop.assert_called_once()


@pytest.mark.audio
@pytest.mark.timeout(2)
def test_mock_audio_player_progress_loop(audio_player, sample_playlist):
    """Test the progress tracking loop."""
    # Set the playlist and start playback
    audio_player.set_playlist(sample_playlist)

    # Set up a mock for time.sleep to avoid actual sleeping
    with patch("time.sleep") as mock_sleep, patch("time.time") as mock_time:
        # Configure time.time to return increasing values
        mock_time.side_effect = [100.0, 100.5]

        # Set the track start time
        audio_player._track_start_time = 90.0  # 10 seconds into the track

        # Setup stop flag to terminate after one iteration
        called = {"value": False}

        def side_effect(*args, **kwargs):
            # Set the stop flag after the first call to time.sleep
            audio_player._stop_progress = True
            called["value"] = True

        mock_sleep.side_effect = side_effect

        # Run the progress loop
        audio_player._stop_progress = False
        audio_player._progress_loop()

        # Ensure our side_effect was called (loop exited as expected)
        assert called[
            "value"
        ], "Mock sleep side_effect was not called; loop may not have exited."

        # Verify that notify_track_progress was called with correct structure
        args, kwargs = audio_player._playback_subject.notify_track_progress.call_args
        assert kwargs["total"] == 180.0
        assert kwargs["track_number"] == 1
        assert kwargs["track_info"] == {
            "number": 1,
            "title": "Track 1",
            "filename": "track1.mp3",
            "duration": 180.0,
        }
        assert kwargs["playlist_info"] == {"name": "Test Playlist", "track_count": 3}
        assert kwargs["is_playing"] is True
        assert kwargs["elapsed"] == pytest.approx(10.0, abs=0.5)  # Accept 10.0 or 10.5
