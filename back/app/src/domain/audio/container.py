# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Dependency injection container for the audio domain."""

from typing import Optional, Any

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors

from .protocols.audio_backend_protocol import AudioBackendProtocol
from .protocols.audio_engine_protocol import AudioEngineProtocol
from .protocols.playlist_manager_protocol import PlaylistManagerProtocol
from .protocols.event_bus_protocol import EventBusProtocol
from .protocols.state_manager_protocol import StateManagerProtocol

from .factory import AudioDomainFactory

logger = get_logger(__name__)


class AudioDomainContainer:
    """Dependency injection container for audio domain components.

    Provides centralized configuration and lifecycle management
    for all audio domain components.
    """

    # MARK: - Initialization

    def __init__(self):
        self._audio_engine: Optional[AudioEngineProtocol] = None
        self._backend: Optional[AudioBackendProtocol] = None
        self._playlist_manager: Optional[PlaylistManagerProtocol] = None
        self._event_bus: Optional[EventBusProtocol] = None
        self._state_manager: Optional[StateManagerProtocol] = None

        self._is_initialized = False
        logger.log(LogLevel.INFO, "AudioDomainContainer created")

    @handle_errors("initialize")
    def initialize(self, existing_backend: Any) -> None:
        """Initialize the container with an existing backend.

        Args:
            existing_backend: Existing audio backend implementation
        """
        if self._is_initialized:
            logger.log(LogLevel.WARNING, "Container already initialized")
            return

        # Create complete audio system
        audio_engine, backend, playlist_manager = AudioDomainFactory.create_complete_system(
            existing_backend
        )
        # Store references
        self._audio_engine = audio_engine
        self._backend = backend
        self._playlist_manager = playlist_manager
        self._event_bus = audio_engine.event_bus
        self._state_manager = audio_engine.state_manager
        self._is_initialized = True
        logger.log(LogLevel.INFO, "AudioDomainContainer initialized successfully")

    # MARK: - Lifecycle Management

    async def start(self) -> None:
        """Start the audio system."""
        if not self._is_initialized:
            raise RuntimeError("Container not initialized")

        await self._audio_engine.start()
        logger.log(LogLevel.INFO, "Audio domain started")

    async def stop(self) -> None:
        """Stop the audio system."""
        if not self._is_initialized:
            return

        await self._audio_engine.stop()
        logger.log(LogLevel.INFO, "Audio domain stopped")

    @handle_errors("cleanup")
    def cleanup(self) -> None:
        """Clean up all resources."""
        if not self._is_initialized:
            return

        if self._playlist_manager:
            self._playlist_manager.cleanup()
        if self._backend:
            self._backend.cleanup()
        self._is_initialized = False
        logger.log(LogLevel.INFO, "AudioDomainContainer cleanup completed")

    # MARK: - Component Access

    @property
    def audio_engine(self) -> AudioEngineProtocol:
        """Get the audio engine."""
        if not self._is_initialized:
            raise RuntimeError("Container not initialized")
        return self._audio_engine

    @property
    def backend(self) -> AudioBackendProtocol:
        """Get the audio backend."""
        if not self._is_initialized:
            raise RuntimeError("Container not initialized")
        return self._backend

    @property
    def playlist_manager(self) -> PlaylistManagerProtocol:
        """Get the playlist manager."""
        if not self._is_initialized:
            raise RuntimeError("Container not initialized")
        return self._playlist_manager

    @property
    def event_bus(self) -> EventBusProtocol:
        """Get the event bus."""
        if not self._is_initialized:
            raise RuntimeError("Container not initialized")
        return self._event_bus

    @property
    def state_manager(self) -> StateManagerProtocol:
        """Get the state manager."""
        if not self._is_initialized:
            raise RuntimeError("Container not initialized")
        return self._state_manager

    @property
    def is_initialized(self) -> bool:
        """Check if container is initialized."""
        return self._is_initialized


# Global container instance
audio_domain_container = AudioDomainContainer()
