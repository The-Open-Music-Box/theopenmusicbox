# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""NFC Factory for creating configured NFC services."""

from typing import Optional, Any

from app.src.domain.nfc import NfcAssociationService, NfcHardwareProtocol, NfcRepositoryProtocol
from app.src.application.services.nfc_application_service import NfcApplicationService
from .adapters.nfc_hardware_adapter import NfcHardwareAdapter, MockNfcHardwareAdapter
from .repositories.nfc_memory_repository import NfcMemoryRepository


class NfcFactory:
    """Factory for creating NFC services with proper dependency injection."""

    @staticmethod
    def create_nfc_application_service(
        legacy_nfc_handler: Optional[Any] = None,
        use_mock_hardware: bool = False,
        repository: Optional[NfcRepositoryProtocol] = None,
    ) -> NfcApplicationService:
        """Create a fully configured NFC application service.

        Args:
            legacy_nfc_handler: Legacy NFC handler for backward compatibility
            use_mock_hardware: Use mock hardware for testing
            repository: Custom repository implementation

        Returns:
            Configured NFC application service
        """
        # Create repository
        nfc_repository = repository or NfcMemoryRepository()

        # Create hardware adapter
        if use_mock_hardware:
            nfc_hardware = MockNfcHardwareAdapter()
        else:
            nfc_hardware = NfcHardwareAdapter(legacy_nfc_handler)

        # Create domain service
        nfc_association_service = NfcAssociationService(nfc_repository)

        # Create application service
        return NfcApplicationService(
            nfc_hardware=nfc_hardware,
            nfc_repository=nfc_repository,
            nfc_association_service=nfc_association_service,
        )

    @staticmethod
    def create_mock_nfc_service() -> NfcApplicationService:
        """Create NFC service with mock hardware for testing.

        Returns:
            NFC application service with mock implementations
        """
        return NfcFactory.create_nfc_application_service(use_mock_hardware=True)
