# app/src/module/gpio/gpio_controller.py
from typing import Generic, TypeVar
from .gpio_hardware import GPIOHardware

T = TypeVar('T', bound=GPIOHardware)

class GPIOController(Generic[T]):
    def __init__(self, hardware: T):
        self._hardware = hardware

    def setup(self, pin: int, mode: str) -> None:
        self._hardware.setup(pin, mode)

    def output(self, pin: int, value: bool) -> None:
        self._hardware.output(pin, value)

    def input(self, pin: int) -> bool:
        return self._hardware.input(pin)

    def cleanup(self) -> None:
        self._hardware.cleanup()
