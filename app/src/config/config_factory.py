"""
Factory for creating and accessing different configurations.
"""
from enum import Enum, auto
from typing import Optional

from app.src.config.config_interface import IConfig
from app.src.config.standard_config import StandardConfig
from app.src.config.test_config import TestConfig
from app.src.config.dev_config import DevConfig


class ConfigType(Enum):
    """Available configuration types."""
    STANDARD = auto()
    TEST = auto()
    DEV = auto()


class ConfigFactory:
    """Factory for creating and accessing configuration objects."""
    
    _instance = None  # Singleton instance
    _current_config = None  # Currently active configuration
    
    @classmethod
    def get_config(cls, config_type: Optional[ConfigType] = None, **kwargs) -> IConfig:
        """
        Get or create a configuration.
        
        Args:
            config_type: Configuration type (if None, uses the active configuration or STANDARD by default)
            **kwargs: Additional arguments for specific configuration creation
            
        Returns:
            A configuration instance
        """
        if cls._instance is None:
            cls._instance = cls()
            
        if config_type is None:
            # Return active configuration or create a standard configuration by default
            if cls._current_config is None:
                cls._current_config = StandardConfig()
            return cls._current_config
            
        # Create a new configuration of the requested type
        if config_type == ConfigType.STANDARD:
            cls._current_config = StandardConfig()
        elif config_type == ConfigType.TEST:
            cls._current_config = TestConfig(**kwargs)
        elif config_type == ConfigType.DEV:
            cls._current_config = DevConfig()
        else:
            raise ValueError(f"Unknown config type: {config_type}")
            
        return cls._current_config
    
    @classmethod
    def reset(cls):
        """Reset the factory to its default state (useful for tests)."""
        cls._current_config = None
