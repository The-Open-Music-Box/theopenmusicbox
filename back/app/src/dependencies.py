# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Dependency providers for FastAPI DI (Depends pattern).

This module provides clean dependency injection functions for FastAPI routes,
using the DI Container to avoid circular dependencies.
"""

from app.src.infrastructure.di.container import get_container
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)

# Get the global DI container
container = get_container()


def get_config():
    """Dependency provider for the global config singleton.

    Returns:
        The global configuration object.
    """
    return container.get("config")


def get_domain_bootstrap():
    """Get the domain bootstrap instance for pure DDD architecture.

    Returns:
        The domain bootstrap instance providing access to domain services.
    """
    return container.get("domain_bootstrap")


def get_audio_service():
    """Retrieve the audio service from domain architecture.

    Returns:
        The unified controller instance.
    """
    return container.get("unified_controller")


def get_playlist_repository():
    """Retrieve the pure DDD playlist repository instance.

    Returns:
        The pure DDD playlist repository implementation.
    """
    return container.get("playlist_repository")


def get_playlist_repository_adapter():
    """Retrieve the playlist repository adapter instance.

    Returns:
        The playlist repository adapter for domain operations.
    """
    return container.get("playlist_repository_adapter")


def get_data_application_service():
    """Retrieve the data application service for use cases.

    Returns:
        The data application service instance.
    """
    return container.get("data_application_service")


def get_audio_application_service():
    """Retrieve the audio application service for use cases.

    Returns:
        The audio application service instance.
    """
    return container.get("audio_application_service")


# Data Domain Dependencies
def get_data_application_service():
    """Retrieve the data application service for use cases.

    Returns:
        The data application service instance.
    """
    return container.get("data_application_service")


def get_data_playlist_service():
    """Retrieve the data playlist service.

    Returns:
        The data playlist service instance.
    """
    return container.get("data_playlist_service")


def get_data_track_service():
    """Retrieve the data track service.

    Returns:
        The data track service instance.
    """
    return container.get("data_track_service")
