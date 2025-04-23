# app/src/module/motor/motor_factory.py

import sys
import os
from src.module.gpio.gpio_hardware import GPIOHardware

from .motor import Motor
from .motor_hardware import MotorHardware
from .motor_mock import MockMotor
from .motor_N2003 import N2003Motor

def get_motor_controller(gpio: GPIOHardware) -> Motor[MotorHardware]:
    if os.environ.get('USE_MOCK_HARDWARE', '').lower() == 'true' or sys.platform == 'darwin':
        return Motor(MockMotor(gpio))
    else:
        return Motor(N2003Motor(gpio))