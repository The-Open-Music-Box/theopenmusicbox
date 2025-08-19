# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Logger module that provides a compatibility layer.

Provides compatibility between the old logger interface and the new 
ImprovedLogger implementation.
"""

from ..monitoring.improved_logger import ImprovedLogger
from ..monitoring.logging.log_level import LogLevel

# Create a default logger instance
logger = ImprovedLogger(__name__)

# Export LogLevel for backward compatibility
# This allows imports like: from app.src.utils.logger import LogLevel, logger