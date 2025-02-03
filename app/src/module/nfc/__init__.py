# app/src/hardware/nfc/__init__.py

"""
NFC Reader module for contactless tag detection and reading.

This module provides a platform-independent interface for NFC operations,
with implementations for both Raspberry Pi hardware (PN532 via SPI/I2C)
and mock testing. Features include:
- Support for multiple connection types (SPI and I2C)
- Continuous tag monitoring in separate thread
- Debounced tag reading
- Reactive tag event streaming
- Automatic card type detection
- Thread-safe bus access
- Robust error handling and recovery
- Automatic platform detection

Supported hardware:
- PN532 NFC controller
- NTAG2xx and MIFARE card types
"""

from .nfc_interface import NFCInterface
from .nfc_factory import (
    NFCConnectionType,
    get_nfc_handler
)
from .nfc_pn532_spi import NFCTag

__all__ = [
    'NFCInterface',
    'NFCConnectionType',
    'NFCTag',
    'get_nfc_handler'
]