# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

from typing import Generic, TypeVar

from .nfc_hardware import NFCHardware

T = TypeVar("T", bound=NFCHardware)


class NFCHandler(Generic[T]):
    """NFC handler that abstracts the underlying hardware (MockNFC or PN532I2CNFC).

    Ensure that all hardware access goes through the proper interfaces.
    """

    def __init__(self, hardware: T):
        """Initialize the handler with the specified NFC hardware.

        Args:
            hardware: Instance of the NFC hardware (mock or real).
        """
        self._hardware = hardware

    @property
    def tag_subject(self):
        """Get the RxPy subject that emits tag detection events.

        Returns:
            The RxPy subject for tag events.
        """
        if hasattr(self._hardware, "tag_subject"):
            return self._hardware.tag_subject
        raise AttributeError(
            "Underlying hardware does not have a tag_subject property."
        )

    async def start_nfc_reader(self) -> None:
        """Démarre le lecteur NFC de manière asynchrone."""
        if hasattr(self._hardware, "start_nfc_reader"):
            await self._hardware.start_nfc_reader()
        else:
            raise NotImplementedError(
                "Underlying hardware does not support start_nfc_reader()."
            )

    async def stop_nfc_reader(self) -> None:
        """Arrête le lecteur NFC de manière asynchrone."""
        if hasattr(self._hardware, "stop_nfc_reader"):
            await self._hardware.stop_nfc_reader()
        else:
            raise NotImplementedError(
                "Underlying hardware does not support stop_nfc_reader()."
            )

    async def read_tag(self) -> str:
        """Lit un tag NFC de manière asynchrone."""
        if hasattr(self._hardware, "read_nfc"):
            return await self._hardware.read_nfc()
        raise NotImplementedError("Underlying hardware does not support read_nfc().")

    async def write_tag(self, data: str) -> None:
        """Écrit des données sur un tag NFC de manière asynchrone."""
        if hasattr(self._hardware, "write_tag"):
            await self._hardware.write_tag(data)
        else:
            raise NotImplementedError(
                "Underlying hardware does not support write_tag()."
            )

    async def cleanup(self) -> None:
        """Clean up hardware resources asynchronously."""
        if hasattr(self._hardware, "cleanup"):
            await self._hardware.cleanup()
        else:
            raise NotImplementedError("Underlying hardware does not support cleanup().")

    def is_running(self) -> bool:
        """Check if the NFC reader is currently running.

        Returns:
            True if the reader is running, False otherwise
        """
        if hasattr(self._hardware, "_running"):
            return self._hardware._running
        return False
