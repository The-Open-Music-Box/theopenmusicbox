# app/src/module/gpio/gpio_factory.py

import os
import sys
from .gpio_controller import GPIOController
from .gpio_hardware import GPIOHardware

def get_gpio_controller() -> GPIOController[GPIOHardware]:
    if os.environ.get('USE_MOCK_HARDWARE', '').lower() == 'true' or sys.platform == 'darwin':
        from .gpio_mock import MockGPIO
        return GPIOController(MockGPIO())
    else:
        from .gpio_raspberry import RaspberryGPIO
        return GPIOController(RaspberryGPIO())
