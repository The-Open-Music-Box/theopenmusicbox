"""
Backward compatibility module for configuration.
This file redirects to the new configuration architecture while maintaining compatibility
with existing code that imports from this module.
"""
from app.src.config.config_interface import IConfig
from app.src.config.standard_config import StandardConfig
from app.src.config.config_factory import ConfigFactory, ConfigType
from app.src.config.test_config import TestConfig

# Re-export the Config class for backward compatibility
Config = StandardConfig

# Re-export the singleton instance
config_singleton = ConfigFactory.get_config()

# Export everything else to maintain the API
__all__ = ['Config', 'config_singleton', 'IConfig', 'ConfigFactory', 'ConfigType', 'TestConfig']
