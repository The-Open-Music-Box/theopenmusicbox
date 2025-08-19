# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""
Service container for dependency injection.

This module provides a centralized service container that manages service instances and
their dependencies, implementing the singleton pattern for stateful services and
enabling proper dependency injection.
"""

from typing import Dict, Type, TypeVar

from app.src.controllers.audio_controller import AudioController
from app.src.controllers.physical_controls_manager import PhysicalControlsManager
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.filesystem_sync_service import FilesystemSyncService
from app.src.services.nfc_association_service import NfcAssociationService
from app.src.services.playlist_crud_service import PlaylistCrudService
from app.src.services.playlist_service import PlaylistService
from app.src.services.track_management_service import TrackManagementService
from app.src.services.upload_service import UploadService

logger = ImprovedLogger(__name__)

T = TypeVar("T")


class ServiceContainer:
    """
    Centralized service container for dependency injection.

    Manages service instances using singleton pattern for stateful services and provides
    clean dependency injection throughout the application.
    """

    def __init__(self, config=None):
        """
        Initialize the service container.

        Args:     config: Application configuration object
        """
        from app.src.config import config as global_config

        self.config = config or global_config
        self._services: Dict[Type, object] = {}
        self._singletons: Dict[Type, object] = {}

        # Register singleton services
        self._register_singletons()

    def _register_singletons(self):
        """
        Register services that should be singletons.
        """
        singleton_services = [
            AudioController,
            PhysicalControlsManager,
            PlaylistService,
            PlaylistCrudService,
            TrackManagementService,
            NfcAssociationService,
            FilesystemSyncService,
        ]

        for service_class in singleton_services:
            self._singletons[service_class] = None

    def get_service(self, service_class: Type[T]) -> T:
        """
        Get a service instance from the container.

        Args:     service_class: The class type of the service to retrieve

        Returns:     Service instance
        """
        # Check if it's a singleton service
        if service_class in self._singletons:
            if self._singletons[service_class] is None:
                self._singletons[service_class] = self._create_service_instance(
                    service_class
                )
            return self._singletons[service_class]

        # For non-singleton services, create new instance each time
        return self._create_service_instance(service_class)

    def _create_service_instance(self, service_class: Type[T]) -> T:
        """
        Create a new service instance with proper dependency injection.

        Args:     service_class: The class type of the service to create

        Returns:     New service instance
        """
        try:
            # Handle special cases for services with specific dependencies
            if service_class == AudioController:
                # Get audio service from the main container (ContainerAsync)
                from app.src.module.audio_player.audio_factory import get_audio_player
                from app.src.services.notification_service import PlaybackSubject

                playback_subject = PlaybackSubject.get_instance()
                audio_service = get_audio_player(playback_subject=playback_subject)
                return AudioController(audio_service)

            elif service_class == PhysicalControlsManager:
                audio_controller = self.get_service(AudioController)
                return PhysicalControlsManager(audio_controller)

            elif service_class == UploadService:
                return UploadService(self.config)

            # For services that only need config
            elif hasattr(service_class, "__init__"):
                import inspect

                sig = inspect.signature(service_class.__init__)
                if "config_obj" in sig.parameters:
                    return service_class(config_obj=self.config)
                else:
                    return service_class()
            else:
                return service_class()

        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Failed to create service instance for {service_class.__name__}: {str(e)}",
            )
            raise

    def register_service(self, service_class: Type[T], instance: T):
        """
        Register a specific service instance.

        Args:     service_class: The class type of the service     instance: The service
        instance to register
        """
        if service_class in self._singletons:
            self._singletons[service_class] = instance
        else:
            self._services[service_class] = instance

    def clear_singletons(self):
        """
        Clear all singleton instances (useful for testing).
        """
        for service_class in self._singletons:
            self._singletons[service_class] = None

    def get_audio_controller(self) -> AudioController:
        """
        Get the audio controller singleton.

        Returns:     AudioController instance
        """
        return self.get_service(AudioController)

    def get_physical_controls_manager(self) -> PhysicalControlsManager:
        """
        Get the physical controls manager singleton.

        Returns:     PhysicalControlsManager instance
        """
        return self.get_service(PhysicalControlsManager)

    def get_playlist_crud_service(self) -> PlaylistCrudService:
        """
        Get the playlist CRUD service singleton.

        Returns:     PlaylistCrudService instance
        """
        return self.get_service(PlaylistCrudService)

    def get_track_management_service(self) -> TrackManagementService:
        """
        Get the track management service singleton.

        Returns:     TrackManagementService instance
        """
        return self.get_service(TrackManagementService)

    def get_nfc_association_service(self) -> NfcAssociationService:
        """
        Get the NFC association service singleton.

        Returns:     NfcAssociationService instance
        """
        return self.get_service(NfcAssociationService)

    def get_filesystem_sync_service(self) -> FilesystemSyncService:
        """
        Get the filesystem sync service singleton.

        Returns:     FilesystemSyncService instance
        """
        return self.get_service(FilesystemSyncService)

    def get_playlist_service(self) -> PlaylistService:
        """
        Get the playlist service singleton.

        Returns:     PlaylistService instance
        """
        return self.get_service(PlaylistService)

    def get_upload_service(self) -> UploadService:
        """
        Get a new upload service instance.

        Returns:     UploadService instance
        """
        return self.get_service(UploadService)
