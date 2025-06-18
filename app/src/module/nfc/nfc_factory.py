import asyncio
import os
import sys

from .nfc_handler import NFCHandler
from .nfc_hardware import NFCHardware


async def get_nfc_handler(bus_lock: asyncio.Lock) -> NFCHandler[NFCHardware]:
    """Returns an NFCHandler with the provided bus_lock injected into the
    hardware module. This lock must be created and managed by the
    application/container.

    Args:
        bus_lock: asyncio.Lock instance for thread-safe bus access

    Returns:
        Initialized NFCHandler instance with proper hardware backend
    """
    if (
        os.environ.get("USE_MOCK_HARDWARE", "").lower() == "true"
        or sys.platform == "darwin"
    ):
        from .nfc_mock import MockNFC

        mock_nfc = MockNFC()
        return NFCHandler(mock_nfc)
    else:
        from .nfc_pn532_i2c import PN532I2CNFC

        # Créer l'instance du hardware
        pn532_nfc = PN532I2CNFC(bus_lock)
        # Initialiser de façon asynchrone
        await pn532_nfc.initialize()
        return NFCHandler(pn532_nfc)
