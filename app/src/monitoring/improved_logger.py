# app/src/monitoring/improved_logger.py

from typing import Optional, Dict, Any
import logging

from .logging.log_base_formatter import BaseLogFormatter
from .logging.log_colored_formatter import ColoredLogFormatter
from .logging.log_level import LogLevel

class ImprovedLogger:
    _instance = None
    _error_counts = {}
    MAX_REPEATED_ERRORS = 1

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
        self._configure_logger()

    def _configure_logger(self):
        self.logger.handlers = []
        self.logger.propagate = False
        handler = logging.StreamHandler()
        formatter = ColoredLogFormatter('%(levelname)s | %(name)s | %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

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

    def log(self, level: LogLevel, message: str, exc_info: Optional[Exception] = None, **kwargs):
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