# app/src/hardware/light_sensor/__init__.py

"""
Light Sensor module for ambient light detection and monitoring.

This module provides a platform-independent interface for light sensing,
with concrete implementations for both Raspberry Pi hardware (using BH1750 sensor)
and mock testing. Features include:
- Real-time light level monitoring
- Reactive streams for light level updates
- Automatic platform detection
- Thread-safe I2C communication
"""

from .light_sensor_interface import (
    LightSensorInterface,
    LightLevel
)
from .light_sensor_factory import get_light_sensor

__all__ = [
    'LightSensorInterface',
    'LightLevel',
    'get_light_sensor'
]