# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""NFC Reader module for contactless tag detection and reading.

This module provides a platform-independent interface for NFC operations,
with implementations for both Raspberry Pi hardware (PN532 via I2C)
and mock. Features include:
- Support for connection types I2C
- Continuous tag monitoring in separate thread
- Debounced tag reading
- Reactive tag event streaming
- Thread-safe bus access
"""

from .nfc_factory import get_nfc_handler

__all__ = ["get_nfc_handler"]
