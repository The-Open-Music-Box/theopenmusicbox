# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

# back/app/src/helpers/__init__.py

from .exceptions import AppError, ErrorCategory, ErrorContext, ErrorSeverity
from .system_dependency_checker import SystemDependencyChecker

__all__ = [
    "AppError",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorContext",
    "SystemDependencyChecker",
]
