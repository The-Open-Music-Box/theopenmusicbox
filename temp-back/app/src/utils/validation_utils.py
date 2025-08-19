# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Validation utilities for common input validation patterns.

This module centralizes validation logic to eliminate code duplication
and ensure consistent validation across the application.
"""

from typing import List, Union, Any
from app.src.services.exceptions.track_management_exceptions import TrackValidationError


class ValidationUtils:
    """Utility class for common validation patterns."""
    
    @staticmethod
    def validate_playlist_id(playlist_id: Any, allow_none: bool = False) -> str:
        """
        Validate playlist ID parameter.
        
        Args:
            playlist_id: The playlist ID to validate
            allow_none: Whether to allow None values
            
        Returns:
            Validated playlist ID as string
            
        Raises:
            TrackValidationError: If playlist_id is invalid
        """
        if allow_none and playlist_id is None:
            return None
            
        if not playlist_id or not isinstance(playlist_id, str):
            raise TrackValidationError("playlist_id must be a non-empty string")
        
        if not playlist_id.strip():
            raise TrackValidationError("playlist_id cannot be empty or whitespace only")
            
        return playlist_id.strip()
    
    @staticmethod
    def validate_track_number(track_number: Any) -> int:
        """
        Validate track number parameter.
        
        Args:
            track_number: The track number to validate
            
        Returns:
            Validated track number as integer
            
        Raises:
            TrackValidationError: If track_number is invalid
        """
        if not isinstance(track_number, int) or track_number <= 0:
            raise TrackValidationError("track_number must be a positive integer")
            
        return track_number
    
    @staticmethod
    def validate_track_numbers(track_numbers: Any) -> List[int]:
        """
        Validate list of track numbers.
        
        Args:
            track_numbers: List of track numbers to validate
            
        Returns:
            Validated and deduplicated list of track numbers
            
        Raises:
            TrackValidationError: If track_numbers is invalid
        """
        if not track_numbers or not isinstance(track_numbers, list):
            raise TrackValidationError("track_numbers must be a non-empty list")
        
        if not all(isinstance(num, int) and num > 0 for num in track_numbers):
            raise TrackValidationError("All track numbers must be positive integers")
        
        # Remove duplicates while preserving order
        seen = set()
        validated_numbers = []
        for num in track_numbers:
            if num not in seen:
                seen.add(num)
                validated_numbers.append(num)
                
        return validated_numbers
    
    @staticmethod
    def validate_track_order(track_order: Any) -> List[int]:
        """
        Validate track order list.
        
        Args:
            track_order: List representing desired track order
            
        Returns:
            Validated track order list
            
        Raises:
            TrackValidationError: If track_order is invalid
        """
        if not track_order or not isinstance(track_order, list):
            raise TrackValidationError("track_order must be a non-empty list")
        
        if not all(isinstance(num, int) and num > 0 for num in track_order):
            raise TrackValidationError("All track numbers in order must be positive integers")
        
        # Check for duplicates
        if len(track_order) != len(set(track_order)):
            raise TrackValidationError("track_order cannot contain duplicate track numbers")
            
        return track_order
    
    @staticmethod
    def validate_string_parameter(param_value: Any, param_name: str, 
                                allow_empty: bool = False, max_length: int = None) -> str:
        """
        Validate string parameter with common checks.
        
        Args:
            param_value: The parameter value to validate
            param_name: Name of the parameter for error messages
            allow_empty: Whether to allow empty strings
            max_length: Maximum allowed length
            
        Returns:
            Validated string parameter
            
        Raises:
            TrackValidationError: If parameter is invalid
        """
        if not isinstance(param_value, str):
            raise TrackValidationError(f"{param_name} must be a string")
        
        if not allow_empty and not param_value.strip():
            raise TrackValidationError(f"{param_name} cannot be empty")
        
        if max_length and len(param_value) > max_length:
            raise TrackValidationError(f"{param_name} cannot exceed {max_length} characters")
            
        return param_value.strip() if not allow_empty else param_value
    
    @staticmethod
    def validate_positive_integer(value: Any, param_name: str, 
                                min_value: int = 1, max_value: int = None) -> int:
        """
        Validate positive integer parameter.
        
        Args:
            value: The value to validate
            param_name: Name of the parameter for error messages
            min_value: Minimum allowed value (default: 1)
            max_value: Maximum allowed value (optional)
            
        Returns:
            Validated integer value
            
        Raises:
            TrackValidationError: If value is invalid
        """
        if not isinstance(value, int):
            raise TrackValidationError(f"{param_name} must be an integer")
        
        if value < min_value:
            raise TrackValidationError(f"{param_name} must be at least {min_value}")
        
        if max_value and value > max_value:
            raise TrackValidationError(f"{param_name} cannot exceed {max_value}")
            
        return value
    
    @staticmethod
    def validate_file_size(file_size: Any, max_size_mb: int = 100) -> int:
        """
        Validate file size parameter.
        
        Args:
            file_size: File size in bytes
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            Validated file size
            
        Raises:
            TrackValidationError: If file size is invalid
        """
        if not isinstance(file_size, int) or file_size <= 0:
            raise TrackValidationError("file_size must be a positive integer")
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise TrackValidationError(f"file_size cannot exceed {max_size_mb}MB")
            
        return file_size
    
    @staticmethod
    def validate_filename(filename: Any) -> str:
        """
        Validate filename parameter.
        
        Args:
            filename: The filename to validate
            
        Returns:
            Validated filename
            
        Raises:
            TrackValidationError: If filename is invalid
        """
        if not isinstance(filename, str) or not filename.strip():
            raise TrackValidationError("filename must be a non-empty string")
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in filename for char in invalid_chars):
            raise TrackValidationError(f"filename contains invalid characters: {invalid_chars}")
        
        # Check length
        if len(filename) > 255:
            raise TrackValidationError("filename cannot exceed 255 characters")
            
        return filename.strip()
