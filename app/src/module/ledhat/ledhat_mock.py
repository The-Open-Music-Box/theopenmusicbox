# app/src/module/ledhat/ledhat_mock.py

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat_hardware import LedHatHardware

logger = ImprovedLogger(__name__)

class MockLedHat(LedHatHardware):
    """
    Mock implementation of the LedHatInterface for testing and development environments.
    Logs all actions instead of controlling real hardware.
    """
    def __init__(self):
        logger.log(LogLevel.INFO, "Initialized Mock LED Hat.")
        self._running = False
        self._current_animation = None
        self._animation_params = {}

    def clear(self) -> None:
        logger.log(LogLevel.INFO, "MockLedHat: clear() called. All pixels turned off (simulated).")

    def start_animation(self, animation_name: str, **kwargs) -> None:
        logger.log(LogLevel.INFO, f"MockLedHat: start_animation('{animation_name}', {kwargs}) called. Animation started (simulated).")
        self._running = True
        self._current_animation = animation_name
        self._animation_params = kwargs

    def stop_animation(self) -> None:
        logger.log(LogLevel.INFO, "MockLedHat: stop_animation() called. Animation stopped (simulated).")
        self._running = False
        self._current_animation = None
        self._animation_params = {}

    def cleanup(self) -> None:
        logger.log(LogLevel.INFO, "MockLedHat: cleanup() called. Resources released (simulated).")
        self.stop_animation()
        self.clear()
