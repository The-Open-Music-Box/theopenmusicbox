# app/src/module/ledhat/__init__.py

"""
Module for controlling an LED strip for the application.
Provides an abstract interface and platform-specific implementations.

This module offers:
- A unified interface for LED operations
- Two implementations: a real one for Raspberry Pi and a mock for testing/development
- Automatic platform detection
- An optional component that doesn't block application startup

The component is designed to be optional and its status can be reported in the health route.
"""

from .ledhat_interface import LedHatInterface
from .ledhat_factory import get_led_hat

__all__ = [
    'LedHatInterface',
    'get_led_hat'
]