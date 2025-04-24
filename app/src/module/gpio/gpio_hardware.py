# app/src/module/gpio/gpio_hardware.py
from typing import Protocol
from enum import Enum, auto

class PinMode(Enum):
    INPUT = auto()
    OUTPUT = auto()
    PWM = auto()


class GPIOHardware(Protocol):
    def setup(self, pin: int, mode: str) -> None: ...
    def output(self, pin: int, value: bool) -> None: ...
    def input(self, pin: int) -> bool: ...
    def cleanup(self) -> None: ...
