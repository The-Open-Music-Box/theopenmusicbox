# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unified Logger for TheOpenMusicBox.

This module provides the ImprovedLogger class with conditional monitoring
based on debug mode and configuration settings.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import monitoring_config
from app.src.monitoring.logging.log_base_formatter import BaseLogFormatter
from app.src.monitoring.logging.log_colored_formatter import ColoredLogFormatter
from app.src.monitoring.logging.log_level import LogLevel


class ImprovedLogger:
    """Thread-safe, context-aware logger for TheOpenMusicBox.

    Provides colored output, error deduplication, and extra context
    formatting for hardware and application logs. Integrates with
    unified monitoring configuration.
    """

    _error_counts = {}
    MAX_REPEATED_ERRORS = 1

    # Log level mapping from string to logging level
    _LOG_LEVEL_MAP = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    def __init__(self, name: str):
        """Initialize the logger with unified configuration.

        Args:
            name: Logger name (typically module __name__)
        """
        self.logger = logging.getLogger(name)
        self.context = {}
        self.name = name
        self._configure_logger()

    def _configure_logger(self):
        """Configure logger with handlers and formatters."""
        self.logger.handlers = []
        self.logger.propagate = False

        # Configure console handler with colored formatter
        console_handler = logging.StreamHandler()
        log_format = monitoring_config.log_format

        # Use colored formatter for console output
        if monitoring_config.debug_mode:
            formatter = ColoredLogFormatter(log_format)
        else:
            formatter = logging.Formatter(log_format)

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Configure file handler with rotation if log_file is specified
        if monitoring_config.file_logging_enabled:
            log_path = Path(monitoring_config.log_file_path)

            # If path is relative, make it absolute from the app root
            if not log_path.is_absolute():
                app_dir = Path(__file__).parent.parent.parent.parent
                log_path = app_dir / log_path

            # Ensure log directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Use RotatingFileHandler with 100 MB limit and 5 backup files
            # maxBytes = 100 MB = 100 * 1024 * 1024 bytes
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=100 * 1024 * 1024,  # 100 MB
                backupCount=5,  # Keep 5 backup files (app.log.1, app.log.2, etc.)
                encoding="utf-8",
            )
            file_formatter = logging.Formatter(log_format)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Set log level from config
        log_level = monitoring_config.log_level.upper()
        self.logger.setLevel(self._LOG_LEVEL_MAP.get(log_level, logging.INFO))

    def _should_log_error(self, error_key: str) -> bool:
        """Check if error should be logged based on deduplication rules.

        Args:
            error_key: Unique key for the error

        Returns:
            True if error should be logged, False otherwise
        """
        count = self._error_counts.get(error_key, 0)
        if count < self.MAX_REPEATED_ERRORS:
            self._error_counts[error_key] = count + 1
            return True
        return False

    def _format_extra(self, extra: Dict[str, Any]) -> str:
        """Format extra context information.

        Args:
            extra: Extra context data

        Returns:
            Formatted extra string
        """
        if not extra:
            return ""
        return BaseLogFormatter().format_extra(extra)

    def log(
        self,
        level: LogLevel,
        message: str,
        exc_info: Optional[Exception] = None,
        **kwargs,
    ):
        """Log a message with the specified level.

        Formats extra context and handles errors appropriately.
        Integrates with unified monitoring for debug information.

        Args:
            level: LogLevel (severity)
            message: Log message
            exc_info: Optional exception for error context
            **kwargs: Additional context for the log formatter
        """
        # Handle hardware unavailable errors gracefully
        if exc_info and isinstance(exc_info, OSError):
            message = "Hardware not available"
            exc_info = None

        error_key = f"{level.value}:{message}"

        # Apply error deduplication for ERROR and CRITICAL levels
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            if not self._should_log_error(error_key):
                return

        # Add debug information if monitoring is enabled
        if monitoring_config.debug_mode and kwargs:
            kwargs["logger_name"] = self.name
            kwargs["monitoring_enabled"] = monitoring_config.event_monitoring_enabled

        extra_str = self._format_extra(kwargs) if kwargs else ""
        full_message = f"{message}{extra_str}"

        # Log the message
        log_func = getattr(self.logger, level.value)
        log_func(full_message)

        # Notify event monitor if available and enabled
        if monitoring_config.event_monitoring_enabled:
            from .. import get_event_monitor

            event_monitor = get_event_monitor()
            if event_monitor:
                # Create a simple log event for the monitor
                try:
                    import asyncio
                    import time
                    from app.src.audio.core.event_bus import LogEvent

                    log_event = LogEvent(
                        logger_name=self.name,
                        level=level.value,
                        message=message,
                        timestamp=time.time(),
                        source_component=self.name,
                    )

                    # Try to schedule the event if we're in an async context
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(event_monitor.handle_event(log_event))
                    except RuntimeError:
                        # Not in async context, skip event monitoring
                        pass

                except ImportError:
                    # LogEvent doesn't exist, skip event monitoring
                    pass

    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log an info message."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log an error message."""
        self.log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log a critical message."""
        self.log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)

    def set_context(self, **context):
        """Set persistent context for this logger.

        Args:
            **context: Context key-value pairs
        """
        self.context.update(context)

    def clear_context(self):
        """Clear all persistent context."""
        self.context.clear()

    def with_context(self, **context):
        """Create a temporary context for a single log message.

        Args:
            **context: Context key-value pairs

        Returns:
            LoggerContext: Context manager for temporary context
        """
        return LoggerContext(self, context)


class LoggerContext:
    """Context manager for temporary logger context."""

    def __init__(self, logger: ImprovedLogger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
        self.original_context = {}

    def __enter__(self):
        # Save original context and update with new context
        for key, value in self.context.items():
            if key in self.logger.context:
                self.original_context[key] = self.logger.context[key]
            self.logger.context[key] = value
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original context
        for key in self.context.keys():
            if key in self.original_context:
                self.logger.context[key] = self.original_context[key]
            else:
                self.logger.context.pop(key, None)
