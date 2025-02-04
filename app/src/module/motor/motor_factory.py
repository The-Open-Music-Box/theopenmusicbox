# app/src/module/motor/motor_factory.py

import sys
from src.module.gpio.gpio_interface import GPIOInterface

from .motor_interface import MotorInterface
from .motor_mock import MockMotor

def get_motor_controller(gpio: GPIOInterface) -> MotorInterface:

    if sys.platform == 'darwin':
        from .motor_mock import MockMotor
        return MockMotor(gpio)
    else:
        from .motor_raspberry import MotorN2003
        return MotorN2003(gpio)