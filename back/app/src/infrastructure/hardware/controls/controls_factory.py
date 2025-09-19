# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Physical Controls Factory.

Factory for creating physical controls implementations based on environment.
"""

import os
from typing import Optional

from app.src.domain.protocols.physical_controls_protocol import PhysicalControlsProtocol
from app.src.config.hardware_config import HardwareConfig
from app.src.infrastructure.hardware.controls.gpio_controls_implementation import GPIOPhysicalControls
from app.src.infrastructure.hardware.controls.mock_controls_implementation import MockPhysicalControls
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)


class PhysicalControlsFactory:
    """Factory for creating physical controls implementations."""

    @staticmethod
    def create_controls(hardware_config: HardwareConfig) -> PhysicalControlsProtocol:
        """Create physical controls implementation based on environment.

        Args:
            hardware_config: Hardware configuration

        Returns:
            PhysicalControlsProtocol implementation
        """
        # Check if mock hardware is requested
        use_mock = (
            os.getenv("USE_MOCK_HARDWARE", "false").lower() == "true" or
            hardware_config.mock_hardware
        )

        if use_mock:
            logger.log(LogLevel.INFO, "🧪 Creating mock physical controls implementation")
            return MockPhysicalControls(hardware_config)
        else:
            logger.log(LogLevel.INFO, "🔌 Creating GPIO physical controls implementation")
            return GPIOPhysicalControls(hardware_config)

    @staticmethod
    def create_mock_controls(hardware_config: HardwareConfig) -> MockPhysicalControls:
        """Create mock controls implementation for testing.

        Args:
            hardware_config: Hardware configuration

        Returns:
            MockPhysicalControls implementation
        """
        logger.log(LogLevel.INFO, "🧪 Creating mock physical controls for testing")
        return MockPhysicalControls(hardware_config)