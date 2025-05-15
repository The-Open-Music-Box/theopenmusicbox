"""
Rotary Encoder Input Device Module

Provides a RotaryEncoder class that wraps the hardware-specific rotary encoder implementation
and emits control events when rotated clockwise or counter-clockwise.
"""

from typing import Optional
from rx.subject import Subject

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.controles.controles_hardware import ControlesHardware
from app.src.module.controles.events.controles_events import ControlesEvent, ControlesEventType

logger = ImprovedLogger(__name__)

class RotaryEncoder:
    """
    Rotary Encoder input device.
    
    Wraps a physical KY-040 rotary encoder connected to GPIO pins and emits
    control events when rotated clockwise or counter-clockwise.
    """
    
    def __init__(self, 
                hardware: ControlesHardware,
                clk_pin: int, 
                dt_pin: int,
                name: str,
                clockwise_event_type: ControlesEventType,
                counter_clockwise_event_type: ControlesEventType,
                event_subject: Subject,
                sw_pin: Optional[int] = None,
                sw_event_type: Optional[ControlesEventType] = None,
                pull_up: bool = True):
        """
        Initialize a rotary encoder on specific GPIO pins.
        
        Args:
            hardware: The hardware implementation to use
            clk_pin: The CLK pin of the rotary encoder
            dt_pin: The DT pin of the rotary encoder
            name: A human-readable name for this rotary encoder
            clockwise_event_type: The event type to emit when rotated clockwise
            counter_clockwise_event_type: The event type to emit when rotated counter-clockwise
            event_subject: The RxPy Subject to emit events to
            sw_pin: Optional switch pin for encoders with integrated button
            sw_event_type: Event type to emit when switch is pressed
            pull_up: Whether to enable pull-up resistors (True) or pull-down (False)
        """
        self.hardware = hardware
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.name = name
        self.clockwise_event_type = clockwise_event_type
        self.counter_clockwise_event_type = counter_clockwise_event_type
        self.sw_event_type = sw_event_type
        self.event_subject = event_subject
        self.pull_up = pull_up
        
        # Set up the rotary encoder in hardware
        if hardware.is_available():
            # Set up rotation detection
            hardware.setup_rotary_encoder(
                clk_pin, 
                dt_pin, 
                self._on_rotation, 
                pull_up
            )
            
            # Set up switch if provided
            if sw_pin is not None and sw_event_type is not None:
                hardware.setup_button(sw_pin, self._on_switch_change, pull_up)
                logger.log(LogLevel.INFO, 
                          f"Rotary encoder '{name}' initialized on pins CLK={clk_pin}, DT={dt_pin}, SW={sw_pin}")
            else:
                logger.log(LogLevel.INFO, 
                          f"Rotary encoder '{name}' initialized on pins CLK={clk_pin}, DT={dt_pin}")
        else:
            logger.log(LogLevel.WARNING, f"Hardware not available. Rotary encoder '{name}' will not function.")
    
    def _on_rotation(self, clockwise: bool) -> None:
        """
        Handle rotary encoder rotation events.
        
        This callback is invoked by the hardware when the encoder is rotated.
        
        Args:
            clockwise: True if rotated clockwise, False if counter-clockwise
        """
        # Determine which event type to emit based on rotation direction
        if clockwise:
            event_type = self.clockwise_event_type
            direction = "clockwise"
        else:
            event_type = self.counter_clockwise_event_type
            direction = "counter-clockwise"
        
        # Create and emit the event
        event = ControlesEvent(
            event_type=event_type,
            source=f"rotary:{self.name}",
            metadata={
                "clk_pin": self.clk_pin,
                "dt_pin": self.dt_pin,
                "direction": direction
            }
        )
        
        logger.log(LogLevel.DEBUG, 
                  f"Rotary encoder '{self.name}' rotated {direction}, emitting {event_type.name}")
        self.event_subject.on_next(event)
    
    def _on_switch_change(self, pressed: bool) -> None:
        """
        Handle rotary encoder switch events.
        
        This callback is invoked by the hardware when the encoder's switch is pressed.
        
        Args:
            pressed: True if switch is pressed, False if released
        """
        # Only emit event on switch press, not release
        if pressed and self.sw_event_type is not None:
            event = ControlesEvent(
                event_type=self.sw_event_type,
                source=f"rotary_switch:{self.name}",
                metadata={
                    "sw_pin": self.sw_pin,
                    "pressed": pressed
                }
            )
            
            logger.log(LogLevel.DEBUG, 
                      f"Rotary encoder '{self.name}' switch pressed, emitting {self.sw_event_type.name}")
            self.event_subject.on_next(event)
