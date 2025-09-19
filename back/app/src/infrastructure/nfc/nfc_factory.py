# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""NFC Factory for creating configured NFC services."""

import asyncio
from typing import Optional, Any

from app.src.domain.nfc import NfcAssociationService, NfcHardwareProtocol, NfcRepositoryProtocol
from app.src.domain.nfc.nfc_adapter import NFCHandlerAdapter
from app.src.application.services.nfc_application_service import NfcApplicationService
from app.src.infrastructure.hardware.nfc import create_nfc_hardware
from app.src.config.nfc_config import NFCConfig
from .adapters.nfc_hardware_adapter import NfcHardwareAdapter, MockNfcHardwareAdapter
from .repositories.nfc_memory_repository import NfcMemoryRepository
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)


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

    @staticmethod
    async def create_nfc_handler_adapter(nfc_lock: Optional[asyncio.Lock] = None) -> NFCHandlerAdapter:
        """Factory function to get NFC handler with new infrastructure.

        Args:
            nfc_lock: Optional asyncio lock for I2C bus synchronization

        Returns:
            NFCHandlerAdapter wrapping the appropriate hardware implementation
        """
        logger.log(LogLevel.INFO, "🏭 Creating NFC handler with new infrastructure...")

        # Create NFC configuration
        config = NFCConfig()

        # Create hardware implementation using factory
        hardware = await create_nfc_hardware(
            bus_lock=nfc_lock,
            config=config,
            force_mock=False,  # Let factory decide based on environment
        )

        # Wrap hardware in adapter
        adapter = NFCHandlerAdapter(hardware)

        hardware_info = "Mock" if adapter._is_mock else "Real PN532"
        logger.log(LogLevel.INFO, f"✅ NFC handler created with {hardware_info} hardware")

        return adapter
