"""Button Input Device Module.

Provides a Button class that wraps the hardware-specific button
implementation and emits control events when pressed or released.
"""

from rx.subject import Subject

from app.src.module.controles.controles_hardware import ControlesHardware
from app.src.module.controles.events.controles_events import (
    ControlesEvent,
    ControlesEventType,
)
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class Button:
    """Button input device.

    Wraps a physical button connected to a GPIO pin and emits control
    events when the button is pressed or released.
    """

    def __init__(
        self,
        hardware: ControlesHardware,
        pin: int,
        event_type: ControlesEventType,
        name: str,
        event_subject: Subject,
        pull_up: bool = True,
    ):
        """Initialize a button on a specific GPIO pin.

        Args:
            hardware: The hardware implementation to use
            pin: The GPIO pin number the button is connected to
            event_type: The event type to emit when button is pressed
            name: A human-readable name for this button
            event_subject: The RxPy Subject to emit events to
            pull_up: Whether to enable pull-up resistor (True) or pull-down (False)
        """
        self.hardware = hardware
        self.pin = pin
        self.event_type = event_type
        self.name = name
        self.event_subject = event_subject
        self.pull_up = pull_up

        # Set up the button in hardware
        if hardware.is_available():
            hardware.setup_button(pin, self._on_button_state_change, pull_up)
            logger.log(LogLevel.INFO, f"Button '{name}' initialized on pin {pin}")
        else:
            logger.log(
                LogLevel.WARNING,
                f"Hardware not available. Button '{name}' will not function.",
            )

    def _on_button_state_change(self, pressed: bool) -> None:
        """Handle button state changes.

        This callback is invoked by the hardware when the button changes state.
        If the button is pressed, emit the configured event.

        Args:
            pressed: True if button is pressed, False if released
        """
        # Only emit event on button press, not release
        if pressed:
            event = ControlesEvent(
                event_type=self.event_type,
                source=f"button:{self.name}",
                metadata={"pin": self.pin, "pressed": pressed},
            )

            logger.log(
                LogLevel.DEBUG,
                f"Button '{self.name}' pressed, emitting {self.event_type.name}",
            )
            self.event_subject.on_next(event)
