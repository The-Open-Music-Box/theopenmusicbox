# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Helpers module initialization for TheOpenMusicBox backend.

Exposes utility classes for error handling, system dependency checking,
and exception management. Provides a centralized collection of helper
functionality used across the application.
"""

from .exceptions import AppError, ErrorCategory, ErrorContext, ErrorSeverity
from .system_dependency_checker import SystemDependencyChecker

__all__ = [
    "AppError",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorContext",
    "SystemDependencyChecker",
]
