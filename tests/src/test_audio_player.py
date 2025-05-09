import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from pathlib import Path
from unittest.mock import MagicMock

from app.src.module.audio_player.audio_mock import MockAudioPlayer
from app.src.module.audio_player.audio_hardware import AudioPlayerHardware
from app.src.model.playlist import Playlist
from app.src.model.track import Track


def test_mock_player_implements_protocol():
    """Test that MockAudioPlayer correctly implements the AudioPlayerHardware protocol"""
    # Create a mock player
    mock_player = MockAudioPlayer()
    
    # Check that it's an instance of the protocol
    assert isinstance(mock_player, AudioPlayerHardware)
    
    # Verify all required protocol methods exist
    assert hasattr(mock_player, 'play')
    assert hasattr(mock_player, 'pause')
    assert hasattr(mock_player, 'resume')
    assert hasattr(mock_player, 'stop')
    assert hasattr(mock_player, 'set_volume')
    assert hasattr(mock_player, 'cleanup')
    assert hasattr(mock_player, 'set_playlist')
    assert hasattr(mock_player, 'next_track')
    assert hasattr(mock_player, 'previous_track')
    assert hasattr(mock_player, 'play_track')
    
    # Check properties
    assert hasattr(mock_player, 'is_paused')
    assert hasattr(mock_player, 'is_playing')


def test_mock_player_play_method():
    """Test the newly added play method"""
    # Create a mock player
    mock_subject = MagicMock()
    mock_player = MockAudioPlayer(playback_subject=mock_subject)
    
    # Test initial state
    assert not mock_player.is_playing
    assert not mock_player.is_paused
    
    # Test play method
    test_track = "/path/to/test_track.mp3"
    mock_player.play(test_track)
    
    # Verify state changes
    assert mock_player.is_playing
    assert not mock_player.is_paused
    
    # Verify notification was sent
    mock_subject.notify_playback_status.assert_called_once()


def test_mock_player_playlist_operations():
    """Test playlist operations"""
    # Create a mock player
    mock_subject = MagicMock()
    mock_player = MockAudioPlayer(playback_subject=mock_subject)
    
    # Create a test playlist
    tracks = [
        Track(number=1, filename="track1.mp3", path=Path("/path/to/track1.mp3"), title="Track 1"),
        Track(number=2, filename="track2.mp3", path=Path("/path/to/track2.mp3"), title="Track 2"),
        Track(number=3, filename="track3.mp3", path=Path("/path/to/track3.mp3"), title="Track 3")
    ]
    playlist = Playlist(name="Test Playlist", tracks=tracks)
    
    # Set the playlist
    result = mock_player.set_playlist(playlist)
    assert result is True
    
    # Verify first track is playing
    assert mock_player.is_playing
    
    # Test next_track
    mock_player.next_track()
    mock_subject.notify_playback_status.assert_called()
    
    # Test previous_track
    mock_player.previous_track()
    
    # Test pause/resume
    mock_player.pause()
    assert not mock_player.is_playing
    assert mock_player.is_paused
    
    mock_player.resume()
    assert mock_player.is_playing
    assert not mock_player.is_paused
    
    # Test stop
    mock_player.stop()
    assert not mock_player.is_playing
    assert not mock_player.is_paused


def test_mock_player_volume_control():
    """Test volume control"""
    mock_player = MockAudioPlayer()
    
    # Test default volume - using protected member for testing only
    # pylint: disable=protected-access
    assert mock_player._volume == 50
    
    # Test setting volume
    mock_player.set_volume(75)
    assert mock_player._volume == 75
    
    # Test bounds
    mock_player.set_volume(150)
    assert mock_player._volume == 100  # Should be capped at 100
    
    mock_player.set_volume(-10)
    assert mock_player._volume == 0  # Should be capped at 0
    # pylint: enable=protected-access
