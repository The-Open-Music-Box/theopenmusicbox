# app/src/module/gpio/gpio_raspberry.py

from typing import Dict, Optional, Any
from threading import Lock
import RPi.GPIO as GPIO

from src.helpers.exceptions import AppError
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .gpio_hardware import GPIOHardware, PinMode

logger = ImprovedLogger(__name__)

class RaspberryGPIO(GPIOHardware):
    def __init__(self, lock) -> None:
        self._global_lock = lock
        self._pwm_instances: Dict[int, Any] = {}

        try:
            GPIO.setmode(GPIO.BCM)
        except Exception as e:
            raise AppError.hardware_error(
                message="Failed to initialize GPIO",
                component="gpio",
                operation="init",
                details={"error": str(e)}
            )

    def setup_pin(self, pin: int, mode: PinMode, initial: Optional[bool] = None, timeout: float = 2.0) -> None:
        with self._global_lock:
            try:
                if mode == PinMode.PWM:
                    GPIO.setup(pin, GPIO.OUT)
                else:
                    GPIO.setup(pin,
                             GPIO.IN if mode == PinMode.INPUT else GPIO.OUT,
                             initial=initial)
            except Exception as e:
                raise AppError.hardware_error(
                    message=f"Failed to setup GPIO pin {pin}",
                    component="gpio",
                    operation="setup_pin",
                    details={"pin": pin, "mode": mode.value, "error": str(e)}
                )

    def read_pin(self, pin: int) -> bool:
        with self._global_lock:
            try:
                return GPIO.input(pin)
            except Exception as e:
                raise AppError.hardware_error(
                    message=f"Failed to read GPIO pin {pin}",
                    component="gpio",
                    operation="read_pin",
                    details={"pin": pin, "error": str(e)}
                )

    def write_pin(self, pin: int, value: bool) -> None:
        with self._global_lock:
            try:
                GPIO.output(pin, value)
            except Exception as e:
                raise AppError.hardware_error(
                    message=f"Failed to write to GPIO pin {pin}",
                    component="gpio",
                    operation="write_pin",
                    details={"pin": pin, "value": value, "error": str(e)}
                )

    def setup_pwm(self, pin: int, frequency: int = 1000) -> Any:
        with self._global_lock:
            try:
                if pin not in self._pwm_instances:
                    self._pwm_instances[pin] = GPIO.PWM(pin, frequency)
                return self._pwm_instances[pin]
            except Exception as e:
                raise AppError.hardware_error(
                    message=f"Failed to setup PWM on pin {pin}",
                    component="gpio",
                    operation="setup_pwm",
                    details={"pin": pin, "frequency": frequency, "error": str(e)}
                )

    def cleanup_pin(self, pin: int) -> None:
        with self._global_lock:
            try:
                if pin in self._pwm_instances:
                    self._pwm_instances[pin].stop()
                    del self._pwm_instances[pin]
                GPIO.cleanup(pin)
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Error cleaning up GPIO pin {pin}: {str(e)}")

    def cleanup_all(self) -> None:
        try:
            with self._global_lock:
                for pin in list(self._pwm_instances.keys()):
                    self.cleanup_pin(pin)
                GPIO.cleanup()
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error during GPIO cleanup: {str(e)}")

    def add_event_detect(self, pin: int, callback: callable, bouncetime: int = 200) -> None:
        with self._global_lock:
            try:
                GPIO.add_event_detect(pin, GPIO.BOTH, callback=callback, bouncetime=bouncetime)
            except Exception as e:
                raise AppError.hardware_error(
                    message=f"Failed to setup event detection on pin {pin}",
                    component="gpio",
                    operation="add_event_detect",
                    details={"pin": pin, "error": str(e)}
                )

    def remove_event_detect(self, pin: int) -> None:
        with self._global_lock:
            try:
                GPIO.remove_event_detect(pin)
            except Exception as e:
                raise AppError.hardware_error(
                    message=f"Failed to remove event detection from pin {pin}",
                    component="gpio",
                    operation="remove_event_detect",
                    details={"pin": pin, "error": str(e)}
                )