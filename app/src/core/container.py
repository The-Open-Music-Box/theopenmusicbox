# app/src/core/container.py

from eventlet.semaphore import Semaphore

from app.src.config import Config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.gpio.gpio_interface import GPIOInterface
from app.src.module.gpio.gpio_factory import get_gpio_controller

logger = ImprovedLogger(__name__)

class Container:
    def __init__(self, config: Config):
        self._config = config
        self._gpio = None
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

    def cleanup(self):
        if self._gpio:
            self._gpio.cleanup_all()
