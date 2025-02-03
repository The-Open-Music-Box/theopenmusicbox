# app/src/module/gpio/gpio_mock.py

from typing import Dict, Optional, Any
from threading import RLock
from .gpio_interface import GPIOInterface, PinMode

class MockPWM:
    """Simulateur d'instance PWM pour les tests."""
    def __init__(self, frequency: int = 1000):
        self.frequency = frequency
        self.duty_cycle = 0
        self.running = False

    def start(self, duty_cycle: float) -> None:
        self.duty_cycle = duty_cycle
        self.running = True
        print(f"[MockPWM] Started with duty cycle {duty_cycle}%")

    def ChangeDutyCycle(self, duty_cycle: float) -> None:
        self.duty_cycle = duty_cycle
        print(f"[MockPWM] Changed duty cycle to {duty_cycle}%")

    def stop(self) -> None:
        self.running = False
        print("[MockPWM] Stopped")

class MockGPIO(GPIOInterface):
    """Implémentation mock du contrôleur GPIO pour les tests."""

    def __init__(self):
        self._pin_states: Dict[int, bool] = {}
        self._pin_modes: Dict[int, PinMode] = {}
        self._pwm_instances: Dict[int, MockPWM] = {}
        self._pin_locks: Dict[int, RLock] = {}
        print("[MockGPIO] Initialized")

    def setup_pin(self,
                  pin: int,
                  mode: PinMode,
                  initial: Optional[bool] = None,
                  timeout: float = 0) -> None:

        with self._get_pin_lock(pin):
            self._pin_modes[pin] = mode
            if mode == PinMode.OUTPUT:
                self._pin_states[pin] = initial if initial is not None else False
            print(f"[MockGPIO] Pin {pin} setup as {mode.value}" +
                  (f" with initial={initial}" if initial is not None else ""))

    def read_pin(self, pin: int) -> bool:
        with self._get_pin_lock(pin):
            if pin not in self._pin_states:
                raise RuntimeError(f"Pin {pin} not configured")
            value = self._pin_states.get(pin, False)
            print(f"[MockGPIO] Read {value} from pin {pin}")
            return value

    def write_pin(self, pin: int, value: bool) -> None:
        with self._get_pin_lock(pin):
            if self._pin_modes.get(pin) != PinMode.OUTPUT:
                raise RuntimeError(f"Pin {pin} not configured as output")
            self._pin_states[pin] = value
            print(f"[MockGPIO] Write {value} to pin {pin}")

    def setup_pwm(self, pin: int, frequency: int = 1000) -> MockPWM:
        with self._get_pin_lock(pin):
            if pin in self._pwm_instances:
                return self._pwm_instances[pin]

            self._pin_modes[pin] = PinMode.PWM
            pwm = MockPWM(frequency)
            self._pwm_instances[pin] = pwm
            print(f"[MockGPIO] Setup PWM on pin {pin} with frequency {frequency}Hz")
            return pwm

    def cleanup_pin(self, pin: int) -> None:
        with self._get_pin_lock(pin):
            if pin in self._pwm_instances:
                self._pwm_instances[pin].stop()
                del self._pwm_instances[pin]
            if pin in self._pin_states:
                del self._pin_states[pin]
            if pin in self._pin_modes:
                del self._pin_modes[pin]
            print(f"[MockGPIO] Cleaned up pin {pin}")

    def cleanup_all(self) -> None:
        for pin in list(self._pin_modes.keys()):
            self.cleanup_pin(pin)
        self._pin_states.clear()
        self._pin_modes.clear()
        self._pwm_instances.clear()
        print("[MockGPIO] All pins cleaned up")

    def _get_pin_lock(self, pin: int) -> RLock:
        if pin not in self._pin_locks:
            self._pin_locks[pin] = RLock()
        return self._pin_locks[pin]

    def add_event_detect(self, pin: int, callback: callable, bouncetime: int = 200) -> None:
        with self._get_pin_lock(pin):
            print(f"[MockGPIO] Added event detect on pin {pin}")

    def remove_event_detect(self, pin: int) -> None:
        with self._get_pin_lock(pin):
            print(f"[MockGPIO] Removed event detect on pin {pin}")
