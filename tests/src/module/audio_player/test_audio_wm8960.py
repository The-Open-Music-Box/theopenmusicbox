"""
Tests for the AudioPlayerWM8960 class.

These tests verify the functionality of the WM8960 hardware audio player implementation.
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.src.module.audio_player.audio_wm8960 import AudioPlayerWM8960
from app.src.module.audio_player.pygame_audio_backend import PygameAudioBackend
from app.src.model.playlist import Playlist
from app.src.model.track import Track
from app.src.services.notification_service import PlaybackSubject

@pytest.fixture
def mock_pygame_backend():
    """Create a mock pygame backend."""
    backend = MagicMock(spec=PygameAudioBackend)
    backend.initialize.return_value = True
    backend.is_playing.return_value = False # Default state
    backend.load.return_value = True

    def mock_play_effect(*args, **kwargs):
        backend.is_playing.return_value = True
        return True
    backend.play.side_effect = mock_play_effect
    backend.play.return_value = True # Keep a default return value

    def mock_resume_effect(*args, **kwargs):
        backend.is_playing.return_value = True
        return True
    backend.resume.side_effect = mock_resume_effect
    backend.resume.return_value = True

    def mock_pause_effect(*args, **kwargs):
        backend.is_playing.return_value = False
        return True
    backend.pause.side_effect = mock_pause_effect
    backend.pause.return_value = True

    def mock_stop_effect(*args, **kwargs):
        backend.is_playing.return_value = False
        return True
    backend.stop.side_effect = mock_stop_effect
    backend.stop.return_value = True
    backend.set_volume.return_value = True
    backend.set_position.return_value = True
    backend.get_duration.return_value = 180.0  # Mock duration
    return backend

@pytest.fixture
def mock_playback_subject():
    """Create a mock playback subject."""
    subject = MagicMock(spec=PlaybackSubject)
    subject.notify_playback_status = MagicMock()
    subject.notify_track_progress = MagicMock()
    return subject

@pytest.fixture
def audio_player_wm8960(mock_pygame_backend, mock_playback_subject):
    """Create an AudioPlayerWM8960 instance with mock dependencies."""
    with patch('app.src.module.audio_player.audio_wm8960.PygameAudioBackend', return_value=mock_pygame_backend):
        player = AudioPlayerWM8960(playback_subject=mock_playback_subject)
    return player

@pytest.fixture
def sample_playlist():
    """Create a sample playlist with tracks for testing."""
    tracks = [
        Track(number=1, title="Track 1", filename="track1.mp3", path=Path("/tmp/track1.mp3")),
        Track(number=2, title="Track 2", filename="track2.mp3", path=Path("/tmp/track2.mp3")),
        Track(number=3, title="Track 3", filename="track3.mp3", path=Path("/tmp/track3.mp3"))
    ]
    return Playlist(name="Test Playlist", tracks=tracks)

@pytest.mark.audio
def test_audio_wm8960_init(mock_pygame_backend, mock_playback_subject):
    """Test initialization of AudioPlayerWM8960."""
    with patch('app.src.module.audio_player.audio_wm8960.PygameAudioBackend', return_value=mock_pygame_backend):
        player = AudioPlayerWM8960(playback_subject=mock_playback_subject)
    assert not player.is_playing
    assert not player.is_paused
    mock_pygame_backend.initialize.assert_called_once()
    mock_pygame_backend.register_end_event_callback.assert_called_once_with(player._handle_track_end)

@pytest.mark.audio
@patch('app.src.module.audio_player.audio_wm8960.MP3')
def test_audio_wm8960_play_track(mock_mp3, audio_player_wm8960, sample_playlist, mock_pygame_backend, mock_playback_subject):
    """Test playing a track."""
    mock_audio_info = MagicMock()
    mock_audio_info.info.length = 180.0
    mock_mp3.return_value = mock_audio_info
    audio_player_wm8960._playlist = sample_playlist

    result = audio_player_wm8960.play_track(1)

    assert result is True
    assert audio_player_wm8960.is_playing
    assert audio_player_wm8960._current_track == sample_playlist.tracks[0]
    mock_pygame_backend.load.assert_called_with(str(sample_playlist.tracks[0].path))
    mock_pygame_backend.play.assert_called_once()
    # Check for the loading call with expected populated data
    expected_loading_playlist_info = {'name': 'Test Playlist', 'track_count': 3}
    expected_loading_track_info = {'number': 1, 'title': 'Track 1', 'filename': 'track1.mp3', 'duration': 180.0}
    mock_playback_subject.notify_playback_status.assert_any_call("loading", expected_loading_playlist_info, expected_loading_track_info)
    mock_playback_subject.notify_playback_status.assert_called_with(
        'playing',
        {'name': 'Test Playlist', 'track_count': 3},
        {
            'number': 1,
            'title': 'Track 1',
            'filename': 'track1.mp3',
            'duration': 180.0
        }
    )

@pytest.mark.audio
@patch('app.src.module.audio_player.audio_wm8960.MP3')
def test_audio_wm8960_pause_resume(mock_mp3, audio_player_wm8960, sample_playlist, mock_pygame_backend, mock_playback_subject):
    """Test pausing and resuming playback."""
    mock_audio_info = MagicMock()
    mock_audio_info.info.length = 180.0
    mock_mp3.return_value = mock_audio_info
    audio_player_wm8960._playlist = sample_playlist
    audio_player_wm8960.play_track(1) # Start playing

    # Pause
    audio_player_wm8960.pause()
    assert not audio_player_wm8960.is_playing
    assert audio_player_wm8960.is_paused
    mock_pygame_backend.pause.assert_called_once()
    mock_playback_subject.notify_playback_status.assert_called_with(
        'paused',
        {'name': 'Test Playlist', 'track_count': 3},
        {
            'number': 1,
            'title': 'Track 1',
            'filename': 'track1.mp3',
            'duration': 180.0
        }
    )

    # Resume
    audio_player_wm8960.resume()
    assert audio_player_wm8960.is_playing
    assert not audio_player_wm8960.is_paused
    mock_pygame_backend.resume.assert_called_once()  # Changed from unpause
    # Check for the 'playing' notification after resume
    # The call count for 'playing' will be 2 (initial play + resume)
    assert mock_playback_subject.notify_playback_status.call_count >= 2
    # Get the last call to notify_playback_status
    last_call_args = mock_playback_subject.notify_playback_status.call_args_list[-1][0]
    assert last_call_args[0] == 'playing'


@pytest.mark.audio
def test_audio_wm8960_stop(audio_player_wm8960, sample_playlist, mock_pygame_backend, mock_playback_subject):
    """Test stopping playback."""
    audio_player_wm8960._playlist = sample_playlist
    audio_player_wm8960.play_track(1) # Start playing

    audio_player_wm8960.stop()
    assert not audio_player_wm8960.is_playing
    assert not audio_player_wm8960.is_paused
    assert audio_player_wm8960._current_track is None
    assert audio_player_wm8960._playlist is None # Playlist is cleared by default
    mock_pygame_backend.stop.assert_called() # Called multiple times (play_track calls stop)
    mock_playback_subject.notify_playback_status.assert_called_with('stopped', None, None)

@pytest.mark.audio
def test_audio_wm8960_set_volume(audio_player_wm8960, mock_pygame_backend):
    """Test setting the volume."""
    result = audio_player_wm8960.set_volume(75)
    assert result is True
    assert audio_player_wm8960._volume == 75
    mock_pygame_backend.set_volume.assert_called_with(75) # Pygame backend expects 0-100

@pytest.mark.audio
def test_audio_wm8960_cleanup(audio_player_wm8960, mock_pygame_backend):
    """Test cleaning up resources."""
    # Mock the progress thread to check join
    mock_thread = MagicMock()
    audio_player_wm8960._progress_thread = mock_thread

    audio_player_wm8960.cleanup()

    assert audio_player_wm8960._stop_progress is True
    mock_thread.join.assert_called_once_with(timeout=2.0)
    mock_pygame_backend.shutdown.assert_called_once()
    assert not audio_player_wm8960._audio_cache # Cache should be cleared

@pytest.mark.audio
@patch('app.src.module.audio_player.audio_wm8960.MP3')
def test_audio_wm8960_get_track_duration(mock_mp3, audio_player_wm8960):
    """Test getting track duration."""
    mock_audio_info = MagicMock()
    mock_audio_info.info.length = 180.0
    mock_mp3.return_value = mock_audio_info

    # Test with MP3
    duration = audio_player_wm8960._get_track_duration(Path("/tmp/test.mp3"))
    assert duration == 180.0

    # Test with non-MP3 (should return 0)
    mock_mp3.side_effect = Exception("Simulating mutagen error for non-mp3") # or just ensure it's not called for non-mp3
    duration = audio_player_wm8960._get_track_duration(Path("/tmp/test.wav"))
    assert duration == 0.0

@pytest.mark.audio
@patch('app.src.module.audio_player.audio_wm8960.MP3')
def test_audio_wm8960_handle_track_end(mock_mp3, audio_player_wm8960, sample_playlist, mock_playback_subject):
    """Test handling the end of a track."""
    mock_audio_info = MagicMock()
    mock_audio_info.info.length = 180.0
    mock_mp3.return_value = mock_audio_info
    audio_player_wm8960._playlist = sample_playlist
    audio_player_wm8960.play_track(1) # Play first track

    # Reset mocks to check calls specifically from _handle_track_end
    mock_playback_subject.notify_playback_status.reset_mock()

    # Simulate track end
    audio_player_wm8960._handle_track_end()

    # Should play next track (track 2)
    assert audio_player_wm8960.is_playing
    assert audio_player_wm8960._current_track == sample_playlist.tracks[1]
    # Check for 'playing' notification for the new track
    mock_playback_subject.notify_playback_status.assert_called_with(
        'playing',
        {'name': 'Test Playlist', 'track_count': 3},
        {
            'number': 2,
            'title': 'Track 2',
            'filename': 'track2.mp3',
            'duration': 180.0
        }
    )

@pytest.mark.audio
def test_audio_wm8960_handle_track_end_at_playlist_end(audio_player_wm8960, sample_playlist, mock_playback_subject):
    """Test handling the end of a track when at the end of the playlist."""
    audio_player_wm8960._playlist = sample_playlist
    audio_player_wm8960.play_track(3) # Play last track

    # Reset mocks
    mock_playback_subject.notify_playback_status.reset_mock()

    # Simulate track end
    audio_player_wm8960._handle_track_end()

    # Should stop playback
    assert not audio_player_wm8960.is_playing
    assert audio_player_wm8960._current_track is None
    mock_playback_subject.notify_playback_status.assert_called_with('stopped', None, None)
