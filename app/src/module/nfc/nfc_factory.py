# app/src/module/nfc/nfc_factory.py

import sys
from typing import Optional
from eventlet.semaphore import Semaphore
from .nfc_interface import NFCInterface

def get_nfc_handler(bus_lock: Optional[Semaphore] = None) -> NFCInterface:
    if sys.platform == 'darwin':
        from .nfc_mock import MockNFC
        return MockNFC()
    else:
        from .nfc_pn532_i2c import NFCPN532I2C
        return NFCPN532I2C(bus_lock)
