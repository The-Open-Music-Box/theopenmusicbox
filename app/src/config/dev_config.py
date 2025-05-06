"""
Development configuration with mock hardware enabled.
Used for local development and testing without physical hardware.
"""
from app.src.config.standard_config import StandardConfig


class DevConfig(StandardConfig):
    """
    Development configuration with mock hardware enabled.
    Extends StandardConfig with development-specific settings.
    """
    
    def __init__(self):
        super().__init__()
    
    @property
    def use_mock_hardware(self) -> bool:
        """Whether to use mock hardware (always True for development)."""
        return True
