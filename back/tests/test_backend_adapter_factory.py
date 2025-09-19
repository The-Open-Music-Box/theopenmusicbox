# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Tests for BackendAdapter and AudioDomainFactory to prevent None backend issues."""

import os
import sys
import pytest
from unittest.mock import patch, Mock

from app.src.domain.audio.factory import AudioDomainFactory
from app.src.domain.audio.backends.backend_adapter import BackendAdapter
from app.src.domain.audio.protocols.audio_backend_protocol import AudioBackendProtocol


class TestBackendAdapterErrorPrevention:
    """Tests to prevent BackendAdapter from wrapping None backends."""

    def test_backend_adapter_rejects_none_backend(self):
        """Test that BackendAdapter properly handles None backend."""
        # This test prevents the original issue where None was passed to BackendAdapter
        adapter = BackendAdapter(None)

        # The adapter should gracefully handle None backend
        result = adapter.play_file("/path/to/test.mp3")

        # Should return False and not crash
        assert result is False

        # Other methods should also handle None gracefully
        assert adapter.is_playing is False
        assert adapter.is_paused is False
        assert adapter.get_position() == 0.0

    def test_backend_adapter_with_valid_backend(self):
        """Test that BackendAdapter works correctly with valid backend."""
        mock_backend = Mock()
        mock_backend.play_file.return_value = True
        mock_backend.is_playing = True

        adapter = BackendAdapter(mock_backend)

        result = adapter.play_file("/path/to/test.mp3")

        assert result is True
        mock_backend.play_file.assert_called_once_with("/path/to/test.mp3")


class TestAudioDomainFactoryDefaultBackend:
    """Tests to ensure AudioDomainFactory always creates valid backends."""

    @patch.dict(os.environ, {"USE_MOCK_HARDWARE": "true"})
    def test_create_default_backend_with_mock_hardware(self):
        """Test that factory creates mock backend when USE_MOCK_HARDWARE=true."""
        backend = AudioDomainFactory.create_default_backend()

        assert backend is not None
        assert hasattr(backend, 'play_file'), "Backend should have play_file method"
        assert hasattr(backend, 'is_playing'), "Backend should have is_playing property"

        # Should be able to call play_file without error
        result = backend.play_file("/path/to/test.mp3")
        assert isinstance(result, bool)

    @patch.dict(os.environ, {"USE_MOCK_HARDWARE": "false"})
    @patch('sys.platform', 'darwin')
    def test_create_default_backend_macos(self):
        """Test that factory creates macOS backend on darwin platform."""
        backend = AudioDomainFactory.create_default_backend()

        assert backend is not None
        assert hasattr(backend, 'play_file'), "Backend should have play_file method"
        assert hasattr(backend, 'is_playing'), "Backend should have is_playing property"

    @patch.dict(os.environ, {"USE_MOCK_HARDWARE": "false"})
    @patch('sys.platform', 'linux')
    def test_create_default_backend_linux(self):
        """Test that factory creates WM8960 backend on linux platform."""
        backend = AudioDomainFactory.create_default_backend()

        assert backend is not None
        assert hasattr(backend, 'play_file'), "Backend should have play_file method"
        assert hasattr(backend, 'is_playing'), "Backend should have is_playing property"

    @patch.dict(os.environ, {"USE_MOCK_HARDWARE": "false"})
    @patch('sys.platform', 'win32')
    def test_create_default_backend_unsupported_platform(self):
        """Test that factory creates fallback mock backend on unsupported platforms."""
        backend = AudioDomainFactory.create_default_backend()

        assert backend is not None
        assert hasattr(backend, 'play_file'), "Backend should have play_file method"
        assert hasattr(backend, 'is_playing'), "Backend should have is_playing property"

    def test_create_default_backend_never_returns_none(self):
        """Critical test: ensure factory NEVER returns None."""
        # Test with various environment configurations
        test_configs = [
            {"USE_MOCK_HARDWARE": "true"},
            {"USE_MOCK_HARDWARE": "false"},
            {},  # No environment variable set
        ]

        platforms = ['darwin', 'linux', 'win32', 'freebsd']

        for config in test_configs:
            for platform in platforms:
                with patch.dict(os.environ, config, clear=False):
                    with patch('sys.platform', platform):
                        backend = AudioDomainFactory.create_default_backend()

                        # This is the critical assertion that would have caught the original bug
                        assert backend is not None, f"Factory returned None for config {config} on platform {platform}"
                        assert hasattr(backend, 'play_file'), f"Backend should have play_file method for config {config} on platform {platform}"


class TestBackendIntegration:
    """Integration tests to ensure complete backend initialization works."""

    @patch.dict(os.environ, {"USE_MOCK_HARDWARE": "true"})
    def test_complete_system_creation_with_mock(self):
        """Test that complete audio system can be created with mock hardware."""
        # This simulates the exact scenario from the original error
        default_backend = AudioDomainFactory.create_default_backend()

        # Should not be None (this would have caught the original bug)
        assert default_backend is not None

        # Should be able to create complete system
        audio_engine, backend, playlist_manager = AudioDomainFactory.create_complete_system(default_backend)

        assert audio_engine is not None
        assert backend is not None
        assert playlist_manager is not None

        # Should be able to call play operations without "Backend does not support play_file" error
        result = backend.play_file("/test/path.mp3")
        assert isinstance(result, bool)

    def test_backend_adapter_double_wrapping_prevention(self):
        """Test that BackendAdapter prevents double-wrapping."""
        mock_backend = Mock()

        # Create first adapter
        adapter1 = AudioDomainFactory.create_backend_adapter(mock_backend)

        # Try to adapt the adapter (should return same instance)
        adapter2 = AudioDomainFactory.create_backend_adapter(adapter1)

        # Should be the same instance to prevent double-wrapping
        assert adapter1 is adapter2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])