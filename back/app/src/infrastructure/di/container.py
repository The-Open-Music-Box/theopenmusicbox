# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Dependency Injection Container for TheOpenMusicBox."""

from typing import Dict, Any, Optional, Callable, TypeVar, Type
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

T = TypeVar('T')

logger = get_logger(__name__)


class DependencyContainer:
    """Dependency Injection Container following DDD principles."""

    def __init__(self):
        """Initialize the DI container."""
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

    def register_singleton(self, service_name: str, instance: Any) -> None:
        """Register a singleton instance.

        Args:
            service_name: Name of the service
            instance: The singleton instance
        """
        self._singletons[service_name] = instance
        logger.log(LogLevel.DEBUG, f"Registered singleton: {service_name}")

    def register_factory(self, service_name: str, factory: Callable) -> None:
        """Register a factory function.

        Args:
            service_name: Name of the service
            factory: Factory function that creates the service
        """
        self._factories[service_name] = factory
        logger.log(LogLevel.DEBUG, f"Registered factory: {service_name}")

    def get(self, service_name: str) -> Any:
        """Get a service instance.

        Args:
            service_name: Name of the service

        Returns:
            The service instance

        Raises:
            KeyError: If service is not registered
        """
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]

        # Check if we have a factory
        if service_name in self._factories:
            instance = self._factories[service_name]()
            # Cache as singleton if it's a class instance
            if hasattr(instance, '__class__') and not callable(instance):
                self._singletons[service_name] = instance
            return instance

        raise KeyError(f"Service '{service_name}' not registered")

    def has(self, service_name: str) -> bool:
        """Check if a service is registered.

        Args:
            service_name: Name of the service

        Returns:
            True if service is registered
        """
        return service_name in self._singletons or service_name in self._factories

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        logger.log(LogLevel.DEBUG, "Cleared all services from DI container")


# Global container instance
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global DI container instance.

    Returns:
        The global DI container
    """
    return _container


def register_core_services():
    """Register core services in the DI container."""
    container = get_container()

    # Register Configuration
    def config_factory():
        from app.src.config import config as app_config
        return app_config
    container.register_factory("config", config_factory)

    # Register Domain Bootstrap
    def domain_bootstrap_factory():
        from app.src.domain.bootstrap import domain_bootstrap
        if not domain_bootstrap.is_initialized:
            logger.log(LogLevel.WARNING, "Domain bootstrap not initialized")
        return domain_bootstrap
    container.register_factory("domain_bootstrap", domain_bootstrap_factory)

    # Register Repositories
    def playlist_repository_factory():
        from app.src.infrastructure.repositories.pure_sqlite_playlist_repository import PureSQLitePlaylistRepository
        return PureSQLitePlaylistRepository()
    container.register_factory("playlist_repository", playlist_repository_factory)

    def playlist_repository_adapter_factory():
        from app.src.infrastructure.adapters.pure_playlist_repository_adapter import PurePlaylistRepositoryAdapter
        return PurePlaylistRepositoryAdapter()
    container.register_factory("playlist_repository_adapter", playlist_repository_adapter_factory)

    # Register Application Services
    def playlist_application_service_factory():
        from app.src.application.services.data_application_service import DataApplicationService
        repository = container.get("playlist_repository_adapter")
        return DataApplicationService(playlist_repository=repository)
    container.register_factory("playlist_application_service", playlist_application_service_factory)

    def audio_application_service_factory():
        from app.src.application.services.audio_application_service import AudioApplicationService
        from app.src.domain.audio.container import audio_domain_container
        from app.src.services.state_manager import StateManager

        # Initialize audio domain container if needed
        if not audio_domain_container.is_initialized:
            domain_bootstrap = container.get("domain_bootstrap")
            if not domain_bootstrap.is_initialized:
                domain_bootstrap.initialize()

        playlist_service = container.get("playlist_application_service")
        return AudioApplicationService(
            audio_domain_container=audio_domain_container,
            playlist_application_service=playlist_service,
            state_manager=StateManager(),
        )
    container.register_factory("audio_application_service", audio_application_service_factory)

    # Register Controllers
    def unified_controller_factory():
        from app.src.application.controllers.unified_controller import unified_controller
        return unified_controller
    container.register_factory("unified_controller", unified_controller_factory)

    logger.log(LogLevel.INFO, "✅ Core services registered in DI container")


# Initialize core services on import
register_core_services()