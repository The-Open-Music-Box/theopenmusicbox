# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..config.app_config import config
from .logging.log_base_formatter import BaseLogFormatter
from .logging.log_colored_formatter import ColoredLogFormatter
from .logging.log_level import LogLevel


class ImprovedLogger:
    """Thread-safe, context-aware logger for TheOpenMusicBox.

    Provides colored output, error deduplication, and extra context
    formatting for hardware and application logs.
    """

    _instance = None
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
        self.logger = logging.getLogger(name)
        self.context = {}
        self._configure_logger()

    def _configure_logger(self):
        self.logger.handlers = []
        self.logger.propagate = False

        # Configure console handler with colored formatter
        console_handler = logging.StreamHandler()
        log_format = config.log_format
        formatter = ColoredLogFormatter(log_format)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Configure file handler if log_file is specified
        if config.log_file:
            log_path = Path(config.log_file)
            # If path is relative, make it absolute from the app root
            if not log_path.is_absolute():
                app_dir = Path(__file__).parent.parent.parent
                log_path = app_dir / log_path

            # Ensure log directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            # BaseLogFormatter doesn't accept format parameters
            file_formatter = BaseLogFormatter()
            file_handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(file_handler)

        # Set log level from config
        log_level = config.log_level.upper()
        self.logger.setLevel(self._LOG_LEVEL_MAP.get(log_level, logging.INFO))

    def _should_log_error(self, error_key: str) -> bool:
        count = self._error_counts.get(error_key, 0)
        if count < self.MAX_REPEATED_ERRORS:
            self._error_counts[error_key] = count + 1
            return True
        return False

    def _format_extra(self, extra: Dict[str, Any]) -> str:
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
        """Log a message with the specified level, formatting extra context and
        handling errors.

        Args:
            level: LogLevel (severity)
            message: Log message
            exc_info: Optional exception for error context
            **kwargs: Additional context for the log formatter
        """
        if exc_info and isinstance(exc_info, OSError):
            message = "Hardware not available"
            exc_info = None

        error_key = f"{level.value}:{message}"

        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            if not self._should_log_error(error_key):
                return

        extra_str = self._format_extra(kwargs) if kwargs else ""
        full_message = f"{message}{extra_str}"

        log_func = getattr(self.logger, level.value)
        log_func(full_message)
