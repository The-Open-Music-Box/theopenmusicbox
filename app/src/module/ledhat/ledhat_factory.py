# app/src/module/ledhat/ledhat_factory.py

import sys
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat_interface import LedHatInterface

logger = ImprovedLogger(__name__)

def get_led_hat(gpio_pin) -> LedHatInterface:
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
    if sys.platform == 'darwin' or sys.platform == 'win32':
        # Use mock implementation for macOS and Windows
        from .ledhat_mock import MockLedHat
        logger.log(LogLevel.INFO, f"Creating mock LED hat")
        return MockLedHat(num_pixels=36, brightness=0.1)
    else:
        # Use real implementation for Raspberry Pi (Linux)
        # No automatic fallback, if it fails, the component will be in error
        from .ledhat_rpi_ws281x import RpiWs281xLedHat
        logger.log(LogLevel.INFO, f"Creating Raspberry Pi LED hat")
        return RpiWs281xLedHat(num_pixels=36, brightness=0.1, pin=gpio_pin)