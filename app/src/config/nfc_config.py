"""
Configuration parameters for NFC hardware and detection logic.

This module provides a dedicated configuration class for NFC-related settings,
allowing for centralized management and injection of these parameters.
"""
from dataclasses import dataclass

@dataclass
class NFCConfig:
    """Configuration parameters for NFC hardware and detection logic."""
    
    # Hardware settings
    read_timeout: float = 0.1
    retry_delay: float = 0.1
    
    # Tag detection settings
    tag_cooldown: float = 0.5
    tag_removal_threshold: float = 1.0
    max_errors: int = 3
    
    # Playback settings
    manual_action_priority_window: float = 1.0
    pause_threshold: float = 3.0
