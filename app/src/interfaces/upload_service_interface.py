# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Upload service interface definition.

This module defines the abstract interface for upload services, promoting
loose coupling and enabling dependency injection with different upload
implementations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Tuple

from fastapi import UploadFile


class UploadServiceInterface(ABC):
    """Abstract interface for upload service implementations.
    
    Defines the contract that all upload services must implement,
    enabling dependency injection and testing with mock implementations.
    """

    @abstractmethod
    async def process_upload(
        self, file: UploadFile, destination_folder: str
    ) -> Tuple[str, Dict[str, str]]:
        """Process an uploaded file and extract metadata.

        Args:
            file: The uploaded file
            destination_folder: Folder to save the file

        Returns:
            Tuple of (filename, metadata_dict)

        Raises:
            InvalidFileError: If the file is invalid
            ProcessingError: If processing fails
        """
        pass

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, str]:
        """Extract metadata from an audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary containing metadata (title, artist, album, duration, etc.)
        """
        pass

    @abstractmethod
    def validate_file(self, file: UploadFile) -> bool:
        """Validate if the uploaded file is acceptable.

        Args:
            file: The uploaded file to validate

        Returns:
            True if file is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> set:
        """Get the set of supported audio file formats.

        Returns:
            Set of supported file extensions (e.g., {'.mp3', '.wav'})
        """
        pass
