"""
Controls Hardware Protocol Definition

Defines the interface (Protocol) for all controls hardware implementations.
This abstraction ensures that both real and mock hardware implementations
provide a consistent set of methods for device initialization, monitoring, and cleanup.

Business Logic and Architectural Notes:
- All hardware-specific control logic must be implemented in a class conforming to this Protocol.
- The Protocol enables architectural boundaries and allows seamless switching between real and mock hardware.
- This promotes maintainability, testability, and platform independence.
"""

from typing import Protocol, Callable, Any, Optional

class ControlesHardware(Protocol):
    """
    Protocol for controls hardware implementations.
    
    Implementations must provide methods for monitoring GPIO pins,
    handling events, and cleaning up resources.
    """
    
    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        """
        Set up a GPIO pin as an input.
        
        Args:
            pin: The GPIO pin number
            pull_up: Whether to enable pull-up resistor (True) or pull-down (False)
        """
        pass
    
    def setup_button(self, pin: int, callback: Callable[[bool], None], pull_up: bool = True) -> None:
        """
        Set up a GPIO pin as a button input with event detection.
        
        Args:
            pin: The GPIO pin number
            callback: Function to call when button state changes (receives state as parameter)
            pull_up: Whether to enable pull-up resistor (True) or pull-down (False)
        """
        pass
    
    def setup_rotary_encoder(self, 
                            clk_pin: int, 
                            dt_pin: int, 
                            callback: Callable[[bool], None],
                            pull_up: bool = True) -> None:
        """
        Set up a pair of GPIO pins as a rotary encoder.
        
        Args:
            clk_pin: The CLK pin of the rotary encoder
            dt_pin: The DT pin of the rotary encoder
            callback: Function to call when encoder is rotated (receives True for clockwise, False for counter-clockwise)
            pull_up: Whether to enable pull-up resistors (True) or pull-down (False)
        """
        pass
    
    def read_input(self, pin: int) -> bool:
        """
        Read the current state of a GPIO input.
        
        Args:
            pin: The GPIO pin number
            
        Returns:
            The current state of the pin (True for HIGH, False for LOW)
        """
        pass
    
    def cleanup(self) -> None:
        """
        Release hardware resources and perform any necessary cleanup.
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if the hardware is available for use.
        
        Returns:
            True if the hardware is available, False otherwise
        """
        pass
