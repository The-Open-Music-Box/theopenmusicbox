# app/src/hardware/motor/__init__.py

"""
Stepper Motor control module for precise motor movement and positioning.

This module provides a platform-independent interface for stepper motor control,
with implementations for both Raspberry Pi hardware (28BYJ-48 with N2003 driver)
and mock testing. Features include:
- Precise step control
- Bidirectional rotation
- Variable speed control (1-2000 steps/second)
- Dynamic acceleration
- Position tracking and callbacks
- Thread-safe operation
- Automatic platform detection
"""

from .motor_interface import (
    MotorInterface,
    MotorDirection,
    MotorStatus
)
from .motor_factory import get_motor_controller

__all__ = [
    'MotorInterface',
    'MotorDirection',
    'MotorStatus',
    'get_motor_controller'
]