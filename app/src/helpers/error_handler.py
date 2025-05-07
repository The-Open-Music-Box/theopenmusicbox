"""
Standardized error handling utility for consistent error management.

This module provides a centralized approach to error handling across the application,
ensuring consistent logging, error creation, and error handling patterns.
"""
import traceback
from typing import Optional, Dict, Any, Callable, TypeVar, Union

from app.src.helpers.exceptions import AppError, ErrorSeverity
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

T = TypeVar('T')  # Generic type for return values

class ErrorHandler:
    """
    Standardized error handling utility for consistent error management.
    """
    
    @staticmethod
    def log_error(error: Exception, 
                 context: str, 
                 level: LogLevel = LogLevel.ERROR,
                 include_traceback: bool = True) -> None:
        """
        Log an error with standardized formatting.
        
        Args:
            error: The exception that occurred
            context: Description of where/when the error occurred
            level: Log level to use
            include_traceback: Whether to include the full traceback
        """
        error_msg = f"{context}: {str(error)}"
        if include_traceback:
            logger.log(level, error_msg, exc_info=error)
        else:
            logger.log(level, error_msg)
    
    @staticmethod
    def create_app_error(error: Exception,
                        message: str,
                        component: str,
                        operation: str,
                        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                        details: Optional[Dict[str, Any]] = None) -> AppError:
        """
        Create a standardized AppError from an exception.
        
        Args:
            error: The original exception
            message: Human-readable error message
            component: System component where the error occurred
            operation: Operation that was being performed
            severity: Error severity level
            details: Additional error details
            
        Returns:
            A properly formatted AppError
        """
        error_details = details or {}
        error_details["original_error"] = str(error)
        error_details["traceback"] = traceback.format_exc()
        
        return AppError.hardware_error(
            message=message,
            component=component,
            operation=operation,
            details=error_details,
            severity=severity
        )
    
    @staticmethod
    def handle_with_fallback(func: Callable[[], T], 
                            fallback_value: T,
                            error_message: str,
                            component: str,
                            operation: str,
                            log_level: LogLevel = LogLevel.ERROR,
                            raise_error: bool = False,
                            expected_exceptions: tuple = (Exception,)) -> T:
        """
        Execute a function with standardized error handling and fallback.
        
        Args:
            func: Function to execute
            fallback_value: Value to return if the function fails
            error_message: Message to log if an error occurs
            component: System component for error reporting
            operation: Operation being performed
            log_level: Log level for errors
            raise_error: Whether to raise the error after logging
            expected_exceptions: Tuple of exception types to catch
            
        Returns:
            The function result or fallback value
            
        Raises:
            AppError: If raise_error is True and an exception occurs
            Exception: Any exception not in expected_exceptions
        """
        try:
            return func()
        except expected_exceptions as e:
            ErrorHandler.log_error(e, error_message, log_level)
            
            if raise_error:
                raise ErrorHandler.create_app_error(
                    error=e,
                    message=error_message,
                    component=component,
                    operation=operation,
                    details={"function": func.__name__}
                )
            
            return fallback_value
