# app/src/module/motor/motor_mock.py


from typing import Callable
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .motor_hardware import MotorHardware, MotorDirection

logger = ImprovedLogger(__name__)

class MockMotor(MotorHardware):
    """
    Mock implementation of MotorHardware for testing and non-hardware environments.
    Simulates motor state and position.
    """
    def __init__(self):
        self._position = 0
        self._running = False
        self._direction = MotorDirection.CLOCKWISE
        self._speed = 0
        self._position_callback = None

    def start(self, direction: MotorDirection, speed: float) -> None:
        logger.log(LogLevel.INFO, f"Mock motor started: direction={direction.value}, speed={speed}RPM")
        self._running = True
        # Simulate position change if callback is set
        if self._position_callback:
            self._position += 10
            self._position_callback(self._position)

    def stop(self) -> None:
        logger.log(LogLevel.INFO, "Mock motor stopped")
        self._running = False

    def subscribe_position(self, callback: Callable[[int], None]) -> None:
        self._position_callback = callback

    def cleanup(self) -> None:
        self.stop()
        logger.log(LogLevel.INFO, "Mock motor cleaned up")

    def __init__(self):
        self._position = 0
        self._running = False
        self._direction = MotorDirection.CLOCKWISE
        self._speed = 0
        self._position_callback = None

    def start(self, direction: MotorDirection, speed: float) -> None:
        logger.log(LogLevel.INFO, f"Mock motor started: direction={direction.value}, speed={speed}RPM")
        self._running = True

    def stop(self) -> None:
        logger.log(LogLevel.INFO, "Mock motor stopped")
        self._running = False

    def subscribe_position(self, callback: Callable[[int], None]) -> None:
        self._position_callback = callback

    def cleanup(self) -> None:
        self.stop()
        logger.log(LogLevel.INFO, "Mock motor cleaned up")
