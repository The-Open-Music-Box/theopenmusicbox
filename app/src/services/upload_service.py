# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

import os
from pathlib import Path
from typing import Dict, Tuple

from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from werkzeug.utils import secure_filename

from app.src.helpers.exceptions import InvalidFileError, ProcessingError
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

ALLOWED_EXTENSIONS = {"mp3", "wav", "flac", "ogg", "m4a"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class UploadService:
    """Service for handling audio file uploads and metadata extraction."""

    def __init__(self, upload_folder: str):
        """Initialize the UploadService with the given upload folder."""
        self.upload_folder = Path(upload_folder)

    def _allowed_file(self, filename: str) -> bool:
        """Return True if the filename is an allowed audio type."""
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    def _check_file_size(self, file) -> bool:
        """Return True if the file size is within the allowed maximum."""
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        return size <= MAX_FILE_SIZE

    def extract_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from an audio file.

        Args:
            file_path: Path to the audio file.

        Returns:
            Dictionary with metadata fields: title, artist, album, duration.
        """
        try:
            audio = MutagenFile(str(file_path), easy=True)
            if audio is None:
                audio = EasyID3(str(file_path))

            metadata = {
                "title": audio.get("title", [Path(file_path).stem])[0],
                "artist": audio.get("artist", ["Unknown"])[0],
                "album": audio.get("album", ["Unknown"])[0],
                "duration": audio.info.length if hasattr(audio.info, "length") else 0,
            }
            return metadata

        except Exception as e:
            logger.log(
                LogLevel.WARNING,
                f"Could not extract metadata from {file_path}: {str(e)}",
            )
            return {
                "title": Path(file_path).stem,
                "artist": "Unknown",
                "album": "Unknown",
                "duration": 0,
            }

    def process_upload(self, file, playlist_path: str) -> Tuple[str, Dict]:
        """Process an uploaded file and extract its metadata.

        Args:
            file: File-like object to upload.
            playlist_path: Destination playlist folder.

        Returns:
            Tuple of (filename, metadata dictionary).

        
        Raises:
            InvalidFileError: If the file is invalid or not allowed.
            ProcessingError: If there is an error during processing.
        """
        if not file or not file.filename:
            raise InvalidFileError("No file provided")

        if not self._allowed_file(file.filename):
            raise InvalidFileError(
                f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        if not self._check_file_size(file):
            raise InvalidFileError(
                f"File too large. Maximum size: {MAX_FILE_SIZE/1024/1024}MB"
            )

        # Secure the filename
        filename = secure_filename(file.filename)

        # Create the playlist folder if necessary
        upload_path = self.upload_folder / playlist_path
        upload_path.mkdir(parents=True, exist_ok=True)

        # Save the file
        file_path = upload_path / filename
        try:
            file.save(str(file_path))

            # Extraire les métadonnées
            metadata = self.extract_metadata(file_path)

            return filename, metadata

        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise ProcessingError(f"Error processing file: {str(e)}")

    def cleanup_failed_upload(self, playlist_path: str, filename: str):
        """Clean up files in case of failure.

        Args:
            playlist_path: Path to the playlist folder.
            filename: Name of the file to remove.
        """
        try:
            file_path = self.upload_folder / playlist_path / filename
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error cleaning up failed upload: {str(e)}")
