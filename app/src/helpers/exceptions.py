# app/src/helpers/exceptions.py

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FATAL = "fatal"

class ErrorCategory(Enum):
    """Main error categories"""
    HARDWARE = "hardware"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"

@dataclass
class ErrorContext:
    """Enriched context for exceptions"""
    category: ErrorCategory
    component: str
    operation: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[int] = None

class AppError(Exception):
    """Unified base exception for the application"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        component: str,
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[int] = None,
    ):
        self.context = ErrorContext(
            category=category,
            component=component,
            operation=operation,
            details=details,
            error_code=error_code
        )
        self.severity = severity
        self.message = message
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        base = f"[{self.severity.value.upper()}] [{self.context.category.value}] {self.message}"
        details = f" ({self.context.component}:{self.context.operation})"
        if self.context.details:
            details += f" - {self.context.details}"
        return base + details

    @classmethod
    def hardware_error(cls, message: str, component: str, operation: str, **kwargs):
        return cls(
            message=message,
            category=ErrorCategory.HARDWARE,
            component=component,
            operation=operation,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )

    @classmethod
    def configuration_error(cls, message: str, config_key: str, **kwargs):
        return cls(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            component="configuration",
            operation=f"validate_{config_key}",
            severity=ErrorSeverity.FATAL,
            **kwargs
        )

    @classmethod
    def timeout_error(cls, component: str, operation: str, timeout_value: float, **kwargs):
        return cls(
            message=f"Operation timed out after {timeout_value}s",
            category=ErrorCategory.TIMEOUT,
            component=component,
            operation=operation,
            details={"timeout_value": timeout_value},
            **kwargs
        )

class InvalidFileError(Exception):
    """Exception raised when a file is invalid"""
    pass

class ProcessingError(Exception):
    """Exception raised during file processing"""
    pass
