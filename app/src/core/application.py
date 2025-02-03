# app/src/core/application.py

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .container import Container

logger = ImprovedLogger(__name__)

class Application:
    def __init__(self, container: Container):
        self._container = container
    def cleanup(self):
        if self._container:
            self._container.cleanup()
