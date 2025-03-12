# app/src/module/motor/motor_N2003.py

import eventlet
from typing import Callable
from src.module.gpio.gpio_interface import GPIOInterface, PinMode
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .motor_interface import MotorInterface, MotorDirection

logger = ImprovedLogger(__name__)

class MotorN2003(MotorInterface):
    PINS = {
        'IN1': 16,
        'IN2': 23,
        'IN3': 24,
        'IN4': 25
    }

    SEQUENCE = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]

    def __init__(self, gpio_controller: GPIOInterface):
        self._gpio = gpio_controller
        self._position = 0
        self._running = False
        self._direction = MotorDirection.CLOCKWISE
        self._speed = 0
        self._sequence_index = 0
        self._position_callback = None
        self._acceleration = 1.0

        self._stop_event = eventlet.event.Event()
        self._pin_states = {pin: False for pin in self.PINS.values()}

        self._setup_gpio()
        self._start_control_thread()
        logger.log(LogLevel.INFO, "Motor controller initialized")

    def _setup_gpio(self) -> None:
        for pin in self.PINS.values():
            self._gpio.setup_pin(pin, PinMode.OUTPUT, initial=False, timeout=1.0)
            self._pin_states[pin] = False
        logger.log(LogLevel.INFO, "Motor GPIO setup completed")

    def stop(self) -> None:
        self._running = False
        self._position = 0
        self._sequence_index = 0
        self._set_all_pins_low()
        logger.log(LogLevel.INFO, "Motor stopped")

    def _set_all_pins_low(self) -> None:
        for pin in self.PINS.values():
            self._gpio.write_pin(pin, False)
            self._pin_states[pin] = False

    def subscribe_position(self, callback: Callable[[int], None]) -> None:
        self._position_callback = callback

    def start(self, direction: MotorDirection, speed: int) -> None:
        self._direction = direction
        self._speed = min(max(1, speed), 2000)
        self._running = True
        self._acceleration = min(max(1.0, speed / 500), 4.0)
        logger.log(LogLevel.INFO, "Motor started",
                  direction=direction.value,
                  speed=speed,
                  acceleration=self._acceleration)

    def _control_loop(self) -> None:
        while not self._stop_event.ready():
            if not self._running:
                eventlet.sleep(0.1)
                continue

            base_delay = 1.0 / (self._speed * self._acceleration)
            step_delay = max(0.001, base_delay)

            self._apply_step()

            if self._direction == MotorDirection.CLOCKWISE:
                self._position += 1
                self._sequence_index = (self._sequence_index + 1) % len(self.SEQUENCE)
            else:
                self._position -= 1
                self._sequence_index = (self._sequence_index - 1) % len(self.SEQUENCE)

            if self._position_callback:
                self._position_callback(self._position)

            eventlet.sleep(step_delay)

    def _apply_step(self) -> None:
        sequence = self.SEQUENCE[self._sequence_index]
        try:
            for pin, value in zip(self.PINS.values(), sequence):
                if self._pin_states.get(pin) != bool(value):
                    self._gpio.write_pin(pin, bool(value))
                    self._pin_states[pin] = bool(value)
        except Exception as exc:
            logger.log(LogLevel.ERROR, "Step application error", exc_info=exc)
            self._set_all_pins_low()

    def _start_control_thread(self) -> None:
        self._control_thread = eventlet.spawn(self._control_loop)
        logger.log(LogLevel.INFO, "Control thread started")

    def cleanup(self) -> None:
        logger.log(LogLevel.INFO, "Starting motor cleanup")
        self._stop_event.send()
        self.stop()
        if hasattr(self, '_control_thread'):
            self._control_thread.wait()
        for pin in self.PINS.values():
            self._gpio.cleanup_pin(pin)
        logger.log(LogLevel.INFO, "Motor cleanup completed")
