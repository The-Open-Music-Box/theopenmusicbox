# app/src/module/gpio/__init__.py

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

from .gpio_interface import GPIOInterface
from .gpio_factory import get_gpio_controller

__all__ = [
    'GPIOInterface',
    'get_gpio_controller'
]
