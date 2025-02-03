# app/src/module/nfc/nfc_pn532_i2c.py

from typing import Optional
import eventlet
from eventlet import spawn_n, Event
from eventlet.semaphore import Semaphore
import board
import busio
import time
from rx.subject import Subject
from adafruit_pn532.i2c import PN532_I2C

from app.src.helpers.exceptions import AppError, ErrorSeverity
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .nfc_interface import NFCInterface

logger = ImprovedLogger(__name__)

class NFCPN532I2C(NFCInterface):
    READ_TIMEOUT = 0.1
    RETRY_DELAY = 0.1
    TAG_COOLDOWN = 1.0
    MAX_ERRORS = 3

    def __init__(self, lock: Semaphore) -> None:
        self._lock = lock
        self._pn532 = None
        self._tag_subject = Subject()
        self._stop_event = Event()
        self._last_tag = None
        self._last_read_time = 0

        try:
            self._initialize_hardware()
            logger.log(LogLevel.INFO, "NFC I2C controller initialized")
        except Exception as e:
            logger.log(LogLevel.ERROR, "NFC initialization failed", exc_info=e)
            raise AppError.hardware_error(
                message="Failed to initialize NFC controller",
                component="nfc",
                operation="init",
                details={"error": str(e)},
                severity=ErrorSeverity.HIGH
            )

    def _initialize_hardware(self) -> None:
        try:
            with self._lock:
                i2c = busio.I2C(board.SCL, board.SDA)
                self._pn532 = PN532_I2C(i2c, debug=False)
                ic, ver, rev, support = self._pn532.firmware_version
                logger.log(LogLevel.INFO, f"Found PN532 with firmware version: {ic} {ver}.{rev} - {support}")
                self._pn532.SAM_configuration()
        except Exception as e:
            raise AppError.hardware_error(
                message="Failed to initialize NFC hardware",
                component="nfc",
                operation="init_hardware",
                details={"error": str(e)},
                severity=ErrorSeverity.HIGH
            )

    def read_nfc(self) -> Optional[str]:
        if not self._pn532:
            return None

        try:
            with self._lock:
                uid = self._pn532.read_passive_target(timeout=self.READ_TIMEOUT)
                if not uid:
                    return None

                return self._process_tag(uid)

        except (RuntimeError, OSError):
            return None

        except Exception as e:
            if not str(e).startswith("No card") and "timeout" not in str(e).lower():
                logger.log(LogLevel.ERROR, "NFC read error", exc_info=e)
            return None

    def _process_tag(self, uid: bytes) -> Optional[str]:
        uid_string = ':'.join([hex(i)[2:].zfill(2) for i in uid])
        current_time = time.time()

        if (uid_string == self._last_tag and
            current_time - self._last_read_time < self.TAG_COOLDOWN):
            return None

        self._last_tag = uid_string
        self._last_read_time = current_time

        self._tag_subject.on_next({
            'uid': uid_string,
            'timestamp': current_time
        })

        logger.log(LogLevel.INFO, f"Tag read: {uid_string}")
        return uid_string

    def _nfc_reader_loop(self) -> None:
        logger.log(LogLevel.INFO, "Starting reader loop")
        error_count = 0

        while not self._stop_event.ready():
            try:
                if error_count >= self.MAX_ERRORS:
                    self._initialize_hardware()
                    error_count = 0

                if self.read_nfc():
                    error_count = 0

                eventlet.sleep(self.RETRY_DELAY)

            except Exception as e:
                error_count += 1
                logger.log(LogLevel.ERROR, "Reader loop error", exc_info=e)
                eventlet.sleep(min(2 ** error_count, 10))  # backoff exponentiel

    def start_nfc_reader(self) -> None:
        spawn_n(self._nfc_reader_loop)
        logger.log(LogLevel.INFO, "Reader started")

    def stop_nfc_reader(self) -> None:
        self._stop_event.send()
        logger.log(LogLevel.INFO, "Reader stopped")

    def cleanup(self) -> None:
        try:
            logger.log(LogLevel.INFO, "Starting cleanup")
            self.stop_nfc_reader()

            with self._lock:
                if self._pn532:
                    self._pn532 = None
                    logger.log(LogLevel.INFO, "Hardware released")

        except Exception as e:
            raise AppError.hardware_error(
                message="Failed to cleanup NFC device",
                component="nfc",
                operation="cleanup",
                details={"error": str(e)},
                severity=ErrorSeverity.HIGH
            )

    @property
    def tag_subject(self) -> Subject:
        return self._tag_subject