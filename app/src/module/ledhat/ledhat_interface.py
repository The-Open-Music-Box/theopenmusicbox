# app/src/module/ledhat/ledhat_interface.py

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any

class LedHatInterface(ABC):
    """
    Abstract interface for controlling an RGB LED strip.
    """

    @abstractmethod
    def set_pixel(self, i: int, color: Tuple[int, int, int]) -> None:
        """
        Set the color of a specific pixel.

        Args:
            i: Pixel index
            color: RGB tuple (r, g, b) with values from 0 to 255
        """
        pass

    @abstractmethod
    def set_all_pixels(self, color: Tuple[int, int, int]) -> None:
        """
        Set all pixels to the same color.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
        """
        pass

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
    def close(self) -> None:
        """Clean up and release resources."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Alias for close() for container compatibility."""
        pass

    @property
    @abstractmethod
    def current_animation(self) -> Optional[str]:
        """Returns the name of the current animation, or None if no animation is running."""
        pass

    @property
    @abstractmethod
    def animation_params(self) -> Dict[str, Any]:
        """Returns the parameters of the current animation."""
        pass