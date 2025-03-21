# app/src/module/ledhat/ledhat_interface.py

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any

class LedHatInterface(ABC):
    """
    Abstract interface for controlling an RGB LED strip.
    """

    @abstractmethod
    def clear(self) -> None:
        """Turn off all pixels."""
        pass

    @abstractmethod
    def start_animation(self, animation_name: str, **kwargs) -> None:
        """
        Start a continuous animation in a separate thread.

        Args:
            animation_name: Name of the animation to run
            **kwargs: Animation-specific parameters
        """
        pass

    @abstractmethod
    def stop_animation(self) -> None:
        """Stop the current animation."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up and release resources."""
        pass