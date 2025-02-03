# app/src/module/light_sensor/light_sensor_factory.py

import sys

from eventlet.semaphore import Semaphore

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .light_sensor_interface import LightSensorInterface

logger = ImprovedLogger(__name__)

def get_light_sensor(bus_lock: Semaphore) -> LightSensorInterface:
    if sys.platform == 'darwin':
        from .light_sensor_mock import MockLightSensor
        logger.log(LogLevel.INFO, "Creating mock light sensor")
        return MockLightSensor()
    else:
        from .light_bh1750_i2c import LightSensorBH1750I2C
        logger.log(LogLevel.INFO, "Creating Raspberry Pi light sensor")
        return LightSensorBH1750I2C(bus_lock)
