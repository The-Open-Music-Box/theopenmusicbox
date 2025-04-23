# app/src/module/nfc/nfc_mock.py

import time
from typing import Optional
from rx.subject import Subject
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .nfc_hardware import NFCHardware

logger = ImprovedLogger(__name__)

class MockNFC(NFCHardware):
    """
    Mock implementation of NFCHardware for testing and non-hardware environments.
    Simulates NFC tag detection using a timer.
    """
    def __init__(self):
        self._tag_subject = Subject()
        self._running = False
        logger.log(LogLevel.INFO, "Initialized Mock NFC Reader")

    @property
    def tag_subject(self) -> Subject:
        return self._tag_subject

    def read_nfc(self) -> Optional[bytes]:
        # Simulate a tag being read every ~5 seconds
        if int(time.time()) % 5 == 0:
            mock_tag = bytes([0x04, 0xA0, 0x71, 0xA6, 0xDF, 0x61, 0x80])
            self._tag_subject.on_next({
                'uid': '04:A0:71:A6:DF:61:80',
                'raw_uid': mock_tag,
                'timestamp': time.time()
            })
            return mock_tag
        return None

    def start_nfc_reader(self) -> None:
        logger.log(LogLevel.INFO,"Started Mock NFC Reader")
        self._running = True

    def stop_nfc_reader(self) -> None:
        logger.log(LogLevel.INFO,"Stopped Mock NFC Reader")
        self._running = False

    def cleanup(self) -> None:
        logger.log(LogLevel.INFO,"Cleaned up Mock NFC Reader")
        self.stop_nfc_reader()

    def __init__(self):
        self._tag_subject = Subject()
        self._running = False
        logger.log(LogLevel.INFO, "Initialized Mock NFC Reader")

    @property
    def tag_subject(self) -> Subject:
        return self._tag_subject

    def read_nfc(self) -> Optional[bytes]:
        if time.time() % 5 < 0.1:
            mock_tag = bytes([0x04, 0xA0, 0x71, 0xA6, 0xDF, 0x61, 0x80])
            self._tag_subject.on_next({
                'uid': '04:A0:71:A6:DF:61:80',
                'raw_uid': mock_tag,
                'timestamp': time.time()
            })
            return mock_tag
        return None

    def start_nfc_reader(self) -> None:
        logger.log(LogLevel.INFO,"Started Mock NFC Reader")
        self._running = True

    def stop_nfc_reader(self) -> None:
        logger.log(LogLevel.INFO,"Stopped Mock NFC Reader")
        self._running = False

    def cleanup(self) -> None:
        logger.log(LogLevel.INFO,"Cleaned up Mock NFC Reader")
        self.stop_nfc_reader()