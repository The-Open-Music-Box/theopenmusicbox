# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Factory for creating audio domain components."""

from typing import Any

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_errors

from app.src.domain.protocols.audio_backend_protocol import AudioBackendProtocol
from app.src.domain.protocols.audio_engine_protocol import AudioEngineProtocol
# PlaylistManagerProtocol removed - use data domain services
from app.src.domain.protocols.event_bus_protocol import EventBusProtocol
from app.src.domain.protocols.state_manager_protocol import StateManagerProtocol

from .engine.event_bus import EventBus
from .engine.state_manager import StateManager
from .engine.audio_engine import AudioEngine
from app.src.infrastructure.adapters.audio.backend_adapter import BackendAdapter

logger = get_logger(__name__)


class AudioDomainFactory:
    """Factory for creating audio domain components with dependency injection."""

    @staticmethod
    def create_event_bus() -> EventBusProtocol:
        """Create a new event bus."""
        return EventBus()

    @staticmethod
    def create_state_manager() -> StateManagerProtocol:
        """Create a new state manager."""
        return StateManager()

    @staticmethod
    def create_backend_adapter(backend: Any) -> AudioBackendProtocol:
        """Create a backend adapter for existing backends.

        Args:
            backend: Existing backend implementation

        Returns:
            AudioBackendProtocol: Adapted backend
        """
        # Avoid double-wrapping: if already a BackendAdapter, return as-is
        if isinstance(backend, BackendAdapter):
            logger.log(
                LogLevel.DEBUG,
                f"Backend is already a BackendAdapter, reusing: {type(backend).__name__}",
            )
            return backend

        return BackendAdapter(backend)

    # PlaylistManager removed - use data domain services

    @staticmethod
    def create_audio_engine(
        backend: AudioBackendProtocol,
        event_bus: EventBusProtocol = None,
        state_manager: StateManagerProtocol = None,
    ) -> AudioEngineProtocol:
        """Create a complete audio engine.

        Args:
            backend: Audio backend
            event_bus: Optional event bus (creates one if None)
            state_manager: Optional state manager (creates one if None)

        Returns:
            AudioEngineProtocol: Complete audio engine
        """
        if event_bus is None:
            event_bus = AudioDomainFactory.create_event_bus()

        if state_manager is None:
            state_manager = AudioDomainFactory.create_state_manager()

        return AudioEngine(backend, event_bus, state_manager)

    @staticmethod
    def create_complete_system(
        existing_backend: Any,
    ) -> tuple[AudioEngineProtocol, AudioBackendProtocol]:
        """Create a complete audio system from an existing backend.

        Args:
            existing_backend: Existing audio backend implementation

        Returns:
            tuple: (audio_engine, backend_adapter, playlist_manager)
        """
        logger.log(
            LogLevel.INFO, f"Creating complete audio system with {type(existing_backend).__name__}"
        )

        # Create adapted backend
        backend = AudioDomainFactory.create_backend_adapter(existing_backend)

        # Create supporting components
        event_bus = AudioDomainFactory.create_event_bus()
        state_manager = AudioDomainFactory.create_state_manager()

        # Create main engine
        audio_engine = AudioDomainFactory.create_audio_engine(
            backend, event_bus, state_manager
        )

        logger.log(LogLevel.INFO, "Complete audio system created successfully")

        return audio_engine, backend

    @staticmethod
    @handle_errors("create_default_backend")
    def create_default_backend() -> AudioBackendProtocol:
        """Create a default audio backend for pure domain architecture.

        Returns:
            AudioBackendProtocol: Default audio backend
        """
        logger.log(LogLevel.INFO, "Creating default audio backend for pure domain architecture")

        import sys
        import os

        from app.src.domain.protocols.notification_protocol import PlaybackNotifierProtocol as PlaybackSubject

        playback_subject = PlaybackSubject.get_instance()

        # Check if we should use mock hardware
        use_mock = os.getenv("USE_MOCK_HARDWARE", "false").lower() == "true"

        if use_mock:
            logger.log(LogLevel.INFO, "🎭 Using mock audio backend (USE_MOCK_HARDWARE=true)")
            from .backends.implementations.mock_audio_backend import MockAudioBackend

            mock_backend = MockAudioBackend(playback_subject)
            logger.log(
                LogLevel.INFO, f"✅ Created mock audio backend: {type(mock_backend).__name__}"
            )
            return AudioDomainFactory.create_backend_adapter(mock_backend)

        # Platform-specific backend selection
        if sys.platform == "darwin":
            logger.log(LogLevel.INFO, "🍎 Detected macOS platform")
            from .backends.implementations.macos_audio_backend import MacOSAudioBackend

            macos_backend = MacOSAudioBackend(playback_subject)
            logger.log(
                LogLevel.INFO, f"✅ Created macOS audio backend: {type(macos_backend).__name__}"
            )
            return AudioDomainFactory.create_backend_adapter(macos_backend)

        elif sys.platform == "linux":
            logger.log(LogLevel.INFO, "🐧 Detected Linux platform")
            from .backends.implementations.wm8960_audio_backend import WM8960AudioBackend

            wm8960_backend = WM8960AudioBackend(playback_subject)
            logger.log(
                LogLevel.INFO, f"✅ Created WM8960 audio backend: {type(wm8960_backend).__name__}"
            )
            return AudioDomainFactory.create_backend_adapter(wm8960_backend)

        else:
            logger.log(
                LogLevel.WARNING,
                f"⚠️ Unsupported platform {sys.platform}, falling back to mock backend",
            )
            from .backends.implementations.mock_audio_backend import MockAudioBackend

            fallback_backend = MockAudioBackend(playback_subject)
            logger.log(
                LogLevel.INFO,
                f"✅ Created fallback mock backend: {type(fallback_backend).__name__}",
            )
            return AudioDomainFactory.create_backend_adapter(fallback_backend)
