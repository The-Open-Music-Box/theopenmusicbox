# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Dependency providers for FastAPI DI (Depends pattern).

Provides config, container, audio, playback_subject, etc.
Functions are used via Depends() in route handlers.
"""

# No direct FastAPI imports needed - functions are used via Depends() in routes

from app.src.config import config as app_config
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

# Safe imports (no circular dependencies)
from app.src.services.state_manager import StateManager

logger = get_logger(__name__)

# MARK: - Configuration Dependencies


def get_config():
    """Dependency provider for the global config singleton.

    Note: Primarily used for FastAPI dependency injection overrides in tests.
    For direct usage in application code, prefer using app_config directly.

    Returns:
        The global configuration object.
    """
    return app_config


# MARK: - Domain Architecture Dependencies


def get_domain_bootstrap():
    """Get the domain bootstrap instance for pure DDD architecture.

    Returns:
        The domain bootstrap instance providing access to domain services.
    """
    from app.src.domain.bootstrap import domain_bootstrap

    if not domain_bootstrap.is_initialized:
        logger.log(LogLevel.WARNING, "Domain bootstrap not initialized")
    return domain_bootstrap


# MARK: - Audio Dependencies


def get_audio_service():
    """Retrieve the audio service from domain architecture.

    Returns:
        The unified controller instance.
    """
    from app.src.domain.controllers.unified_controller import unified_controller

    return unified_controller


# MARK: - Repository Dependencies

# Global repository instances (singleton pattern)
_playlist_repository_instance = None
_playlist_repository_adapter_instance = None

def get_playlist_repository():
    """Retrieve the pure DDD playlist repository instance (singleton).

    Returns:
        The pure DDD playlist repository implementation.
    """
    global _playlist_repository_instance

    if _playlist_repository_instance is None:
        from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import (
            PureSQLitePlaylistRepository,
        )
        _playlist_repository_instance = PureSQLitePlaylistRepository()
        logger.log(LogLevel.INFO, "✅ Created singleton Pure DDD Playlist Repository instance")

    return _playlist_repository_instance

def get_playlist_repository_adapter():
    """Retrieve the playlist repository adapter instance (singleton).

    Returns:
        The playlist repository adapter for domain operations.
    """
    global _playlist_repository_adapter_instance

    if _playlist_repository_adapter_instance is None:
        from app.src.infrastructure.adapters.pure_playlist_repository_adapter import (
            PurePlaylistRepositoryAdapter,
        )
        _playlist_repository_adapter_instance = PurePlaylistRepositoryAdapter()
        logger.log(LogLevel.INFO, "✅ Created singleton Pure DDD Repository Adapter instance")

    return _playlist_repository_adapter_instance


# MARK: - Application Service Dependencies


def get_playlist_application_service():
    """Retrieve the playlist application service for use cases.

    Returns:
        The playlist application service instance.
    """
    from app.src.application.services.playlist_application_service import PlaylistApplicationService

    repository = get_playlist_repository_adapter()
    return PlaylistApplicationService(playlist_repository=repository)


def get_audio_application_service():
    """Retrieve the audio application service for use cases.

    Returns:
        The audio application service instance.
    """
    from app.src.application.services.audio_application_service import AudioApplicationService
    from app.src.domain.audio.container import audio_domain_container

    # Initialize audio domain container if not already initialized
    if not audio_domain_container.is_initialized:
        from app.src.domain.bootstrap import domain_bootstrap

        if not domain_bootstrap.is_initialized:
            domain_bootstrap.initialize()
        else:
            logger.log(LogLevel.DEBUG, "Domain bootstrap initialized but audio container not ready")

    # Get required dependencies
    playlist_service = get_playlist_application_service()

    return AudioApplicationService(
        audio_domain_container=audio_domain_container,
        playlist_application_service=playlist_service,
        state_manager=StateManager(),
    )
