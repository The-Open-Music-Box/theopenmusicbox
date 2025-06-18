"""Controls Hardware Mock Implementation.

Provides a mock implementation of the ControlesHardware protocol for development and testing.
This implementation simulates hardware behavior without requiring physical GPIO access.

It can be used for:
- Development on non-Raspberry Pi environments
- Testing the control system logic without hardware
- Simulating hardware events in a controlled manner
"""

import threading
import time
from typing import Any, Callable, Dict

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class ControlesMock:
    """Mock implementation of the ControlesHardware protocol.

    Simulates hardware behavior for buttons and rotary encoders. Always
    reports as available and provides simulated responses.
    """

    def __init__(self):
        """Initialize the mock hardware controller."""
        self._pin_states: Dict[int, bool] = {}
        self._button_callbacks: Dict[int, Callable[[bool], None]] = {}
        self._rotary_callbacks: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        logger.log(LogLevel.INFO, "Initialized mock controls hardware")

    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        """Set up a simulated GPIO pin as an input.

        Args:
            pin: The GPIO pin number
            pull_up: Whether to enable pull-up resistor (True) or pull-down (False)
        """
        with self._lock:
            # Initialize the pin state based on pull-up/pull-down
            self._pin_states[pin] = pull_up
            logger.log(
                LogLevel.DEBUG, f"Set up mock input on pin {pin} (pull_up={pull_up})"
            )

    def setup_button(
        self, pin: int, callback: Callable[[bool], None], pull_up: bool = True
    ) -> None:
        """Set up a simulated button on a GPIO pin.

        Args:
            pin: The GPIO pin number
            callback: Function to call when button state changes (receives state as parameter)
            pull_up: Whether to enable pull-up resistor (True) or pull-down (False)
        """
        with self._lock:
            # Initialize the pin state and store the callback
            self._pin_states[pin] = pull_up
            self._button_callbacks[pin] = callback
            logger.log(
                LogLevel.DEBUG, f"Set up mock button on pin {pin} (pull_up={pull_up})"
            )

    def setup_rotary_encoder(
        self,
        clk_pin: int,
        dt_pin: int,
        callback: Callable[[bool], None],
        pull_up: bool = True,
    ) -> None:
        """Set up a simulated rotary encoder on a pair of GPIO pins.

        Args:
            clk_pin: The CLK pin of the rotary encoder
            dt_pin: The DT pin of the rotary encoder
            callback: Function to call when encoder is rotated (receives True for clockwise, False for counter-clockwise)
            pull_up: Whether to enable pull-up resistors (True) or pull-down (False)
        """
        with self._lock:
            # Initialize the pin states
            self._pin_states[clk_pin] = pull_up
            self._pin_states[dt_pin] = pull_up

            # Store the rotary encoder configuration
            self._rotary_callbacks[clk_pin] = {"dt_pin": dt_pin, "callback": callback}

            logger.log(
                LogLevel.DEBUG,
                f"Set up mock rotary encoder on CLK={clk_pin}, DT={dt_pin}",
            )

    def read_input(self, pin: int) -> bool:
        """Read the simulated state of a GPIO input.

        Args:
            pin: The GPIO pin number

        Returns:
            The current state of the pin (True for HIGH, False for LOW)
        """
        with self._lock:
            # Return the stored pin state or default to False if not initialized
            return self._pin_states.get(pin, False)

    def simulate_button_press(self, pin: int) -> None:
        """Simulate a button press event.

        Args:
            pin: The GPIO pin number of the button to simulate
        """
        if pin not in self._button_callbacks:
            logger.log(LogLevel.WARNING, f"No button callback registered for pin {pin}")
            return

        # Get the callback
        callback = self._button_callbacks[pin]

        # Simulate button press (usually inverts the default state)
        logger.log(LogLevel.DEBUG, f"Simulating button press on pin {pin}")
        callback(True)

        # Execute in a new thread to avoid blocking
        threading.Thread(target=self._simulate_button_release, args=(pin,)).start()

    def _simulate_button_release(self, pin: int) -> None:
        """Simulate a button release event after a short delay.

        Args:
            pin: The GPIO pin number of the button to simulate
        """
        # Wait a moment before releasing
        time.sleep(0.1)

        # If the button callback still exists, simulate release
        if pin in self._button_callbacks:
            callback = self._button_callbacks[pin]
            logger.log(LogLevel.DEBUG, f"Simulating button release on pin {pin}")
            callback(False)

    def simulate_rotary_turn(self, clk_pin: int, clockwise: bool = True) -> None:
        """Simulate a rotary encoder turn event.

        Args:
            clk_pin: The CLK pin of the rotary encoder to simulate
            clockwise: Whether to simulate clockwise (True) or counter-clockwise (False) rotation
        """
        if clk_pin not in self._rotary_callbacks:
            logger.log(
                LogLevel.WARNING,
                f"No rotary encoder callback registered for CLK pin {clk_pin}",
            )
            return

        # Get the callback
        callback = self._rotary_callbacks[clk_pin]["callback"]

        # Simulate rotation
        direction = "clockwise" if clockwise else "counter-clockwise"
        logger.log(
            LogLevel.DEBUG,
            f"Simulating rotary encoder turn ({direction}) on CLK pin {clk_pin}",
        )
        callback(clockwise)

    def cleanup(self) -> None:
        """Clean up the mock hardware resources."""
        with self._lock:
            self._pin_states.clear()
            self._button_callbacks.clear()
            self._rotary_callbacks.clear()
            logger.log(LogLevel.DEBUG, "Mock controls hardware cleaned up")

    def is_available(self) -> bool:
        """Check if the hardware is available for use.

        Always returns True for the mock implementation.

        Returns:
            True (always available)
        """
        return True
