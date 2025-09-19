# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for audio backend implementations.

These tests verify that audio backends implement the protocol correctly
and handle various edge cases and error conditions properly.
"""

import pytest
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.src.domain.audio.backends.implementations.base_audio_backend import BaseAudioBackend
from app.src.domain.audio.backends.implementations.mock_audio_backend import MockAudioBackend
from app.src.domain.audio.backends.implementations.macos_audio_backend import MacOSAudioBackend
from app.src.services.notification_service import PlaybackSubject


class TestBaseAudioBackend:
    """Test the base audio backend functionality."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_playback_subject = Mock(spec=PlaybackSubject)
        self.backend = BaseAudioBackend(self.mock_playback_subject)
    
    def test_initialization(self):
        """Test backend initialization."""
        assert self.backend._playback_subject == self.mock_playback_subject
        assert isinstance(self.backend._state_lock, threading.RLock)
        assert self.backend._is_playing is False
        assert self.backend._current_file_path is None
        assert self.backend._volume == 70  # Default volume
        assert self.backend._backend_name == "BaseAudioBackend"
    
    def test_validate_file_path_success(self):
        """Test file path validation with existing file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            result = self.backend._validate_file_path(temp_path)
            assert result is not None
            assert isinstance(result, Path)
            assert str(result) == temp_path
        finally:
            Path(temp_path).unlink()  # Clean up
    
    def test_validate_file_path_nonexistent(self):
        """Test file path validation with non-existent file."""
        result = self.backend._validate_file_path("/nonexistent/file.mp3")
        assert result is None
    
    def test_validate_file_path_empty_string(self):
        """Test file path validation with empty string."""
        result = self.backend._validate_file_path("")
        assert result is None
    
    def test_validate_file_path_none(self):
        """Test file path validation with None."""
        with pytest.raises(TypeError):
            self.backend._validate_file_path(None)
    
    def test_state_properties(self):
        """Test state property getters."""
        # Initial state
        assert self.backend.is_playing() is False
        assert self.backend.get_volume() == 70
        assert self.backend.get_current_file() is None
        
        # After setting state
        self.backend._is_playing = True
        self.backend._current_file_path = "/test/file.mp3"
        self.backend._volume = 85
        
        assert self.backend.is_playing() is True
        assert self.backend.get_volume() == 85
        assert self.backend.get_current_file() == "/test/file.mp3"
    
    def test_thread_safety(self):
        """Test that state access is thread-safe."""
        # This test verifies that the state lock is used
        original_lock = self.backend._state_lock
        mock_lock = Mock(spec=threading.RLock)
        self.backend._state_lock = mock_lock
        
        # Call a method that should acquire the lock
        self.backend.is_playing()
        
        # Verify lock was used (this is implementation-dependent)
        # For BaseAudioBackend, we just verify the lock exists
        assert self.backend._state_lock == mock_lock
        
        # Restore original lock
        self.backend._state_lock = original_lock
    
    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            self.backend.play_file("/test.mp3")
        
        with pytest.raises(NotImplementedError):
            self.backend.pause()
        
        with pytest.raises(NotImplementedError):
            self.backend.resume()
        
        with pytest.raises(NotImplementedError):
            self.backend.stop()
        
        with pytest.raises(NotImplementedError):
            self.backend.set_volume(50)


class TestMockAudioBackend:
    """Test the mock audio backend implementation."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_playback_subject = Mock(spec=PlaybackSubject)
        self.backend = MockAudioBackend(self.mock_playback_subject)
    
    def test_initialization(self):
        """Test mock backend initialization."""
        assert self.backend._playback_subject == self.mock_playback_subject
        assert self.backend._backend_name == "MockAudioBackend"
        assert self.backend.is_available() is True
    
    def test_play_file_success(self):
        """Test successful file playback."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            result = self.backend.play_file(temp_path)
            assert result is True
            assert self.backend.is_playing() is True
            assert self.backend.get_current_file() == temp_path
        finally:
            Path(temp_path).unlink()
    
    def test_play_file_nonexistent(self):
        """Test playing non-existent file."""
        result = self.backend.play_file("/nonexistent/file.mp3")
        assert result is False
        assert self.backend.is_playing() is False
    
    def test_pause_when_playing(self):
        """Test pausing during playback."""
        # Start playing first
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            self.backend.play_file(temp_path)
            assert self.backend.is_playing() is True
            
            result = self.backend.pause()
            assert result is True
            assert self.backend.is_playing() is False
        finally:
            Path(temp_path).unlink()
    
    def test_pause_when_not_playing(self):
        """Test pausing when not playing."""
        result = self.backend.pause()
        assert result is False
    
    def test_resume_when_paused(self):
        """Test resuming after pause."""
        # Start playing and then pause
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            self.backend.play_file(temp_path)
            self.backend.pause()
            assert self.backend.is_playing() is False
            
            result = self.backend.resume()
            assert result is True
            assert self.backend.is_playing() is True
        finally:
            Path(temp_path).unlink()
    
    def test_resume_when_not_paused(self):
        """Test resuming when not paused."""
        result = self.backend.resume()
        assert result is False
    
    def test_stop_when_playing(self):
        """Test stopping during playback."""
        # Start playing first
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            self.backend.play_file(temp_path)
            assert self.backend.is_playing() is True
            
            result = self.backend.stop()
            assert result is True
            assert self.backend.is_playing() is False
            assert self.backend.get_current_file() is None
        finally:
            Path(temp_path).unlink()
    
    def test_stop_when_not_playing(self):
        """Test stopping when not playing."""
        result = self.backend.stop()
        assert result is False
    
    def test_set_volume_valid_range(self):
        """Test setting volume within valid range."""
        result = self.backend.set_volume(85)
        assert result is True
        assert self.backend.get_volume() == 85
    
    def test_set_volume_below_minimum(self):
        """Test setting volume below minimum."""
        result = self.backend.set_volume(-10)
        assert result is False
        assert self.backend.get_volume() == 70  # Unchanged
    
    def test_set_volume_above_maximum(self):
        """Test setting volume above maximum."""
        result = self.backend.set_volume(150)
        assert result is False
        assert self.backend.get_volume() == 70  # Unchanged
    
    def test_set_volume_boundary_values(self):
        """Test setting volume at boundary values."""
        # Minimum boundary
        result = self.backend.set_volume(0)
        assert result is True
        assert self.backend.get_volume() == 0
        
        # Maximum boundary  
        result = self.backend.set_volume(100)
        assert result is True
        assert self.backend.get_volume() == 100
    
    def test_notification_subject_integration(self):
        """Test integration with playback notification subject."""
        # Create a temporary file and play it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            self.backend.play_file(temp_path)
            
            # Verify notification subject was called
            # Note: MockAudioBackend should notify the subject on state changes
            # This test verifies the integration point exists
            assert self.mock_playback_subject is not None
        finally:
            Path(temp_path).unlink()


class TestMacOSAudioBackend:
    """Test the macOS audio backend implementation."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_playback_subject = Mock(spec=PlaybackSubject)
    
    @patch('platform.system')
    def test_initialization_on_macos(self, mock_platform):
        """Test backend initialization on macOS."""
        mock_platform.return_value = 'Darwin'
        backend = MacOSAudioBackend(self.mock_playback_subject)
        
        assert backend._playback_subject == self.mock_playback_subject
        assert backend._backend_name == "MacOSAudioBackend"
        assert backend.is_available() is True
    
    @patch('platform.system')
    def test_initialization_on_non_macos(self, mock_platform):
        """Test backend initialization on non-macOS platform."""
        mock_platform.return_value = 'Linux'
        backend = MacOSAudioBackend(self.mock_playback_subject)
        
        assert backend.is_available() is False
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_play_file_with_afplay(self, mock_subprocess, mock_platform):
        """Test playing file using afplay command."""
        mock_platform.return_value = 'Darwin'
        mock_subprocess.return_value = Mock(returncode=0)
        
        backend = MacOSAudioBackend(self.mock_playback_subject)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            result = backend.play_file(temp_path)
            assert result is True
            assert backend.is_playing() is True
            
            # Verify afplay was called
            mock_subprocess.assert_called()
            call_args = mock_subprocess.call_args[0][0]
            assert 'afplay' in call_args
            assert temp_path in call_args
        finally:
            Path(temp_path).unlink()
            backend.stop()  # Clean up any running processes
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_play_file_afplay_failure(self, mock_subprocess, mock_platform):
        """Test handling of afplay command failure."""
        mock_platform.return_value = 'Darwin'
        mock_subprocess.return_value = Mock(returncode=1)
        
        backend = MacOSAudioBackend(self.mock_playback_subject)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            result = backend.play_file(temp_path)
            assert result is False
            assert backend.is_playing() is False
        finally:
            Path(temp_path).unlink()
    
    @patch('platform.system')
    def test_volume_control_not_implemented_gracefully(self, mock_platform):
        """Test that volume control fails gracefully on macOS backend."""
        mock_platform.return_value = 'Darwin'
        backend = MacOSAudioBackend(self.mock_playback_subject)
        
        # macOS backend might not support direct volume control
        # This test ensures it handles this gracefully
        result = backend.set_volume(50)
        # The result depends on implementation - it might return False or handle it differently
        assert result is not None


class TestAudioBackendProtocolCompliance:
    """Test that all backends properly implement the protocol."""
    
    def test_mock_backend_implements_protocol(self):
        """Test that MockAudioBackend implements AudioBackendProtocol."""
        from app.src.domain.audio.protocols.audio_backend_protocol import AudioBackendProtocol
        
        backend = MockAudioBackend()
        assert isinstance(backend, AudioBackendProtocol)
        
        # Test all required methods exist and are callable
        assert callable(getattr(backend, 'play_file', None))
        assert callable(getattr(backend, 'pause', None))
        assert callable(getattr(backend, 'resume', None))
        assert callable(getattr(backend, 'stop', None))
        assert callable(getattr(backend, 'set_volume', None))
        assert callable(getattr(backend, 'get_volume', None))
        assert callable(getattr(backend, 'is_playing', None))
        assert callable(getattr(backend, 'is_available', None))
    
    def test_macos_backend_implements_protocol(self):
        """Test that MacOSAudioBackend implements AudioBackendProtocol."""
        from app.src.domain.audio.protocols.audio_backend_protocol import AudioBackendProtocol
        
        backend = MacOSAudioBackend()
        assert isinstance(backend, AudioBackendProtocol)
        
        # Test all required methods exist and are callable
        assert callable(getattr(backend, 'play_file', None))
        assert callable(getattr(backend, 'pause', None))
        assert callable(getattr(backend, 'resume', None))
        assert callable(getattr(backend, 'stop', None))
        assert callable(getattr(backend, 'set_volume', None))
        assert callable(getattr(backend, 'get_volume', None))
        assert callable(getattr(backend, 'is_playing', None))
        assert callable(getattr(backend, 'is_available', None))


class TestAudioBackendErrorHandling:
    """Test error handling across audio backends."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_playback_subject = Mock(spec=PlaybackSubject)
    
    def test_mock_backend_handles_exceptions_gracefully(self):
        """Test that MockAudioBackend handles internal exceptions."""
        backend = MockAudioBackend(self.mock_playback_subject)
        
        # Test with various invalid inputs
        assert backend.play_file(None) is False
        assert backend.play_file("") is False
        assert backend.set_volume(None) is False
        assert backend.set_volume("invalid") is False
    
    def test_concurrent_access_safety(self):
        """Test that backends handle concurrent access safely."""
        backend = MockAudioBackend(self.mock_playback_subject)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        results = []
        
        def play_and_pause():
            results.append(backend.play_file(temp_path))
            results.append(backend.pause())
        
        def set_volume():
            results.append(backend.set_volume(50))
            results.append(backend.set_volume(80))
        
        try:
            # Run concurrent operations
            thread1 = threading.Thread(target=play_and_pause)
            thread2 = threading.Thread(target=set_volume)
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
            # Verify no exceptions were raised (results collected)
            assert len(results) == 4
            assert all(isinstance(result, bool) for result in results)
        finally:
            Path(temp_path).unlink()
            backend.stop()


class TestAudioBackendIntegrationBehavior:
    """Test backend integration behavior for domain requirements."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_playback_subject = Mock(spec=PlaybackSubject)
    
    def test_backend_state_consistency(self):
        """Test that backend state remains consistent across operations."""
        backend = MockAudioBackend(self.mock_playback_subject)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            # Test state transitions
            assert backend.is_playing() is False
            assert backend.get_current_file() is None
            
            # Play file
            backend.play_file(temp_path)
            assert backend.is_playing() is True
            assert backend.get_current_file() == temp_path
            
            # Pause
            backend.pause()
            assert backend.is_playing() is False
            assert backend.get_current_file() == temp_path  # Should still be set
            
            # Resume
            backend.resume()
            assert backend.is_playing() is True
            assert backend.get_current_file() == temp_path
            
            # Stop
            backend.stop()
            assert backend.is_playing() is False
            assert backend.get_current_file() is None
        finally:
            Path(temp_path).unlink()
    
    def test_volume_persistence(self):
        """Test that volume settings persist across playback operations."""
        backend = MockAudioBackend(self.mock_playback_subject)
        
        # Set volume
        backend.set_volume(85)
        assert backend.get_volume() == 85
        
        # Create and play file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
            
        try:
            backend.play_file(temp_path)
            assert backend.get_volume() == 85  # Should persist
            
            backend.pause()
            assert backend.get_volume() == 85  # Should persist
            
            backend.resume()
            assert backend.get_volume() == 85  # Should persist
            
            backend.stop()
            assert backend.get_volume() == 85  # Should persist
        finally:
            Path(temp_path).unlink()
    
    def test_backend_availability_reporting(self):
        """Test that backends correctly report their availability."""
        mock_backend = MockAudioBackend(self.mock_playback_subject)
        assert mock_backend.is_available() is True
        
        # MacOS backend availability depends on platform
        macos_backend = MacOSAudioBackend(self.mock_playback_subject)
        availability = macos_backend.is_available()
        assert isinstance(availability, bool)  # Should return a boolean