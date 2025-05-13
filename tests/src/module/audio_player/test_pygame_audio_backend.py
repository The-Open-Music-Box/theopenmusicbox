"""
Tests for the PygameAudioBackend class.

These tests verify the functionality of the Pygame audio backend implementation.
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from pathlib import Path
import pygame # Import pygame for event constants # Keep this for pygame.USEREVENT if not mocked below

from app.src.module.audio_player.pygame_audio_backend import PygameAudioBackend

@pytest.fixture
def mock_pygame_objects():
    """Create a comprehensive mock for the entire pygame module and its submodules."""
    pg_mock = MagicMock() # Mock the top-level pygame module without using spec

    # Mock pygame.mixer and its music object
    pg_mock.mixer = MagicMock()
    pg_mock.mixer.init = MagicMock(return_value=None)
    pg_mock.mixer.quit = MagicMock(return_value=None)
    pg_mock.mixer.get_init.return_value = True # Assume mixer is initialized after call

    pg_mock.mixer.music = MagicMock()
    pg_mock.mixer.music.load = MagicMock(return_value=None)
    pg_mock.mixer.music.play = MagicMock(return_value=None)
    pg_mock.mixer.music.pause = MagicMock(return_value=None)
    pg_mock.mixer.music.unpause = MagicMock(return_value=None)
    pg_mock.mixer.music.stop = MagicMock(return_value=None)
    pg_mock.mixer.music.rewind = MagicMock(return_value=None)
    pg_mock.mixer.music.set_volume = MagicMock(return_value=None)
    pg_mock.mixer.music.get_volume = MagicMock(return_value=0.5)  # Default volume
    pg_mock.mixer.music.get_busy = MagicMock(return_value=False) # Default not playing
    pg_mock.mixer.music.set_pos = MagicMock(return_value=None)
    pg_mock.mixer.music.set_endevent = MagicMock(return_value=None)

    # Mock pygame.event
    pg_mock.event = MagicMock()
    pg_mock.event.get = MagicMock(return_value=[]) # Default no events
    pg_mock.event.clear = MagicMock(return_value=None)

    # Mock pygame constants and general functions
    pg_mock.USEREVENT = pygame.USEREVENT # Use the real constant if available, or mock to an int
    pg_mock.init = MagicMock(return_value=None)
    pg_mock.quit = MagicMock(return_value=None)

    # Mock pygame.display (if any part of it is used, e.g. display.quit)
    pg_mock.display = MagicMock()
    pg_mock.display.quit = MagicMock(return_value=None)

    return pg_mock

@pytest.fixture
def mock_mutagen_mp3():
    """Create a mock for mutagen.mp3.MP3."""
    mock_mp3 = MagicMock()
    mock_mp3_instance = MagicMock()
    mock_mp3_instance.info.length = 180.0 # Mock duration
    mock_mp3.return_value = mock_mp3_instance
    return mock_mp3

@pytest.fixture
def pygame_audio_backend(mock_pygame_objects, mock_mutagen_mp3):
    """Create a PygameAudioBackend instance with mock dependencies."""
    # Patch the pygame module and MP3 class at the module level
    with patch('app.src.module.audio_player.pygame_audio_backend.pygame', mock_pygame_objects), \
         patch('app.src.module.audio_player.pygame_audio_backend.MP3', mock_mutagen_mp3):
        # Create a new instance with the patched modules
        backend = PygameAudioBackend()
        # Set initialized to True to avoid initialization issues
        backend._initialized = True
        # Set the music end event
        backend._music_end_event = mock_pygame_objects.USEREVENT + 1
        yield backend


@pytest.mark.audio
def test_pygame_audio_backend_initialize(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test initialization of PygameAudioBackend."""
    # Patch os.name and os.uname for consistent testing of initialization paths
    with patch('app.src.module.audio_player.pygame_audio_backend.os.name', 'posix'), \
         patch('app.src.module.audio_player.pygame_audio_backend.os.uname', MagicMock(return_value=MagicMock(machine='x86_64', sysname='Darwin'))):
        pygame_audio_backend._initialized = False # Reset before test
        result = pygame_audio_backend.initialize()

    assert result is True, "initialize() should return True on success"
    assert pygame_audio_backend._initialized is True, "backend should be marked as initialized"

    mock_pygame_objects.mixer.init.assert_called_once_with() # Default init for macOS
    mock_pygame_objects.init.assert_called_once() # Check that global pygame.init() was called
    mock_pygame_objects.mixer.music.set_endevent.assert_called_once_with(mock_pygame_objects.USEREVENT + 1)
    mock_pygame_objects.mixer.music.set_volume.assert_called_once_with(0.5) # Default volume 50%

@pytest.mark.audio
def test_pygame_audio_backend_shutdown(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test shutting down PygameAudioBackend."""
    # We need to simulate a successful initialization for shutdown to proceed
    pygame_audio_backend._initialized = True
    # Ensure mixer.quit and pygame.quit are attributes of the mock_pygame_objects
    mock_pygame_objects.mixer.quit = MagicMock()
    mock_pygame_objects.quit = MagicMock()

    result = pygame_audio_backend.shutdown()
    assert result is True
    mock_pygame_objects.mixer.quit.assert_called_once()
    mock_pygame_objects.quit.assert_called_once()


@pytest.mark.audio
def test_pygame_audio_backend_load(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test loading an audio file."""
    pygame_audio_backend._initialized = True # Assume initialized
    file_path = Path("/tmp/test.mp3")
    result = pygame_audio_backend.load(file_path)
    assert result is True
    mock_pygame_objects.mixer.music.load.assert_called_once_with(str(file_path))

@pytest.mark.audio
def test_pygame_audio_backend_play(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test playing an audio file."""
    pygame_audio_backend._initialized = True # Assume initialized
    pygame_audio_backend._current_file = Path("/tmp/test.mp3") # Assume loaded
    mock_pygame_objects.mixer.get_init.return_value = True

    result = pygame_audio_backend.play()
    assert result is True
    mock_pygame_objects.mixer.music.play.assert_called_once()

@pytest.mark.audio
def test_pygame_audio_backend_pause_resume(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test pausing and resuming playback."""
    pygame_audio_backend._initialized = True
    pygame_audio_backend._current_file = Path("/tmp/test.mp3")
    mock_pygame_objects.mixer.get_init.return_value = True

    # Simulate playing for pause
    mock_pygame_objects.mixer.music.get_busy.return_value = True
    pygame_audio_backend._start_time = time.time() # Need a start time for get_position

    result_pause = pygame_audio_backend.pause()
    assert result_pause is True
    mock_pygame_objects.mixer.music.pause.assert_called_once()

    # Simulate paused for resume
    mock_pygame_objects.mixer.music.get_busy.return_value = False
    result_resume = pygame_audio_backend.resume()
    assert result_resume is True
    mock_pygame_objects.mixer.music.unpause.assert_called_once()

@pytest.mark.audio
def test_pygame_audio_backend_stop(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test stopping playback."""
    pygame_audio_backend._initialized = True
    mock_pygame_objects.mixer.get_init.return_value = True

    result = pygame_audio_backend.stop()
    assert result is True
    mock_pygame_objects.mixer.music.stop.assert_called_once()

@pytest.mark.audio
def test_pygame_audio_backend_set_volume(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test setting the volume."""
    pygame_audio_backend._initialized = True
    mock_pygame_objects.mixer.get_init.return_value = True

    result = pygame_audio_backend.set_volume(75)
    assert result is True
    mock_pygame_objects.mixer.music.set_volume.assert_called_with(0.75)

@pytest.mark.audio
def test_pygame_audio_backend_get_volume(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test getting the volume."""
    pygame_audio_backend._initialized = True
    mock_pygame_objects.mixer.get_init.return_value = True
    mock_pygame_objects.mixer.music.get_volume.return_value = 0.6

    volume = pygame_audio_backend.get_volume()
    assert volume == 60

@pytest.mark.audio
def test_pygame_audio_backend_is_playing(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test checking if audio is playing."""
    pygame_audio_backend._initialized = True
    mock_pygame_objects.mixer.get_init.return_value = True

    mock_pygame_objects.mixer.music.get_busy.return_value = True
    assert pygame_audio_backend.is_playing() is True

    mock_pygame_objects.mixer.music.get_busy.return_value = False
    assert pygame_audio_backend.is_playing() is False

@pytest.mark.audio
def test_pygame_audio_backend_register_end_event_callback(pygame_audio_backend): # No mock_pygame_objects needed if only setting attribute
    """Test registering an end event callback."""
    pygame_audio_backend._initialized = True # Assume initialized
    callback = MagicMock()
    result = pygame_audio_backend.register_end_event_callback(callback)
    assert result is True
    assert pygame_audio_backend._end_event_callback == callback

@pytest.mark.audio
def test_pygame_audio_backend_get_duration(pygame_audio_backend, mock_mutagen_mp3): # mock_mutagen_mp3 is still fine
    """Test getting track duration."""
    pygame_audio_backend._initialized = True # Assume initialized
    file_path = Path("/tmp/test.mp3")
    duration = pygame_audio_backend.get_duration(file_path)
    assert duration == 180.0
    mock_mutagen_mp3.assert_called_once_with(str(file_path))

    # Test caching
    mock_mutagen_mp3.reset_mock()
    duration_cached = pygame_audio_backend.get_duration(file_path)
    assert duration_cached == 180.0
    mock_mutagen_mp3.assert_not_called() # Should use cached value

@pytest.mark.audio
def test_pygame_audio_backend_process_events(pygame_audio_backend, mock_pygame_objects): # Use mock_pygame_objects
    """Test processing pygame events for track end."""
    # Patch pygame at the module level for this specific test
    with patch('app.src.module.audio_player.pygame_audio_backend.pygame', mock_pygame_objects):
        pygame_audio_backend._initialized = True # Assume initialized
        # Need to set _music_end_event as it's done in initialize()
        pygame_audio_backend._music_end_event = mock_pygame_objects.USEREVENT + 1
        callback = MagicMock()
        pygame_audio_backend.register_end_event_callback(callback)

        # Simulate a track end event
        end_event = MagicMock()
        end_event.type = pygame_audio_backend._music_end_event
        mock_pygame_objects.event.get.return_value = [end_event]

        pygame_audio_backend.process_events()
        callback.assert_called_once()
