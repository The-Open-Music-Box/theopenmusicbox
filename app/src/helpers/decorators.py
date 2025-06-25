# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Utility decorators for the application.

This module provides various decorators that can be used throughout the
application to add common functionality to methods and functions.
"""

import functools
import warnings
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(func: F) -> F:
    """Decorator to mark functions as deprecated. It will result in a warning
    being emitted when the function is used.

    Args:
        func: The function to mark as deprecated

    Returns:
        Wrapped function that emits a warning when called
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"Call to deprecated function {func.__name__}. "
            f"This function will be removed in a future version.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper
