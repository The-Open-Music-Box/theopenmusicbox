# app/src/module/gpio/gpio_factory.py

import sys
from .gpio_interface import GPIOInterface

def get_gpio_controller() -> GPIOInterface:
    if sys.platform == 'darwin':
        from .gpio_mock import MockPWM
        return MockPWM()
    else:
        from .gpio_raspberry import RaspberryGPIO
        return RaspberryGPIO()
