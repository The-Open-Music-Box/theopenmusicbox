# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Domain-driven architecture bootstrap.

This module provides the main entry point for initializing the domain-driven architecture
and provides compatibility layers for legacy code.
"""

from typing import Any, Dict

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors

from .audio.container import audio_domain_container
from .audio.factory import AudioDomainFactory
from .controllers.unified_controller import unified_controller
from .error_handling.unified_error_handler import (
    unified_error_handler,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
)

logger = get_logger(__name__)


class DomainBootstrap:
    """Bootstrap class for domain-driven architecture."""

    # MARK: - Initialization

    def __init__(self):
        """Initialize the bootstrap."""
        self._is_initialized = False

    @handle_errors(operation_name="initialize", component="domain.bootstrap")
    def initialize(self, existing_backend: Any = None) -> None:
        """Initialize the domain-driven architecture.

        Args:
            existing_backend: Existing audio backend to adapt
        """
        if self._is_initialized:
            logger.log(LogLevel.WARNING, "DomainBootstrap already initialized")
            return

        logger.log(LogLevel.INFO, "🚀 Initializing domain architecture...")
        if existing_backend:
            audio_domain_container.initialize(existing_backend)
            logger.log(
                LogLevel.DEBUG, f"Audio domain initialized with {type(existing_backend).__name__}"
            )
        else:
            default_backend = AudioDomainFactory.create_default_backend()
            audio_domain_container.initialize(default_backend)
            logger.log(
                LogLevel.DEBUG,
                f"Pure domain audio initialized with {type(default_backend).__name__}",
            )

        self._is_initialized = True
        logger.log(LogLevel.INFO, "✅ Domain bootstrap initialized")

    # MARK: - Lifecycle Management

    @handle_errors(operation_name="start", component="domain.bootstrap")
    async def start(self) -> None:
        """Start all domain services."""
        if not self._is_initialized:
            context = ErrorContext(
                component="domain.bootstrap",
                operation="start",
                category=ErrorCategory.GENERAL,
                severity=ErrorSeverity.HIGH,
            )
            unified_error_handler.handle_error(
                RuntimeError("DomainBootstrap not initialized"), context
            )
            return

        if audio_domain_container.is_initialized:
            await audio_domain_container.start()
        else:
            logger.log(LogLevel.WARNING, "⚠️ Audio domain not initialized, skipping start")
        await unified_controller.start()
        logger.log(LogLevel.INFO, "🚀 Domain services started")

    @handle_errors(operation_name="stop", component="domain.bootstrap")
    async def stop(self) -> None:
        """Stop all domain services."""
        if not self._is_initialized:
            return
        await unified_controller.stop()
        if audio_domain_container.is_initialized:
            await audio_domain_container.stop()
        logger.log(LogLevel.DEBUG, "Domain services stopped")

    @handle_errors(operation_name="cleanup", component="domain.bootstrap")
    def cleanup(self) -> None:
        """Cleanup all resources."""
        if not self._is_initialized:
            return

        unified_controller.cleanup()
        audio_domain_container.cleanup()
        self._is_initialized = False
        logger.log(LogLevel.DEBUG, "Domain cleanup completed")

    # MARK: - Public Properties

    @property
    def is_initialized(self) -> bool:
        """Check if bootstrap is initialized."""
        return self._is_initialized

    # MARK: - System Status

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "domain_bootstrap": {
                "initialized": self._is_initialized,
                "architecture": "pure_domain",
            },
            "audio_domain": {
                "initialized": audio_domain_container.is_initialized,
                "running": (
                    audio_domain_container.audio_engine.is_running
                    if audio_domain_container.is_initialized
                    else False
                ),
            },
            "unified_controller": {
                "initialized": unified_controller.is_initialized,
                "playing": unified_controller.is_playing,
                "paused": unified_controller.is_paused,
            },
            "error_handler": unified_error_handler.get_error_statistics(),
        }

    # MARK: Internal Methods

    def _setup_error_callbacks(self) -> None:
        """Setup error handling callbacks."""
        unified_error_handler.register_callback(ErrorCategory.AUDIO, self._handle_audio_error)

        unified_error_handler.register_callback(ErrorCategory.AUDIO, self._handle_critical_error)

    def _handle_audio_error(self, error_record) -> None:
        """Handle audio-specific errors."""
        logger.log(LogLevel.WARNING, f"🎵 Audio error handled: {error_record.message}")

        # TODO: could implement recovery strategies here
        # For example: restart audio backend, switch to backup backend, etc.

    def _handle_critical_error(self, error_record) -> None:
        """Handle critical errors."""
        logger.log(LogLevel.ERROR, f"🔥 Critical error handled: {error_record.message}")

        # TODO: implement emergency procedures here
        # For example: notify administrators, save state, initiate safe shutdown, etc.


# MARK: - Global Instance

domain_bootstrap = DomainBootstrap()
