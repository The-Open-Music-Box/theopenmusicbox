# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unified Monitoring System for TheOpenMusicBox.

This module provides centralized monitoring, logging, and error handling
with conditional activation based on debug mode and configuration.
"""

from typing import Optional
from .config import monitoring_config
from .core.logger import ImprovedLogger

# from .core.error_handler import UnifiedErrorHandler  # Removed - using domain error handler
from .specialized.event_monitor import EventMonitor

# Global instances
_event_monitor_instance: Optional[EventMonitor] = None
_error_handler_instance = None  # Using domain error handler instead


def get_logger(name: str) -> ImprovedLogger:
    """Get a logger instance for the specified module.

    Args:
        name: Module name (typically __name__)

    Returns:
        ImprovedLogger instance
    """
    return ImprovedLogger(name)


def get_error_handler():
    """Get the unified error handler instance.

    Returns:
        Domain error handler instance
    """
    from app.src.domain.error_handling import unified_error_handler

    return unified_error_handler


def get_event_monitor() -> Optional[EventMonitor]:
    """Get event monitor instance (only if debug enabled).

    Returns:
        EventMonitor instance if debug mode is enabled, None otherwise
    """
    global _event_monitor_instance

    if not monitoring_config.event_monitoring_enabled:
        return None

    if _event_monitor_instance is None:
        _event_monitor_instance = EventMonitor(
            max_trace_history=monitoring_config.trace_history_size,
            enable_file_logging=monitoring_config.file_logging_enabled,
        )

    return _event_monitor_instance


def shutdown_monitoring():
    """Shutdown all monitoring components."""
    global _event_monitor_instance, _error_handler_instance

    if _event_monitor_instance:
        _event_monitor_instance.shutdown()
        _event_monitor_instance = None

    # Error handler is now managed by domain bootstrap
    pass


def get_monitoring_statistics() -> dict:
    """Get comprehensive monitoring statistics.

    Returns:
        Dictionary with monitoring statistics
    """
    stats = {
        "debug_mode": monitoring_config.debug_mode,
        "event_monitoring_enabled": monitoring_config.event_monitoring_enabled,
        "performance_monitoring_enabled": monitoring_config.performance_monitoring_enabled,
        "file_logging_enabled": monitoring_config.file_logging_enabled,
        "event_monitor_active": _event_monitor_instance is not None,
        "error_handler_active": True,  # Domain error handler is always active
    }

    if _event_monitor_instance:
        stats["event_monitor_stats"] = _event_monitor_instance.get_monitoring_statistics()

    return stats


# Export public interface
__all__ = [
    "get_logger",
    "get_error_handler",
    "get_event_monitor",
    "shutdown_monitoring",
    "get_monitoring_statistics",
    "monitoring_config",
]
