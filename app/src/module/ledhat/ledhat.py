# app/src/module/ledhat/ledhat.py
from typing import Generic, TypeVar
from .ledhat_hardware import LedHatHardware

HW = TypeVar("HW", bound=LedHatHardware)

class LedHat(Generic[HW]):
    """
    Generic LED Hat controller wrapper that delegates to the given hardware implementation.
    """
    def __init__(self, hardware: HW):
        self.hardware = hardware

    def clear(self) -> None:
        self.hardware.clear()

    def start_animation(self, animation_name: str, **kwargs) -> None:
        self.hardware.start_animation(animation_name, **kwargs)

    def stop_animation(self) -> None:
        self.hardware.stop_animation()

    def cleanup(self) -> None:
        self.hardware.cleanup()
