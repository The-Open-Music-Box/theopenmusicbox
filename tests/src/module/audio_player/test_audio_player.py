"""
Improved tests for the AudioPlayer wrapper class.

These tests verify the AudioPlayer functionality by using a real test implementation
of the AudioPlayerHardware interface instead of relying exclusively on MagicMock.
This approach ensures the actual behavior and integration between components is tested
correctly, with a focus on state transitions and real interactions.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock
import tempfile
import shutil

from app.src.module.audio_player.audio_player import AudioPlayer
from app.src.module.audio_player.audio_hardware import AudioPlayerHardware
from app.src.model.playlist import Playlist
from app.src.model.track import Track


class MockAudioHardwareImplementation(AudioPlayerHardware):
    """
    Real test implementation of the AudioPlayerHardware interface.
    This class simulates an audio hardware implementation for testing purposes,
    tracking internal state changes without relying on external hardware.
    """
    def __init__(self):
        self._is_playing = False
        self._is_paused = False
        self._current_track = None
        self._current_playlist = None
        self._current_track_index = -1
        self._volume = 80
        self._track_finished = False
        self._play_count = {}  # Track play count statistics for test verification

    def play(self, track_path):
        """Start playing a track."""
        self._is_playing = True
        self._is_paused = False
        self._current_track = track_path
        self._track_finished = False
        
        # Record play count for verification
        if track_path not in self._play_count:
            self._play_count[track_path] = 0
        self._play_count[track_path] += 1
        
        return True

    def pause(self):
        """Pause the current track."""
        if self._is_playing:
            self._is_paused = True
            self._is_playing = False
            return True
        return False

    def resume(self):
        """Resume a paused track."""
        if self._is_paused:
            self._is_playing = True
            self._is_paused = False
            return True
        return False

    def stop(self):
        """Stop the current track."""
        was_playing = self._is_playing or self._is_paused
        self._is_playing = False
        self._is_paused = False
        self._track_finished = False
        return was_playing

    def set_volume(self, volume):
        """Set the playback volume."""
        if 0 <= volume <= 100:
            self._volume = volume
            return True
        return False

    def cleanup(self):
        """Clean up resources."""
        self._is_playing = False
        self._is_paused = False
        self._current_track = None
        self._volume = 80
        return True

    def set_playlist(self, playlist):
        """Set the current playlist."""
        self._current_playlist = playlist
        self._current_track_index = -1
        return True

    def next_track(self):
        """Play the next track in the playlist."""
        if not self._current_playlist or not self._current_playlist.tracks:
            return False
            
        if self._current_track_index < len(self._current_playlist.tracks) - 1:
            self._current_track_index += 1
            track = self._current_playlist.tracks[self._current_track_index]
            return self.play(str(track.path))
        return False

    def previous_track(self):
        """Play the previous track in the playlist."""
        if not self._current_playlist or not self._current_playlist.tracks:
            return False
            
        if self._current_track_index > 0:
            self._current_track_index -= 1
            track = self._current_playlist.tracks[self._current_track_index]
            return self.play(str(track.path))
        return False

    def play_track(self, track_index):
        """Play a specific track from the playlist."""
        if not self._current_playlist or not self._current_playlist.tracks:
            return False
            
        if 0 <= track_index < len(self._current_playlist.tracks):
            self._current_track_index = track_index
            track = self._current_playlist.tracks[track_index]
            return self.play(str(track.path))
        return False

    @property
    def is_playing(self):
        """Check if audio is currently playing."""
        return self._is_playing

    @property
    def is_paused(self):
        """Check if audio is currently paused."""
        return self._is_paused
        
    def is_finished(self):
        """Check if the current track has finished playing."""
        return self._track_finished
        
    # Test helper methods for simulation
    def simulate_track_finished(self):
        """Simulate a track finishing playback."""
        self._is_playing = False
        self._track_finished = True
        
    def get_current_track(self):
        """Get the current track path for test verification."""
        return self._current_track
        
    def get_current_track_index(self):
        """Get the current track index for test verification."""
        return self._current_track_index
        
    def get_volume(self):
        """Get the current volume setting for test verification."""
        return self._volume
        
    def get_play_count(self, track_path):
        """Get the play count for a track for test verification."""
        return self._play_count.get(track_path, 0)


# Test fixtures

@pytest.fixture
def test_hardware():
    """Create a real test implementation of the audio hardware."""
    return MockAudioHardwareImplementation()


@pytest.fixture
def audio_player(test_hardware):
    """Create an AudioPlayer instance with test hardware implementation."""
    return AudioPlayer(hardware=test_hardware)


@pytest.fixture
def temp_audio_dir():
    """Create a temporary directory for test audio files."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create dummy audio files
        for i in range(1, 4):
            track_path = os.path.join(temp_dir, f"track{i}.mp3")
            with open(track_path, "w", encoding="utf-8") as f:
                f.write(f"dummy audio content for track{i}")
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_playlist(temp_audio_dir):
    """Create a sample playlist with tracks for testing."""
    tracks = [
        Track(number=1, title="Track 1", filename="track1.mp3", 
              path=Path(os.path.join(temp_audio_dir, "track1.mp3"))),
        Track(number=2, title="Track 2", filename="track2.mp3", 
              path=Path(os.path.join(temp_audio_dir, "track2.mp3"))),
        Track(number=3, title="Track 3", filename="track3.mp3", 
              path=Path(os.path.join(temp_audio_dir, "track3.mp3")))
    ]
    return Playlist(name="Test Playlist", tracks=tracks)


@pytest.fixture
def mock_hardware_for_fallback_tests():
    """Create a MagicMock for the hardware to test fallback attribute access."""
    hardware = MagicMock(spec=AudioPlayerHardware)
    # Set up default presence of attributes that AudioPlayer might check first
    # Tests will then delete these to check fallbacks
    hardware.is_playing = False
    hardware.is_paused = False
    # For is_finished, it's a method, so we'll mock it as such by default
    hardware.is_finished = MagicMock(return_value=False)
    return hardware


@pytest.fixture
def audio_player_with_mock_hardware(mock_hardware_for_fallback_tests):
    """Create an AudioPlayer instance with a MagicMock hardware for fallback tests."""
    return AudioPlayer(hardware=mock_hardware_for_fallback_tests)


# Test cases

@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_init(test_hardware):
    """Test initialization of the AudioPlayer wrapper with test hardware."""
    player = AudioPlayer(hardware=test_hardware)
    assert player._hardware == test_hardware


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_play_and_state(audio_player, temp_audio_dir):
    """Test the play method and verify state changes in the hardware."""
    # Initially not playing
    assert not audio_player.is_playing
    
    # Play a track
    track_path = os.path.join(temp_audio_dir, "track1.mp3")
    audio_player.play(track_path)  # play() doesn't return a value

    # Verify the state after playing
    assert audio_player.is_playing
    assert audio_player._hardware.get_current_track() == track_path
    assert audio_player._hardware.get_play_count(track_path) == 1


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_pause_resume_cycle(audio_player, temp_audio_dir):
    """Test the pause and resume methods through a full cycle."""
    track_path = os.path.join(temp_audio_dir, "track1.mp3")
    
    # Start playing
    audio_player.play(track_path)
    assert audio_player.is_playing
    assert not audio_player.is_paused
    
    # Pause
    audio_player.pause()
    assert not audio_player.is_playing
    assert audio_player.is_paused
    
    # Resume
    audio_player.resume()
    assert audio_player.is_playing
    assert not audio_player.is_paused
    
    # Pause again
    audio_player.pause()
    assert not audio_player.is_playing
    assert audio_player.is_paused
    
    # Stop while paused
    audio_player.stop()
    assert not audio_player.is_playing
    assert not audio_player.is_paused


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_stop_from_playing(audio_player, temp_audio_dir):
    """Test stopping playback from a playing state."""
    track_path = os.path.join(temp_audio_dir, "track1.mp3")
    
    # Start playing
    audio_player.play(track_path)
    assert audio_player.is_playing
    
    # Stop
    audio_player.stop()
    assert not audio_player.is_playing
    assert not audio_player.is_paused


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_volume_control(audio_player):
    """Test volume control capabilities."""
    # Set volume to 50%
    audio_player.set_volume(50)
    assert audio_player._hardware.get_volume() == 50
    
    # Set volume to maximum
    audio_player.set_volume(100)
    assert audio_player._hardware.get_volume() == 100
    
    # Set volume to minimum
    audio_player.set_volume(0)
    assert audio_player._hardware.get_volume() == 0
    
    # Try setting invalid volume (should be constrained)
    audio_player.set_volume(110)
    assert audio_player._hardware.get_volume() == 0  # Should not change from previous value


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_playlist_navigation(audio_player, sample_playlist):
    """Test playlist navigation (next, previous, play_track)."""
    # Set the playlist
    audio_player.set_playlist(sample_playlist)
    
    # Start with first track
    assert audio_player.play_track(0) is True
    assert audio_player._hardware.get_current_track_index() == 0
    assert audio_player.is_playing
    
    # Move to next track
    audio_player.next_track()  # next_track() doesn't return a value
    assert audio_player._hardware.get_current_track_index() == 1
    assert audio_player.is_playing
    
    # Move to next track again
    audio_player.next_track()  # next_track() doesn't return a value
    assert audio_player._hardware.get_current_track_index() == 2
    assert audio_player.is_playing
    
    # Try to move past the end
    audio_player.next_track()  # next_track() doesn't return a value
    # Verify we're still on the last track (can't go beyond)
    assert audio_player._hardware.get_current_track_index() == 2
    assert audio_player._hardware.get_current_track_index() == 2  # Should remain at the last track
    assert audio_player.is_playing
    
    # Move back
    audio_player.previous_track()  # previous_track() doesn't return a value
    # Verify we moved back to the previous track
    assert audio_player._hardware.get_current_track_index() == 1
    assert audio_player._hardware.get_current_track_index() == 1
    assert audio_player.is_playing
    
    # Move back again
    audio_player.previous_track()  # previous_track() doesn't return a value
    # Verify we moved back to the first track
    assert audio_player._hardware.get_current_track_index() == 0
    assert audio_player._hardware.get_current_track_index() == 0
    assert audio_player.is_playing
    
    # Try to move before the beginning
    audio_player.previous_track()  # previous_track() doesn't return a value
    # Verify we're still on the first track (can't go below 0)
    assert audio_player._hardware.get_current_track_index() == 0
    assert audio_player._hardware.get_current_track_index() == 0  # Should remain at the first track
    assert audio_player.is_playing
    
    # Jump to a specific track
    assert audio_player.play_track(2) is True
    assert audio_player._hardware.get_current_track_index() == 2
    assert audio_player.is_playing


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_track_completion(audio_player, temp_audio_dir):
    """Test detection of track completion."""
    track_path = os.path.join(temp_audio_dir, "track1.mp3")
    
    # Start playing
    audio_player.play(track_path)
    assert not audio_player.is_finished()
    
    # Simulate track finishing
    audio_player._hardware.simulate_track_finished()
    assert audio_player.is_finished()
    assert not audio_player.is_playing
    
    # Playing a new track should reset the finished state
    audio_player.play(track_path)
    assert not audio_player.is_finished()
    assert audio_player.is_playing


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_cleanup(audio_player, temp_audio_dir):
    """Test cleanup functionality."""
    track_path = os.path.join(temp_audio_dir, "track1.mp3")
    
    # Start playing
    audio_player.play(track_path)
    assert audio_player.is_playing
    
    # Clean up
    audio_player.cleanup()
    assert not audio_player.is_playing
    assert not audio_player.is_paused
    assert audio_player._hardware.get_current_track() is None


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_play_nonexistent_file(audio_player):
    """Test playing a nonexistent file (should still work in the test implementation)."""
    # Even non-existent files should "work" in our test implementation
    # as we're just testing the API interaction, not actual file operations
    audio_player.play("/nonexistent/file.mp3")  # play() doesn't return a value
    # Just verify that the state was updated correctly
    assert audio_player.is_playing
    assert audio_player.is_playing


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_repeated_state_changes(audio_player, temp_audio_dir):
    """Test multiple state transitions to verify stability."""
    track_path = os.path.join(temp_audio_dir, "track1.mp3")
    
    # State sequence: stop (initial) -> play -> pause -> resume -> stop -> play -> stop
    assert not audio_player.is_playing
    assert not audio_player.is_paused
    
    audio_player.play(track_path)
    assert audio_player.is_playing
    assert not audio_player.is_paused
    
    audio_player.pause()
    assert not audio_player.is_playing
    assert audio_player.is_paused
    
    audio_player.resume()
    assert audio_player.is_playing
    assert not audio_player.is_paused
    
    audio_player.stop()
    assert not audio_player.is_playing
    assert not audio_player.is_paused
    
    audio_player.play(track_path)
    assert audio_player.is_playing
    assert not audio_player.is_paused
    
    audio_player.stop()
    assert not audio_player.is_playing
    assert not audio_player.is_paused


@pytest.mark.audio
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_audio_player_playlist_exhaustion(audio_player, sample_playlist):
    """Test playing through an entire playlist."""
    # Set the playlist
    audio_player.set_playlist(sample_playlist)
    
    # Play all tracks sequentially
    audio_player.play_track(0)
    assert audio_player.is_playing
    assert audio_player._hardware.get_current_track_index() == 0
    
    # Mock track completion and advance
    audio_player._hardware.simulate_track_finished()
    assert audio_player.is_finished()
    
    audio_player.next_track()
    assert audio_player.is_playing
    assert audio_player._hardware.get_current_track_index() == 1
    
    # Mock track completion and advance
    audio_player._hardware.simulate_track_finished()
    assert audio_player.is_finished()
    
    audio_player.next_track()
    assert audio_player.is_playing
    assert audio_player._hardware.get_current_track_index() == 2
    
    # Mock track completion on last track
    audio_player._hardware.simulate_track_finished()
    assert audio_player.is_finished()
    
    # Try to advance past the end
    audio_player.next_track()  # next_track() doesn't return a value
    # Check if we're still on the last track (no advancement)
    assert audio_player._hardware.get_current_track_index() == 2
    assert audio_player._hardware.get_current_track_index() == 2  # Should remain at the last track


# --- Fallback Logic Tests (using MagicMock) ---

@pytest.mark.audio
@pytest.mark.timeout(5)
def test_ap_is_playing_fallback(audio_player_with_mock_hardware, mock_hardware_for_fallback_tests):
    """Test the is_playing property fallback to _is_playing."""
    # Ensure the primary attribute is present first, then remove it
    assert hasattr(mock_hardware_for_fallback_tests, 'is_playing'), "Precondition: mock_hardware should have is_playing"
    del mock_hardware_for_fallback_tests.is_playing
    mock_hardware_for_fallback_tests._is_playing = True
    
    assert audio_player_with_mock_hardware.is_playing is True
    
    mock_hardware_for_fallback_tests._is_playing = False
    assert audio_player_with_mock_hardware.is_playing is False


@pytest.mark.audio
@pytest.mark.timeout(5)
def test_ap_is_playing_default(audio_player_with_mock_hardware, mock_hardware_for_fallback_tests):
    """Test the is_playing property default when no attribute is available."""
    # Remove both primary and fallback attributes
    if hasattr(mock_hardware_for_fallback_tests, 'is_playing'):
        del mock_hardware_for_fallback_tests.is_playing
    if hasattr(mock_hardware_for_fallback_tests, '_is_playing'):
        del mock_hardware_for_fallback_tests._is_playing
        
    assert audio_player_with_mock_hardware.is_playing is False


@pytest.mark.audio
@pytest.mark.timeout(5)
def test_ap_is_paused_primary(audio_player_with_mock_hardware, mock_hardware_for_fallback_tests):
    """Test the is_paused property returns the hardware state via primary attribute."""
    mock_hardware_for_fallback_tests.is_paused = True
    assert audio_player_with_mock_hardware.is_paused is True
    
    mock_hardware_for_fallback_tests.is_paused = False
    assert audio_player_with_mock_hardware.is_paused is False


@pytest.mark.audio
@pytest.mark.timeout(5)
def test_ap_is_paused_default(audio_player_with_mock_hardware, mock_hardware_for_fallback_tests):
    """Test the is_paused property default when no attribute is available."""
    # AudioPlayer.is_paused doesn't have an _is_paused fallback, directly defaults if primary is missing
    if hasattr(mock_hardware_for_fallback_tests, 'is_paused'):
        del mock_hardware_for_fallback_tests.is_paused
        
    assert audio_player_with_mock_hardware.is_paused is False


@pytest.mark.audio
@pytest.mark.timeout(5)
def test_ap_is_finished_method_primary(audio_player_with_mock_hardware, mock_hardware_for_fallback_tests):
    """Test the is_finished method when hardware has the primary method."""
    mock_hardware_for_fallback_tests.is_finished = MagicMock(return_value=True)
    result = audio_player_with_mock_hardware.is_finished()
    mock_hardware_for_fallback_tests.is_finished.assert_called_once()
    assert result is True
    
    mock_hardware_for_fallback_tests.is_finished = MagicMock(return_value=False)
    result = audio_player_with_mock_hardware.is_finished()
    assert result is False


@pytest.mark.audio
@pytest.mark.timeout(5)
def test_ap_is_finished_fallback(audio_player_with_mock_hardware, mock_hardware_for_fallback_tests):
    """Test the is_finished method fallback to _is_finished method."""
    # Ensure the primary method is present first, then remove it
    assert hasattr(mock_hardware_for_fallback_tests, 'is_finished'), "Precondition: mock_hardware should have is_finished"
    del mock_hardware_for_fallback_tests.is_finished
    mock_hardware_for_fallback_tests._is_finished = MagicMock(return_value=True)
    
    result = audio_player_with_mock_hardware.is_finished()
    mock_hardware_for_fallback_tests._is_finished.assert_called_once()
    assert result is True
    
    mock_hardware_for_fallback_tests._is_finished = MagicMock(return_value=False)
    result = audio_player_with_mock_hardware.is_finished()
    assert result is False


@pytest.mark.audio
@pytest.mark.timeout(5)
def test_ap_is_finished_default(audio_player_with_mock_hardware, mock_hardware_for_fallback_tests):
    """Test the is_finished method default when no method is available."""
    # Remove both primary and fallback methods
    if hasattr(mock_hardware_for_fallback_tests, 'is_finished'):
        delattr(mock_hardware_for_fallback_tests, 'is_finished')
    if hasattr(mock_hardware_for_fallback_tests, '_is_finished'):
        delattr(mock_hardware_for_fallback_tests, '_is_finished')
    
    result = audio_player_with_mock_hardware.is_finished()
    assert result is False
