# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Configuration for the unified monitoring system."""

from typing import Optional


class MonitoringConfig:
    """Centralized configuration for all monitoring components.

    Uses lazy loading to avoid circular dependencies during module initialization.
    """

    def __init__(self):
        """Initialize monitoring config with lazy loading."""
        self._app_config = None

    def _get_config(self):
        """Lazy load the app config to avoid circular dependencies."""
        if self._app_config is None:
            from app.src.config.app_config import config
            self._app_config = config
        return self._app_config

    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._get_config().debug

    @property
    def event_monitoring_enabled(self) -> bool:
        """Check if event monitoring is enabled (only in debug mode)."""
        return self._get_config().enable_event_monitoring

    @property
    def performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled."""
        return self._get_config().enable_performance_monitoring

    @property
    def file_logging_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return self._get_config().log_file is not None

    @property
    def trace_history_size(self) -> int:
        """Get maximum events to keep in trace history."""
        return self._get_config().monitoring_trace_history_size

    @property
    def monitoring_file_logging_enabled(self) -> bool:
        """Check if monitoring-specific file logging is enabled."""
        return self._get_config().monitoring_file_logging

    @property
    def log_level(self) -> str:
        """Get the configured log level."""
        return self._get_config().log_level

    @property
    def log_format(self) -> str:
        """Get the configured log format."""
        return self._get_config().log_format

    @property
    def log_file_path(self) -> Optional[str]:
        """Get the log file path."""
        return self._get_config().log_file

    def should_monitor_component(self, component_name: str) -> bool:
        """Check if a specific component should be monitored.

        Args:
            component_name: Name of the component to check

        Returns:
            True if component should be monitored, False otherwise
        """
        if not self.debug_mode:
            return False

        # Component-specific monitoring rules
        component_rules = {
            "audio_engine": self.event_monitoring_enabled,
            "playlist_manager": self.event_monitoring_enabled,
            "event_bus": self.event_monitoring_enabled,
            "performance": self.performance_monitoring_enabled,
        }

        return component_rules.get(component_name, self.event_monitoring_enabled)


# Global monitoring configuration instance
# Note: MonitoringConfig should be retrieved from DI container
# Use: container.get("monitoring_config") or get_monitoring_config()
# Legacy global instance kept for backward compatibility during transition
import warnings
warnings.warn(
    "Global 'monitoring_config' instance is deprecated. Use dependency injection instead. "
    "This global will be removed in v2.0 (Q2 2026)",
    DeprecationWarning,
    stacklevel=2
)
monitoring_config = MonitoringConfig()
