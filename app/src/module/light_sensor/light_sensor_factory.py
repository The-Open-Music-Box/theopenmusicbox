# app/src/module/light_sensor/light_sensor_factory.py

import sys

from eventlet.semaphore import Semaphore

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .light_sensor import LightSensor
from .light_sensor_hardware import LightSensorHardware

logger = ImprovedLogger(__name__)

def get_light_sensor(bus_lock: Semaphore) -> LightSensor[LightSensorHardware]:
    if os.environ.get('USE_MOCK_HARDWARE', '').lower() == 'true' or sys.platform == 'darwin':
        from .light_sensor_mock import MockLightSensor
        logger.log(LogLevel.INFO, "Creating mock light sensor")
        return LightSensor(MockLightSensor())
    else:
        from .light_bh1750_i2c import Bh1750I2cLightSensor
        logger.log(LogLevel.INFO, "Creating Raspberry Pi light sensor")
        return LightSensor(Bh1750I2cLightSensor(bus_lock))
