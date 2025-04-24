# app/src/module/nfc/nfc_factory.py

import os
import sys
from typing import Optional
from eventlet.semaphore import Semaphore
from .nfc_handler import NFCHandler
from .nfc_hardware import NFCHardware

def get_nfc_handler(bus_lock: Semaphore) -> NFCHandler[NFCHardware]:
    """
    Returns an NFCHandler with the provided bus_lock injected into the hardware module.
    This lock must be created and managed by the application/container.
    """
    if os.environ.get('USE_MOCK_HARDWARE', '').lower() == 'true' or sys.platform == 'darwin':
        from .nfc_mock import MockNFC
        return NFCHandler(MockNFC())
    else:
        from .nfc_pn532_i2c import PN532I2CNFC
        return NFCHandler(PN532I2CNFC(bus_lock))
