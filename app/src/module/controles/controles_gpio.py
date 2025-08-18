# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Controls Hardware GPIO Implementation.

Provides a concrete implementation of the ControlesHardware protocol
using gpiozero with lgpio backend for Raspberry Pi.

This implementation handles direct communication with GPIO pins for
buttons and rotary encoders.
"""

import threading
import time
from typing import Callable, Dict

try:
    # Import gpiozero for Raspberry Pi GPIO access
    from gpiozero import Button as GPIOButton
    from gpiozero import DigitalInputDevice
    from gpiozero.pins.lgpio import LGPIOFactory

    # Set up gpiozero to use lgpio backend
    pin_factory = LGPIOFactory()
    GPIO_AVAILABLE = True
except ImportError:
    # GPIO libraries not available
    GPIO_AVAILABLE = False

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class ControlesGPIO:
    """GPIO-based implementation of the ControlesHardware protocol.

    Uses gpiozero with lgpio backend to interact with physical GPIO
    pins. Manages pin setup, event detection, and cleanup for buttons
    and rotary encoders.
    """

    def __init__(self):
        """Initialize the GPIO controller."""
        self._inputs: Dict[int, DigitalInputDevice] = {}
        self._buttons: Dict[int, GPIOButton] = {}
        self._rotary_states: Dict[int, Dict[str, any]] = {}
        self._lock = threading.Lock()

        # Check if GPIO is available
        if not GPIO_AVAILABLE:
            logger.log(
                LogLevel.WARNING,
                "GPIO libraries not available. Hardware controls disabled.",
            )

    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        """Set up a GPIO pin as an input.

        Args:
            pin: The GPIO pin number
            pull_up: Whether to enable pull-up resistor (True) or pull-down (False)
        """
        if not GPIO_AVAILABLE:
            return

        try:
            # Create DigitalInputDevice with pull-up or pull-down
            self._inputs[pin] = DigitalInputDevice(
                pin=pin, pull_up=pull_up, pin_factory=pin_factory
            )
            logger.log(LogLevel.DEBUG, f"Set up GPIO input on pin {pin}")
        except Exception as e:
            logger.log(
                LogLevel.ERROR, f"Failed to set up GPIO input on pin {pin}: {str(e)}"
            )

    def setup_button(
        self, pin: int, callback: Callable[[bool], None], pull_up: bool = True
    ) -> None:
        """Set up a GPIO pin as a button input with event detection.

        Args:
            pin: The GPIO pin number
            callback: Function to call when button state changes (receives state as parameter)
            pull_up: Whether to enable pull-up resistor (True) or pull-down (False)
        """
        if not GPIO_AVAILABLE:
            return

        try:
            # Create GPIOButton with debounce
            self._buttons[pin] = GPIOButton(
                pin=pin,
                pull_up=pull_up,
                bounce_time=0.05,  # 50ms hardware debounce
                pin_factory=pin_factory,
            )

            # Set up callback only for button press (not release)
            # This prevents double-triggering on press+release
            def press_only_callback():
                logger.log(LogLevel.INFO, f"[GPIO] Button PRESS detected on pin {pin}")
                # Always pass True for press event
                callback(True)
            
            # Only set when_pressed, explicitly set when_released to None
            self._buttons[pin].when_pressed = press_only_callback
            self._buttons[pin].when_released = None  # Explicitly disable release callback
            
            # Log current button state
            logger.log(LogLevel.INFO, f"[GPIO] Button on pin {pin} initial state: {'pressed' if self._buttons[pin].is_pressed else 'released'}")

            logger.log(LogLevel.DEBUG, f"Set up button on GPIO pin {pin}")
        except Exception as e:
            logger.log(
                LogLevel.ERROR, f"Failed to set up button on GPIO pin {pin}: {str(e)}"
            )

    def setup_rotary_encoder(
        self,
        clk_pin: int,
        dt_pin: int,
        callback: Callable[[bool], None],
        pull_up: bool = True,
    ) -> None:
        """Set up a pair of GPIO pins as a rotary encoder.

        Args:
            clk_pin: The CLK pin of the rotary encoder
            dt_pin: The DT pin of the rotary encoder
            callback: Function to call when encoder is rotated (receives True for clockwise, False for counter-clockwise)
            pull_up: Whether to enable pull-up resistors (True) or pull-down (False)
        """
        if not GPIO_AVAILABLE:
            return

        try:
            # Set up input devices for CLK and DT pins
            self.setup_input(clk_pin, pull_up)
            self.setup_input(dt_pin, pull_up)

            # Initialize rotary encoder state
            self._rotary_states[clk_pin] = {
                "clk_pin": clk_pin,
                "dt_pin": dt_pin,
                "callback": callback,
                "last_clk": self.read_input(clk_pin),
                "last_dt": self.read_input(dt_pin),
                "last_time": time.time(),
                "debounce_time": 0.01,  # 10ms software debounce
            }

            # Set up state change detection using event monitoring
            clk_device = self._inputs[clk_pin]

            # Add our custom handler for value changes
            clk_device.when_activated = lambda: self._handle_rotary_state_change(
                clk_pin
            )
            clk_device.when_deactivated = lambda: self._handle_rotary_state_change(
                clk_pin
            )

            logger.log(
                LogLevel.DEBUG,
                f"Set up rotary encoder on GPIO pins CLK={clk_pin}, DT={dt_pin}",
            )
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Failed to set up rotary encoder on GPIO pins CLK={clk_pin}, DT={dt_pin}: {str(e)}",
            )

    def _handle_rotary_state_change(self, clk_pin: int) -> None:
        """Handle a rotary encoder state change.

        This is called when the CLK pin changes state.

        Args:
            clk_pin: The CLK pin of the rotary encoder
        """
        with self._lock:
            if clk_pin not in self._rotary_states:
                return

            state = self._rotary_states[clk_pin]
            dt_pin = state["dt_pin"]
            callback = state["callback"]
            now = time.time()

            # Software debounce
            if now - state["last_time"] < state["debounce_time"]:
                return

            # Read current states
            clk = self.read_input(clk_pin)
            dt = self.read_input(dt_pin)

            # Detect rotation direction
            if clk != state["last_clk"]:
                # CLK changed
                if clk == 0:  # Falling edge of CLK
                    if dt != clk:
                        # DT is different from CLK: counter-clockwise
                        callback(False)
                    else:
                        # DT is same as CLK: clockwise
                        callback(True)

            # Update state
            state["last_clk"] = clk
            state["last_dt"] = dt
            state["last_time"] = now

    def read_input(self, pin: int) -> bool:
        """Read the current state of a GPIO input.

        Args:
            pin: The GPIO pin number

        Returns:
            The current state of the pin (True for HIGH, False for LOW)
        """
        if not GPIO_AVAILABLE or pin not in self._inputs:
            return False

        return self._inputs[pin].value == 1

    def cleanup(self) -> None:
        """Release hardware resources and perform any necessary cleanup."""
        if not GPIO_AVAILABLE:
            return

        # Close all inputs and buttons
        for device in list(self._inputs.values()) + list(self._buttons.values()):
            try:
                device.close()
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Error closing GPIO device: {str(e)}")

        # Clear internal state
        self._inputs.clear()
        self._buttons.clear()
        self._rotary_states.clear()

        logger.log(LogLevel.DEBUG, "GPIO resources cleaned up")

    def is_available(self) -> bool:
        """Check if the hardware is available for use.

        Returns:
            True if the hardware is available, False otherwise
        """
        return GPIO_AVAILABLE
