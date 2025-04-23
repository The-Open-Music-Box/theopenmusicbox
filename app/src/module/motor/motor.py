# app/src/module/motor/motor.py
from typing import Generic, TypeVar
from .motor_hardware import MotorHardware

T = TypeVar('T', bound=MotorHardware)

class Motor(Generic[T]):
    def __init__(self, hardware: T):
        self._hardware = hardware

    def forward(self, speed: float) -> None:
        self._hardware.forward(speed)

    def backward(self, speed: float) -> None:
        self._hardware.backward(speed)

    def stop(self) -> None:
        self._hardware.stop()

    def cleanup(self) -> None:
        self._hardware.cleanup()
