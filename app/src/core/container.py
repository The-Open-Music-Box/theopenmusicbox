# app/src/core/container.py

from eventlet.semaphore import Semaphore

from app.src.config import Config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.gpio.gpio_interface import GPIOInterface
from app.src.module.gpio.gpio_factory import get_gpio_controller
from app.src.module.nfc.nfc_interface import NFCInterface
from app.src.module.nfc.nfc_factory import get_nfc_handler

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
            except Exception as e:
                logger.log(LogLevel.ERROR, f"GPIO init failed: {e}")
                raise
        return self._gpio

    @property
    def nfc(self) -> NFCInterface:
        if not self._nfc:
            self._nfc = get_nfc_handler(self.bus_lock)
            logger.log(LogLevel.INFO, "NFC initialized")
        return self._nfc

    def cleanup(self):
        if self._nfc:
            self._nfc.cleanup()
        if self._gpio:
            self._gpio.cleanup_all()
