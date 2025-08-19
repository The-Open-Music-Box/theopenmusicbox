# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Controls Hardware Factory Module.

Provides a factory for creating the appropriate controls hardware
implementation based on the current environment (Raspberry Pi or
development machine).
"""

import os
import platform
from typing import Union

from app.src.module.controles.controles_mock import ControlesMock
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

# Conditionally import GPIO-dependent class
try:
    from app.src.module.controles.controles_gpio import ControlesGPIO

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

logger = ImprovedLogger(__name__)


def create_controles_hardware() -> Union[ControlesMock, "ControlesGPIO"]:
    """Create the appropriate controls hardware implementation.

    This factory function selects the right implementation based on:
    1. The current platform (Raspberry Pi vs. other)
    2. The availability of GPIO libraries
    3. Environment configuration

    Returns:
        A hardware implementation (real or mock)
    """
    # Check if we're being forced to use mock hardware via environment variable
    force_mock = os.environ.get("USE_MOCK_CONTROLS", "").lower() in ("true", "1", "yes")

    if force_mock:
        logger.log(
            LogLevel.INFO, "Using mock controls hardware (forced by environment)"
        )
        return ControlesMock()

    # Check if we're running on a Raspberry Pi
    is_raspberry_pi = platform.machine().startswith(
        "arm"
    ) or platform.machine().startswith("aarch")

    # Use real GPIO if available and we're on a Pi
    if is_raspberry_pi and GPIO_AVAILABLE:
        logger.log(LogLevel.INFO, "Using real GPIO controls hardware")
        return ControlesGPIO()
    else:
        # Fall back to mock implementation
        if is_raspberry_pi:
            logger.log(
                LogLevel.WARNING,
                "Running on Raspberry Pi but GPIO libraries not available. Using mock controls.",
            )
        else:
            logger.log(
                LogLevel.INFO,
                "Not running on Raspberry Pi. Using mock controls hardware.",
            )

        return ControlesMock()
