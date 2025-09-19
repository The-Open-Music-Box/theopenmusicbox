# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Configuration for the unified monitoring system."""

from typing import Optional
from app.src.config.app_config import config


class MonitoringConfig:
    """Centralized configuration for all monitoring components."""

    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return config.debug

    @property
    def event_monitoring_enabled(self) -> bool:
        """Check if event monitoring is enabled (only in debug mode)."""
        return config.enable_event_monitoring

    @property
    def performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled."""
        return config.enable_performance_monitoring

    @property
    def file_logging_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return config.log_file is not None

    @property
    def trace_history_size(self) -> int:
        """Get maximum events to keep in trace history."""
        return config.monitoring_trace_history_size

    @property
    def monitoring_file_logging_enabled(self) -> bool:
        """Check if monitoring-specific file logging is enabled."""
        return config.monitoring_file_logging

    @property
    def log_level(self) -> str:
        """Get the configured log level."""
        return config.log_level

    @property
    def log_format(self) -> str:
        """Get the configured log format."""
        return config.log_format

    @property
    def log_file_path(self) -> Optional[str]:
        """Get the log file path."""
        return config.log_file

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
monitoring_config = MonitoringConfig()
