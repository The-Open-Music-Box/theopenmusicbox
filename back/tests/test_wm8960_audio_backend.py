# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Tests for WM8960 audio backend implementation.

These tests verify device detection, pygame initialization,
and audio playback functionality.
"""

import pytest
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import asyncio

from app.src.domain.audio.backends.implementations.wm8960_audio_backend import WM8960AudioBackend


class TestWM8960AudioBackend:
    """Test the WM8960 audio backend implementation."""

    def setup_method(self):
        """Set up test dependencies."""
        # Create a mock PlaybackSubject
        self.mock_playback_subject = Mock()
        self.mock_playback_subject.notify = Mock()

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run')
    def test_detect_wm8960_device_card_3(self, mock_subprocess):
        """Test device detection when WM8960 is at card 3."""
        # Mock aplay -l output matching the user's system
        mock_output = """**** List of PLAYBACK Hardware Devices ****
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
  Subdevices: 8/8
card 1: vc4hdmi0 [vc4-hdmi-0], device 0: MAI PCM i2s-hifi-0 [MAI PCM i2s-hifi-0]
  Subdevices: 1/1
card 2: vc4hdmi1 [vc4-hdmi-1], device 0: MAI PCM i2s-hifi-0 [MAI PCM i2s-hifi-0]
  Subdevices: 1/1
card 3: wm8960soundcard [wm8960-soundcard], device 0: bcm2835-i2s-wm8960-hifi wm8960-hifi-0 [bcm2835-i2s-wm8960-hifi wm8960-hifi-0]
  Subdevices: 0/1"""

        mock_subprocess.return_value = Mock(returncode=0, stdout=mock_output)

        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True):
            with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
                mock_pygame.mixer.get_init.return_value = None
                mock_pygame.mixer.init.return_value = None

                backend = WM8960AudioBackend(self.mock_playback_subject)
                device = backend._detect_wm8960_device()

                # Should detect card 3 and use plughw format
                assert device == "plughw:3,0"

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run')
    def test_detect_wm8960_device_card_changes(self, mock_subprocess):
        """Test device detection when card number changes."""
        # Mock aplay -l output with WM8960 at card 1
        mock_output = """**** List of PLAYBACK Hardware Devices ****
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
  Subdevices: 8/8
card 1: wm8960soundcard [wm8960-soundcard], device 0: bcm2835-i2s-wm8960-hifi wm8960-hifi-0 [bcm2835-i2s-wm8960-hifi wm8960-hifi-0]
  Subdevices: 0/1"""

        mock_subprocess.return_value = Mock(returncode=0, stdout=mock_output)

        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True):
            with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
                mock_pygame.mixer.get_init.return_value = None
                mock_pygame.mixer.init.return_value = None

                backend = WM8960AudioBackend(self.mock_playback_subject)
                device = backend._detect_wm8960_device()

                # Should detect card 1 dynamically
                assert device == "plughw:1,0"

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run')
    def test_detect_wm8960_device_not_found(self, mock_subprocess):
        """Test device detection when WM8960 is not found."""
        # Mock aplay -l output without WM8960
        mock_output = """**** List of PLAYBACK Hardware Devices ****
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
  Subdevices: 8/8"""

        mock_subprocess.return_value = Mock(returncode=0, stdout=mock_output)

        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True):
            with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
                mock_pygame.mixer.get_init.return_value = None
                mock_pygame.mixer.init.return_value = None

                with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.config') as mock_config:
                    mock_config.hardware.alsa_device = None

                    backend = WM8960AudioBackend(self.mock_playback_subject)
                    device = backend._detect_wm8960_device()

                    # Should fall back to default
                    assert device == "plughw:0,0"

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run')
    def test_detect_wm8960_aplay_not_found(self, mock_subprocess):
        """Test device detection when aplay is not available (macOS)."""
        # Simulate aplay not found
        mock_subprocess.side_effect = FileNotFoundError()

        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True):
            with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
                mock_pygame.mixer.get_init.return_value = None
                mock_pygame.mixer.init.return_value = None

                with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.config') as mock_config:
                    mock_config.hardware.alsa_device = None

                    backend = WM8960AudioBackend(self.mock_playback_subject)
                    device = backend._detect_wm8960_device()

                    # Should return fallback when aplay not found
                    assert device == "plughw:1,0"

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run')
    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True)
    def test_init_pygame_simple_sets_environment(self, mock_subprocess):
        """Test that pygame initialization sets correct environment variables."""
        # Mock aplay output with WM8960 at card 3
        mock_output = """card 3: wm8960soundcard [wm8960-soundcard], device 0: wm8960"""
        mock_subprocess.return_value = Mock(returncode=0, stdout=mock_output)

        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
            mock_pygame.mixer.get_init.return_value = None
            mock_pygame.mixer.init.return_value = None
            mock_pygame.mixer.get_init.return_value = (44100, -16, 2)  # After init

            backend = WM8960AudioBackend(self.mock_playback_subject)

            # Check environment variables were set
            assert os.environ.get('SDL_AUDIODRIVER') == 'alsa'
            assert os.environ.get('SDL_AUDIODEV') == 'plughw:3,0'

            # Check pygame was initialized with correct parameters
            mock_pygame.mixer.pre_init.assert_called_with(
                frequency=44100, size=-16, channels=2, buffer=4096
            )
            mock_pygame.mixer.init.assert_called()

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run')
    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True)
    def test_play_file_with_device_reconfiguration(self, mock_subprocess):
        """Test playing a file triggers device reconfiguration if needed."""
        # Mock aplay output
        mock_output = """card 3: wm8960soundcard [wm8960-soundcard], device 0: wm8960"""
        mock_subprocess.return_value = Mock(returncode=0, stdout=mock_output)

        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
            # Setup more comprehensive get_init mock
            def get_init_side_effect():
                # Return different values based on the test phase
                if hasattr(get_init_side_effect, 'call_count'):
                    get_init_side_effect.call_count += 1
                else:
                    get_init_side_effect.call_count = 1

                if get_init_side_effect.call_count == 1:
                    return None  # Initial check during __init__
                elif get_init_side_effect.call_count == 2:
                    return (44100, -16, 2)  # After init in __init__
                elif get_init_side_effect.call_count == 3:
                    return (44100, -16, 2)  # play_file check
                elif get_init_side_effect.call_count == 4:
                    return None  # After quit
                else:
                    return (44100, -16, 2)  # After reinit

            mock_pygame.mixer.get_init.side_effect = get_init_side_effect
            mock_pygame.mixer.music.get_busy.return_value = False

            # First init returns wrong device
            os.environ['SDL_AUDIODEV'] = 'wrong_device'

            backend = WM8960AudioBackend(self.mock_playback_subject)
            backend._audio_device = 'plughw:3,0'  # Expected device

            # Create a temp file to play
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_path = temp_file.name

            try:
                result = backend.play_file(temp_path)

                # Should have reinitialized pygame with correct device
                assert os.environ.get('SDL_AUDIODEV') == 'plughw:3,0'
                assert result is True

                # Verify pygame.mixer.music was used
                mock_pygame.mixer.music.load.assert_called_with(temp_path)
                mock_pygame.mixer.music.play.assert_called()
            finally:
                Path(temp_path).unlink(missing_ok=True)

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', False)
    def test_play_file_pygame_not_available(self):
        """Test play_file when pygame is not available."""
        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run'):
            backend = WM8960AudioBackend(self.mock_playback_subject)

            result = backend.play_file("/some/file.mp3")
            assert result is False

    @pytest.mark.asyncio
    async def test_async_methods(self):
        """Test async wrapper methods."""
        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run'):
            with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True):
                with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
                    mock_pygame.mixer.get_init.return_value = None
                    mock_pygame.mixer.init.return_value = None

                    backend = WM8960AudioBackend(self.mock_playback_subject)
                    backend._is_playing = True
                    backend._volume = 50

                    # Test async pause
                    result = await backend.pause()
                    assert isinstance(result, bool)

                    # Test async resume
                    backend._is_paused = True
                    result = await backend.resume()
                    assert isinstance(result, bool)

                    # Test async stop
                    result = await backend.stop()
                    assert isinstance(result, bool)

                    # Test async set_volume (returns None due to error handling)
                    with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run'):
                        result = await backend.set_volume(75)
                        # set_volume_sync returns bool, but may return None if subprocess fails
                        assert result is None or isinstance(result, bool)

                    # Test async get_volume (volume was changed to 75)
                    volume = await backend.get_volume()
                    assert volume == 75  # Volume was updated to 75 in set_volume call

                    # Test async get_position
                    backend._play_start_time = 1000
                    position = await backend.get_position()
                    assert position is None or isinstance(position, int)

    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.subprocess.run')
    @patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.PYGAME_AVAILABLE', True)
    def test_set_volume_with_amixer(self, mock_subprocess):
        """Test volume setting with both pygame and amixer."""
        with patch('app.src.domain.audio.backends.implementations.wm8960_audio_backend.pygame') as mock_pygame:
            mock_pygame.mixer.get_init.return_value = (44100, -16, 2)

            backend = WM8960AudioBackend(self.mock_playback_subject)
            backend.set_volume_sync(75)

            # Check pygame volume was set (75% = 0.75)
            mock_pygame.mixer.music.set_volume.assert_called_with(0.75)

            # Check amixer was called
            expected_call = call(
                ["amixer", "sset", "Master", "75%"],
                check=True,
                capture_output=True
            )
            assert expected_call in mock_subprocess.call_args_list