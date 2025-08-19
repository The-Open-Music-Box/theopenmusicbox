# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Controls System Module.

This module provides access to physical controls (buttons and rotary
encoders) for interacting with the audio playback system.

It provides a singleton pattern access to the ControlesManager, which
manages all physical control devices.
"""

from typing import Optional

from .controles_manager import ControlesManager

# Singleton instance of the controls manager
_controles_manager_instance: Optional[ControlesManager] = None


def get_controles_manager() -> ControlesManager:
    """Get the singleton instance of the controls manager.

    Returns:
        The controls manager instance
    """
    global _controles_manager_instance

    if _controles_manager_instance is None:
        _controles_manager_instance = ControlesManager()

    return _controles_manager_instance
