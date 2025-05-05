from typing import Generic, TypeVar
from .nfc_hardware import NFCHardware

T = TypeVar('T', bound=NFCHardware)

class NFCHandler(Generic[T]):
    def __init__(self, hardware: T):
        self._hardware = hardware

    @property
    def tag_subject(self):
        if hasattr(self._hardware, "tag_subject"):
            return self._hardware.tag_subject
        raise AttributeError("Underlying hardware does not have a tag_subject property.")

    def start_nfc_reader(self) -> None:
        if hasattr(self._hardware, "start_nfc_reader"):
            self._hardware.start_nfc_reader()
        else:
            raise NotImplementedError("Underlying hardware does not support start_nfc_reader().")

    def stop_nfc_reader(self) -> None:
        if hasattr(self._hardware, "stop_nfc_reader"):
            self._hardware.stop_nfc_reader()
        else:
            raise NotImplementedError("Underlying hardware does not support stop_nfc_reader().")

    def read_tag(self) -> str:
        return self._hardware.read_tag()

    def write_tag(self, data: str) -> None:
        self._hardware.write_tag(data)

    def cleanup(self) -> None:
        self._hardware.cleanup()
