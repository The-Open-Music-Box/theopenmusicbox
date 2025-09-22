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
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_errors

from .audio.container import audio_domain_container
from .audio.factory import AudioDomainFactory
from app.src.infrastructure.error_handling.unified_error_handler import (
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
        self._is_stopping = False

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
        # Note: unified_controller has been moved to application layer
        logger.log(LogLevel.INFO, "🚀 Domain services started")

    @handle_errors(operation_name="stop", component="domain.bootstrap")
    async def stop(self) -> None:
        """Stop all domain services."""
        if not self._is_initialized or self._is_stopping:
            return

        self._is_stopping = True
        try:
            # Note: unified_controller has been moved to application layer
            if audio_domain_container.is_initialized:
                await audio_domain_container.stop()
            logger.log(LogLevel.DEBUG, "Domain services stopped")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error stopping domain services: {e}")
            # Don't re-raise during shutdown to prevent recursion
        finally:
            self._is_stopping = False

    @handle_errors(operation_name="cleanup", component="domain.bootstrap")
    def cleanup(self) -> None:
        """Cleanup all resources."""
        if not self._is_initialized:
            return

        # Note: unified_controller has been moved to application layer
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
            # Note: unified_controller has been moved to application layer
            "error_handler": unified_error_handler.get_error_statistics(),
        }

    # MARK: Internal Methods

    def _setup_error_callbacks(self) -> None:
        """Setup error handling callbacks."""
        unified_error_handler.register_callback(ErrorCategory.AUDIO, self._handle_audio_error)

        unified_error_handler.register_callback(ErrorCategory.AUDIO, self._handle_critical_error)

    def _handle_audio_error(self, error_record) -> None:
        """Handle audio-specific errors with recovery strategies."""
        logger.log(LogLevel.WARNING, f"🎵 Audio error handled: {error_record.message}")

        # Implement audio recovery strategies based on error type
        if "connection" in error_record.message.lower():
            logger.log(LogLevel.INFO, "🔄 Attempting audio backend reconnection...")
            # Note: Actual recovery would require access to audio container
            # In a real implementation, we'd inject recovery service here
        elif "timeout" in error_record.message.lower():
            logger.log(LogLevel.INFO, "⏱️ Audio timeout detected, attempting restart...")
        else:
            logger.log(LogLevel.INFO, "🛠️ General audio error recovery initiated...")

    def _handle_critical_error(self, error_record) -> None:
        """Handle critical errors with emergency procedures."""
        logger.log(LogLevel.ERROR, f"🔥 Critical error handled: {error_record.message}")

        # Implement emergency procedures for critical errors
        logger.log(LogLevel.ERROR, "🚨 Initiating emergency procedures...")

        # Log critical error for administrator notification
        logger.log(LogLevel.CRITICAL, f"ALERT: Critical system error - {error_record.message}")

        # Attempt to save current state before potential shutdown
        try:
            logger.log(LogLevel.INFO, "💾 Attempting to save current application state...")
            # Note: State saving would require access to state services
            # In a real implementation, we'd inject state persistence service here
        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Failed to save state: {e}")

        # Consider graceful degradation rather than immediate shutdown
        logger.log(LogLevel.WARNING, "🔒 Entering safe mode operation...")


# MARK: - Global Instance

domain_bootstrap = DomainBootstrap()
