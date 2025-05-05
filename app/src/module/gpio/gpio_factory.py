import os
import sys
from .gpio_controller import GPIOController
from .gpio_hardware import GPIOHardware

def get_gpio_controller(lock) -> GPIOController[GPIOHardware]:
    if os.environ.get('USE_MOCK_HARDWARE', '').lower() == 'true' or sys.platform == 'darwin':
        from .gpio_mock import MockGPIO
        return GPIOController(MockGPIO(lock))
    else:
        from .gpio_raspberry import RaspberryGPIO
        return GPIOController(RaspberryGPIO(lock))
