"""
Configuration package for the application.
"""
from app.src.config.config_interface import IConfig
from app.src.config.standard_config import StandardConfig
from app.src.config.test_config import TestConfig
from app.src.config.dev_config import DevConfig
from app.src.config.config_factory import ConfigFactory, ConfigType

# Define Config as an alias to StandardConfig for backward compatibility
Config = StandardConfig

# Export main classes and functions
__all__ = ['IConfig', 'StandardConfig', 'TestConfig', 'DevConfig', 'ConfigFactory', 'ConfigType', 'Config']

# For backward compatibility with existing code
config_singleton = ConfigFactory.get_config()
