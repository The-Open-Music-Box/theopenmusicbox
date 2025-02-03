# app/src/core/container.py

from eventlet.semaphore import Semaphore

from app.src.config import Config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class Container:
    def __init__(self, config: Config):
        self._config = config
        self.bus_lock = Semaphore()


    def cleanup(self):
