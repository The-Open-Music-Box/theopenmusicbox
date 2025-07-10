# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.src.helpers.exceptions import InvalidFileError, ProcessingError
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.upload_service import UploadService

logger = ImprovedLogger(__name__)


class ChunkedUploadService:
    """Service for handling chunked file uploads, managing temporary storage
    and assembly.

    This class provides methods to manage chunked file uploads,
    including creating sessions, processing individual chunks, and
    finalizing uploads by assembling chunks.
    """

    def __init__(self, config, upload_service: Optional[UploadService] = None):
        """Initialize the ChunkedUploadService with application config.

        Args:
            config: Application configuration object
            upload_service: Optional UploadService instance for metadata extraction
        """
        self.temp_folder = Path(config.upload_folder) / "temp"
        self.temp_folder.mkdir(parents=True, exist_ok=True)
        self.upload_service = upload_service or UploadService(config)
        self.max_file_size = config.upload_max_size
        self.allowed_extensions = set(config.upload_allowed_extensions)
        self.active_uploads = (
            {}
        )  # Dictionary to track active uploads: {session_id: {filename, chunks, total_size, etc}}

    def _allowed_file(self, filename: str) -> bool:
        """Return True if the filename is an allowed audio type."""
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in self.allowed_extensions
        )

    def _check_file_size(self, current_size: int, chunk_size: int) -> bool:
        """Return True if the file size is within the allowed maximum."""
        return (current_size + chunk_size) <= self.max_file_size

    def create_session(self, filename: str, total_chunks: int, total_size: int) -> str:
        """Create a new upload session for a file.

        Args:
            filename: Original filename
            total_chunks: Total number of chunks expected
            total_size: Total file size expected

        Returns:
            session_id: Unique identifier for the upload session

        Raises:
            InvalidFileError: If the file type is not allowed or size exceeds limit
        """
        if not self._allowed_file(filename):
            raise InvalidFileError(
                f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )

        if total_size > self.max_file_size:
            raise InvalidFileError(
                f"File too large. Maximum size: {self.max_file_size/1024/1024}MB"
            )

        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Create a directory for this upload session
        session_dir = self.temp_folder / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Track the upload in memory
        self.active_uploads[session_id] = {
            "filename": filename,
            "total_chunks": total_chunks,
            "total_size": total_size,
            "received_chunks": set(),
            "current_size": 0,
            "session_dir": session_dir,
            "complete": False,
        }

        logger.log(
            LogLevel.INFO, f"Created upload session {session_id} for file {filename}"
        )
        return session_id

    async def process_chunk(
        self, session_id: str, chunk_index: int, chunk_data, chunk_size: int
    ) -> Dict:
        """Process a chunk of an upload session.

        Args:
            session_id: Upload session identifier
            chunk_index: Index of the current chunk (0-based)
            chunk_data: Binary data of the chunk
            chunk_size: Size of the chunk in bytes

        Returns:
            Dictionary with status information

        Raises:
            InvalidFileError: If the session doesn't exist or chunk is invalid
            ProcessingError: If there is an error during processing
        """
        # Check if session exists
        if session_id not in self.active_uploads:
            raise InvalidFileError(f"Upload session {session_id} not found")

        session = self.active_uploads[session_id]

        # Check if this chunk was already received
        if chunk_index in session["received_chunks"]:
            return {
                "status": "duplicate",
                "message": f"Chunk {chunk_index} already received",
                "progress": len(session["received_chunks"])
                / session["total_chunks"]
                * 100,
            }

        # Check if adding this chunk would exceed max file size
        if not self._check_file_size(session["current_size"], chunk_size):
            raise InvalidFileError(
                f"File too large. Maximum size: {self.max_file_size/1024/1024}MB"
            )

        try:
            # Save the chunk to the session directory
            chunk_path = session["session_dir"] / f"chunk_{chunk_index}"
            with open(chunk_path, "wb") as f:
                f.write(chunk_data)

            # Update session tracking
            session["received_chunks"].add(chunk_index)
            session["current_size"] += chunk_size

            # Calculate progress
            progress = len(session["received_chunks"]) / session["total_chunks"] * 100

            # Check if upload is complete
            is_complete = len(session["received_chunks"]) == session["total_chunks"]
            session["complete"] = is_complete

            return {
                "status": "success",
                "message": "Chunk received",
                "chunk_index": chunk_index,
                "progress": progress,
                "complete": is_complete,
            }

        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error processing chunk {chunk_index} for session {session_id}: {str(e)}",
            )
            raise ProcessingError(f"Error processing chunk: {str(e)}")

    async def finalize_upload(
        self, session_id: str, playlist_path: str
    ) -> Tuple[str, Dict]:
        """Finalize an upload by assembling all chunks and processing the
        complete file.

        This method combines all uploaded chunks into a single file and extracts metadata.

        Args:
            session_id: Upload session identifier
            playlist_path: Destination playlist folder path

        Returns:
            Tuple of (filename, metadata dictionary)

        Raises:
            InvalidFileError: If the session doesn't exist or is incomplete
            ProcessingError: If there is an error during processing
        """
        # Check if session exists
        if session_id not in self.active_uploads:
            raise InvalidFileError(f"Upload session {session_id} not found")

        session = self.active_uploads[session_id]

        # Check if all chunks have been received
        if not session["complete"]:
            missing = set(range(session["total_chunks"])) - session["received_chunks"]
            raise InvalidFileError(f"Upload incomplete. Missing chunks: {missing}")

        try:
            # Create the destination directory
            upload_path = Path(self.upload_service.upload_folder) / playlist_path
            upload_path.mkdir(parents=True, exist_ok=True)

            # Assemble the file from chunks
            filename = session["filename"]
            assembled_file_path = upload_path / filename

            with open(assembled_file_path, "wb") as output_file:
                # Write chunks in order
                for i in range(session["total_chunks"]):
                    chunk_path = session["session_dir"] / f"chunk_{i}"
                    with open(chunk_path, "rb") as chunk_file:
                        output_file.write(chunk_file.read())

            # Extract metadata
            metadata = self.upload_service.extract_metadata(assembled_file_path)

            # Clean up the temporary files
            self._cleanup_session(session_id)

            logger.log(
                LogLevel.INFO,
                f"Successfully assembled file {filename} from {session['total_chunks']} chunks",
            )
            return filename, metadata

        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error finalizing upload for session {session_id}: {str(e)}",
            )
            self._cleanup_session(session_id)
            raise ProcessingError(f"Error finalizing upload: {str(e)}")

    def get_session_status(self, session_id: str) -> Dict:
        """Get the status of an upload session.

        Args:
            session_id: Upload session identifier

        Returns:
            Dictionary with session status information

        Raises:
            InvalidFileError: If the session doesn't exist
        """
        if session_id not in self.active_uploads:
            raise InvalidFileError(f"Upload session {session_id} not found")

        session = self.active_uploads[session_id]
        return {
            "filename": session["filename"],
            "total_chunks": session["total_chunks"],
            "received_chunks": len(session["received_chunks"]),
            "current_size": session["current_size"],
            "total_size": session["total_size"],
            "progress": len(session["received_chunks"]) / session["total_chunks"] * 100,
            "complete": session["complete"],
        }

    def _cleanup_session(self, session_id: str):
        """Clean up temporary files for a session.

        Args:
            session_id: Upload session identifier
        """
        if session_id in self.active_uploads:
            try:
                session_dir = self.active_uploads[session_id]["session_dir"]
                if session_dir.exists():
                    shutil.rmtree(session_dir)
                del self.active_uploads[session_id]
                logger.log(LogLevel.INFO, f"Cleaned up session {session_id}")
            except Exception as e:
                logger.log(
                    LogLevel.ERROR, f"Error cleaning up session {session_id}: {str(e)}"
                )

    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired upload sessions.

        Args:
            max_age_hours: Maximum age in hours for inactive sessions
        """
        # Implementation would check directory creation times
        # and remove sessions older than max_age_hours
        pass
