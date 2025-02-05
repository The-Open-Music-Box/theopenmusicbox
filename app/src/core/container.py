# app/src/core/container.py

from typing import Optional
from eventlet.semaphore import Semaphore

from src.config import Config
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.module.gpio.gpio_interface import GPIOInterface
from src.module.gpio.gpio_factory import get_gpio_controller
from src.module.nfc.nfc_interface import NFCInterface
from src.module.nfc.nfc_factory import get_nfc_handler
from src.helpers.exceptions import AppError

logger = ImprovedLogger(__name__)

class Container:
    def __init__(self, config: Config):
        self._config = config
        self._gpio = None
        self._nfc = None
        self.bus_lock = Semaphore()

    @property
    def gpio(self) -> GPIOInterface:
        if not self._gpio:
            try:
                self._gpio = get_gpio_controller()
                logger.log(LogLevel.INFO, "GPIO initialized")
            except AppError as e:
                logger.log(LogLevel.ERROR, f"GPIO init failed: {e}")
                raise
        return self._gpio

    @property
    def nfc(self) -> Optional[NFCInterface]:
        if not self._nfc:
            try:
                self._nfc = get_nfc_handler(self.bus_lock)
                logger.log(LogLevel.INFO, "NFC initialized")
            except AppError as e:
                logger.log(LogLevel.WARNING, f"NFC hardware not available: {str(e)}")
                self._nfc = None
        return self._nfc

    def cleanup(self):
        logger.log(LogLevel.INFO, "Starting container cleanup")

        # Clean up NFC
        if self._nfc:
            try:
                self._nfc.cleanup()
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cleaning up NFC: {e}")
            self._nfc = None

        # Clean up GPIO
        if self._gpio:
            try:
                self._gpio.cleanup_all()
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cleaning up GPIO: {e}")
            self._gpio = None

        # Release bus lock if held
        try:
            if self.bus_lock and self.bus_lock.locked():
                self.bus_lock.release()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error releasing bus lock: {e}")
