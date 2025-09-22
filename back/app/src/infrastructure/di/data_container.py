# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Data domain dependency injection container."""

from app.src.monitoring import get_logger
from app.src.infrastructure.di.container import get_container
from app.src.domain.data.services.playlist_service import PlaylistService
from app.src.domain.data.services.track_service import TrackService
from app.src.application.services.data_application_service import DataApplicationService
from app.src.infrastructure.repositories.data_playlist_repository import DataPlaylistRepository
from app.src.infrastructure.repositories.data_track_repository import DataTrackRepository
from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import (
    PureSQLitePlaylistRepository
)

logger = get_logger(__name__)


def register_data_domain_services() -> None:
    """Register all data domain services in the DI container."""
    container = get_container()

    # Register repository factories
    def create_data_playlist_repository():
        # Get the existing SQLite repository
        sqlite_repo = container.get("pure_sqlite_playlist_repository")
        return DataPlaylistRepository(sqlite_repo)

    def create_data_track_repository():
        # Get the existing SQLite repository
        sqlite_repo = container.get("pure_sqlite_playlist_repository")
        return DataTrackRepository(sqlite_repo)

    def create_playlist_service():
        playlist_repo = container.get("data_playlist_repository")
        track_repo = container.get("data_track_repository")
        return PlaylistService(playlist_repo, track_repo)

    def create_track_service():
        track_repo = container.get("data_track_repository")
        playlist_repo = container.get("data_playlist_repository")
        return TrackService(track_repo, playlist_repo)

    def create_data_application_service():
        playlist_service = container.get("data_playlist_service")
        track_service = container.get("data_track_service")
        return DataApplicationService(playlist_service, track_service)

    # Register services
    container.register_factory("data_playlist_repository", create_data_playlist_repository)
    container.register_factory("data_track_repository", create_data_track_repository)
    container.register_factory("data_playlist_service", create_playlist_service)
    container.register_factory("data_track_service", create_track_service)
    container.register_factory("data_application_service", create_data_application_service)

    logger.info("✅ Data domain services registered in DI container")


def get_data_playlist_service() -> PlaylistService:
    """Get the data playlist service.

    Returns:
        PlaylistService instance
    """
    return get_container().get("data_playlist_service")


def get_data_track_service() -> TrackService:
    """Get the data track service.

    Returns:
        TrackService instance
    """
    return get_container().get("data_track_service")