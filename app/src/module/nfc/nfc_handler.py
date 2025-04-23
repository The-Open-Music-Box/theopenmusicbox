# app/src/module/nfc/nfc_handler.py
from typing import Generic, TypeVar
from .nfc_hardware import NFCHardware

T = TypeVar('T', bound=NFCHardware)

class NFCHandler(Generic[T]):
    def __init__(self, hardware: T):
        self._hardware = hardware

    def read_tag(self) -> str:
        return self._hardware.read_tag()

    def write_tag(self, data: str) -> None:
        self._hardware.write_tag(data)

    def cleanup(self) -> None:
        self._hardware.cleanup()
