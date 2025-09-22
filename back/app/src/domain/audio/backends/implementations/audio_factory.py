# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Audio backend factory for creating platform-specific audio players.

Provides factory functions to create appropriate audio backends based on the
current platform and hardware configuration, supporting macOS, Raspberry Pi,
and mock implementations for testing.
"""

import sys
from typing import Optional

from app.src.config import config
from app.src.domain.protocols.notification_protocol import PlaybackNotifierProtocol as PlaybackSubject
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_errors

from .unified_audio_player import UnifiedAudioPlayer
from app.src.domain.protocols.audio_backend_protocol import AudioBackendProtocol

logger = get_logger(__name__)


def get_unified_audio_player(
    playback_subject: Optional[PlaybackSubject] = None,
) -> UnifiedAudioPlayer:
    """Create a unified audio player with centralized playlist management.

    This is the recommended way to create audio players as it provides
    consistent playlist behavior across all platforms.

    Args:
        playback_subject: Optional notification service for playback events

    Returns:
        UnifiedAudioPlayer: A unified audio player with centralized playlist management
    """
    backend = _create_audio_backend(playback_subject)
    # Note: playlist_controller will be injected later by Infrastructure layer
    return UnifiedAudioPlayer(backend, playlist_controller=None, playback_subject=playback_subject)


@handle_errors("_create_audio_backend")
def _create_audio_backend(
    playback_subject: Optional[PlaybackSubject] = None,
) -> AudioBackendProtocol:
    """Create the appropriate audio backend based on platform and configuration.

    Args:
        playback_subject: Optional notification service for playbook events

    Returns:
        AudioBackendProtocol: Platform-appropriate audio backend
    """
    if config.hardware.mock_hardware:
        from .mock_audio_backend import MockAudioBackend

        logger.log(LogLevel.INFO, "🧪 Creating MockAudioBackend (mock hardware mode)")
        return MockAudioBackend(playback_subject)

    elif sys.platform == "darwin":
        # Use macOS-specific audio backend with Core Audio
        from .macos_audio_backend import MacOSAudioBackend

        logger.log(LogLevel.INFO, "🍎 Creating MacOSAudioBackend...")
        backend = MacOSAudioBackend(playback_subject)
        logger.log(LogLevel.INFO, "✅ macOS Audio Backend initialized successfully")
        return backend
        # Try to initialize hardware audio backend (WM8960 for Raspberry Pi)
        try:
            from .wm8960_audio_backend import WM8960AudioBackend

            logger.log(LogLevel.INFO, "🔊 Creating WM8960AudioBackend...")
            backend = WM8960AudioBackend(playback_subject)
            logger.log(LogLevel.INFO, "✅ WM8960 Audio Backend initialized successfully")
            return backend
        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Failed to initialize WM8960 audio: {e}")
            logger.log(LogLevel.WARNING, "⚠️️ Falling back to MockAudioBackend")

            from .mock_audio_backend import MockAudioBackend

            return MockAudioBackend(playback_subject)
