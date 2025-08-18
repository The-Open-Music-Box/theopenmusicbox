# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Common error handling utilities for consistent error management.

This module provides standardized error handling patterns, response formatting,
and exception utilities to ensure consistent error handling across the application.
"""

from typing import Any, Dict, Optional, Union

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from socketio import AsyncServer

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class ErrorHandler:
    """Centralized error handling utilities.
    
    Provides consistent error response formatting, logging, and Socket.IO
    error emission patterns across the application.
    """

    @staticmethod
    def create_error_response(
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        log_level: LogLevel = LogLevel.ERROR
    ) -> JSONResponse:
        """Create a standardized error response.
        
        Args:
            status_code: HTTP status code
            message: Error message
            details: Optional additional error details
            log_level: Log level for the error
            
        Returns:
            JSONResponse with standardized error format
        """
        error_data = {
            "status": "error",
            "message": message,
            "error_code": status_code
        }
        
        if details:
            error_data["details"] = details
            
        logger.log(log_level, f"Error response {status_code}: {message}")
        
        return JSONResponse(content=error_data, status_code=status_code)

    @staticmethod
    def create_http_exception(
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """Create a standardized HTTP exception.
        
        Args:
            status_code: HTTP status code
            message: Error message
            details: Optional additional error details
            
        Returns:
            HTTPException with standardized format
        """
        detail = {"message": message}
        if details:
            detail["details"] = details
            
        return HTTPException(status_code=status_code, detail=detail)

    @staticmethod
    async def emit_socket_error(
        socketio: AsyncServer,
        event_name: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        room: Optional[str] = None
    ) -> None:
        """Emit a standardized error event via Socket.IO.
        
        Args:
            socketio: Socket.IO server instance
            event_name: Name of the error event to emit
            error_message: Error message
            context: Optional context information
            room: Optional room to emit to
        """
        try:
            error_data = {
                "status": "error",
                "message": error_message,
                "timestamp": logger._get_timestamp()
            }
            
            if context:
                error_data.update(context)
                
            await socketio.emit(event_name, error_data, room=room)
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Failed to emit socket error {event_name}: {str(e)}"
            )

    @staticmethod
    def log_and_raise_http_exception(
        status_code: int,
        message: str,
        original_exception: Optional[Exception] = None,
        log_level: LogLevel = LogLevel.ERROR
    ) -> None:
        """Log an error and raise an HTTP exception.
        
        Args:
            status_code: HTTP status code
            message: Error message
            original_exception: Original exception that caused the error
            log_level: Log level for the error
            
        Raises:
            HTTPException with the specified status code and message
        """
        if original_exception:
            logger.log(
                log_level,
                f"{message}: {str(original_exception)}"
            )
        else:
            logger.log(log_level, message)
            
        raise HTTPException(status_code=status_code, detail=message)

    @staticmethod
    def handle_service_error(
        operation: str,
        exception: Exception,
        default_status_code: int = 500
    ) -> JSONResponse:
        """Handle service layer errors with appropriate HTTP responses.
        
        Args:
            operation: Description of the operation that failed
            exception: The exception that occurred
            default_status_code: Default HTTP status code if not determinable
            
        Returns:
            JSONResponse with appropriate error information
        """
        from app.src.helpers.exceptions import InvalidFileError, ProcessingError
        
        if isinstance(exception, InvalidFileError):
            return ErrorHandler.create_error_response(
                400, f"{operation} failed: {str(exception)}"
            )
        elif isinstance(exception, ProcessingError):
            return ErrorHandler.create_error_response(
                500, f"{operation} failed: {str(exception)}"
            )
        elif isinstance(exception, ValueError):
            return ErrorHandler.create_error_response(
                400, f"{operation} failed: Invalid input - {str(exception)}"
            )
        elif isinstance(exception, FileNotFoundError):
            return ErrorHandler.create_error_response(
                404, f"{operation} failed: Resource not found - {str(exception)}"
            )
        elif isinstance(exception, PermissionError):
            return ErrorHandler.create_error_response(
                403, f"{operation} failed: Permission denied - {str(exception)}"
            )
        else:
            return ErrorHandler.create_error_response(
                default_status_code,
                f"{operation} failed: {str(exception)}"
            )

    @staticmethod
    def create_success_response(
        message: str,
        data: Optional[Dict[str, Any]] = None,
        status_code: int = 200
    ) -> JSONResponse:
        """Create a standardized success response.
        
        Args:
            message: Success message
            data: Optional response data
            status_code: HTTP status code (default 200)
            
        Returns:
            JSONResponse with standardized success format
        """
        response_data = {
            "status": "success",
            "message": message
        }
        
        if data:
            response_data.update(data)
            
        return JSONResponse(content=response_data, status_code=status_code)

    @staticmethod
    async def emit_socket_success(
        socketio: AsyncServer,
        event_name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        room: Optional[str] = None
    ) -> None:
        """Emit a standardized success event via Socket.IO.
        
        Args:
            socketio: Socket.IO server instance
            event_name: Name of the success event to emit
            message: Success message
            data: Optional response data
            room: Optional room to emit to
        """
        try:
            response_data = {
                "status": "success",
                "message": message,
                "timestamp": logger._get_timestamp()
            }
            
            if data:
                response_data.update(data)
                
            await socketio.emit(event_name, response_data, room=room)
            
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Failed to emit socket success {event_name}: {str(e)}"
            )
