# app/src/module/ledhat/ledhat_factory.py

import os
import sys
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat import LedHat
from .ledhat_mock import MockLedHat
from .ledhat_rpi_ws281x import RpiWs281xLedHat

logger = ImprovedLogger(__name__)

def get_led_hat(gpio_pin):
    """
    Returns the appropriate LED controller implementation based on the platform.
    If the real implementation fails, no fallback is performed and an exception is raised.

    The component is optional and should not prevent the application from starting.
    Its status can be reported in the health route.

    Args:
        num_pixels: Number of LEDs on the strip
        brightness: LED brightness (0.0 to 1.0)

    Returns:
        An instance of LedHatInterface

    Raises:
        ImportError: If the necessary libraries are not available
        Exception: If hardware initialization fails
    """
    if os.environ.get('USE_MOCK_HARDWARE', '').lower() == 'true' or sys.platform in ['darwin', 'win32']:
        logger.log(LogLevel.INFO, f"Creating mock LED hat")
        return LedHat(MockLedHat())
    else:
        logger.log(LogLevel.INFO, f"Creating Raspberry Pi LED hat")
        return LedHat(RpiWs281xLedHat(num_pixels=36, brightness=0.1, pin=gpio_pin))