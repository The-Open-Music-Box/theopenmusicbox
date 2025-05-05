"""
Hardware GPIO control module providing platform-independent GPIO management.

This module offers a unified interface for GPIO operations with implementations for:
- Raspberry Pi hardware using RPi.GPIO
- Mock controller for development and testing

Features include:
- Pin setup and configuration
- PWM control
- Safe cleanup and resource management
- Automatic platform detection
"""

from .gpio_factory import get_gpio_controller

__all__ = [
    'get_gpio_controller'
]
