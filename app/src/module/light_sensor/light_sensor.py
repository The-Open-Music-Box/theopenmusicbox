# app/src/module/light_sensor/light_sensor.py
from typing import Generic, TypeVar
from .light_sensor_hardware import LightSensorHardware

T = TypeVar('T', bound=LightSensorHardware)

class LightSensor(Generic[T]):
    def __init__(self, hardware: T):
        self._hardware = hardware

    def read_lux(self) -> float:
        return self._hardware.read_lux()

    def cleanup(self) -> None:
        self._hardware.cleanup()
