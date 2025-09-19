# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for Upload Application Service layer following DDD principles.

Tests cover:
- UploadApplicationService use case orchestration
- File storage integration
- Metadata extraction integration
- Error handling and resilience
- Session lifecycle management
- Validation integration
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from app.src.application.services.upload_application_service import UploadApplicationService
from app.src.domain.upload.entities.upload_session import UploadSession, UploadStatus
from app.src.domain.upload.entities.audio_file import AudioFile
from app.src.domain.upload.value_objects.file_chunk import FileChunk
from app.src.domain.upload.value_objects.file_metadata import FileMetadata
from app.src.domain.upload.services.upload_validation_service import UploadValidationService
from app.src.domain.upload.protocols.file_storage_protocol import FileStorageProtocol, MetadataExtractionProtocol


class MockFileStorage:
    """Mock file storage for testing."""
    
    def __init__(self):
        self.sessions = {}
        self.chunks = {}
        self.should_fail = False
        self.assembled_files = {}
    
    async def create_session_directory(self, session_id: str):
        if self.should_fail:
            raise Exception("Storage failure")
        self.sessions[session_id] = {"chunks": {}}
    
    async def store_chunk(self, session_id: str, chunk: FileChunk):
        if self.should_fail:
            raise Exception("Chunk storage failure")
        if session_id not in self.sessions:
            self.sessions[session_id] = {"chunks": {}}
        self.sessions[session_id]["chunks"][chunk.index] = chunk.data
    
    async def assemble_file(self, session: UploadSession, output_path: Path) -> Path:
        if self.should_fail:
            raise Exception("File assembly failure")
        
        # Simulate assembling chunks
        chunks = self.sessions.get(session.session_id, {}).get("chunks", {})
        assembled_data = b""
        for i in range(session.total_chunks):
            if i in chunks:
                assembled_data += chunks[i]
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write assembled file
        output_path.write_bytes(assembled_data)
        self.assembled_files[str(output_path)] = assembled_data
        
        return output_path
    
    async def verify_file_integrity(self, file_path: Path, expected_size: int) -> bool:
        if self.should_fail:
            return False
        
        if not file_path.exists():
            return False
        
        actual_size = file_path.stat().st_size
        return actual_size == expected_size
    
    async def cleanup_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_supported_formats(self) -> list:
        return ["mp3", "wav", "flac"]


class MockMetadataExtractor:
    """Mock metadata extractor for testing."""
    
    def __init__(self):
        self.should_fail = False
        self.extracted_metadata = {}
    
    async def extract_metadata(self, file_path: Path) -> FileMetadata:
        if self.should_fail:
            raise Exception("Metadata extraction failure")
        
        # Return mock metadata
        return FileMetadata(
            filename=file_path.name,
            size_bytes=file_path.stat().st_size if file_path.exists() else 1024,
            mime_type="audio/mpeg",
            title="Extracted Song",
            artist="Extracted Artist",
            duration_seconds=180.0,
            bitrate=320
        )
    
    def get_supported_formats(self) -> list:
        return ["mp3", "wav", "flac", "ogg"]


class TestUploadApplicationService:
    """Test UploadApplicationService use case orchestration."""
    
    @pytest.fixture
    def mock_storage(self):
        """Mock file storage fixture."""
        return MockFileStorage()
    
    @pytest.fixture
    def mock_metadata_extractor(self):
        """Mock metadata extractor fixture."""
        return MockMetadataExtractor()
    
    @pytest.fixture
    def validation_service(self):
        """Upload validation service fixture."""
        return UploadValidationService(
            max_file_size=10 * 1024 * 1024,  # 10MB
            allowed_extensions={"mp3", "wav", "flac"}
        )
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Temporary upload directory fixture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def app_service(self, mock_storage, mock_metadata_extractor, validation_service, temp_upload_dir):
        """Upload application service fixture."""
        return UploadApplicationService(
            file_storage=mock_storage,
            metadata_extractor=mock_metadata_extractor,
            validation_service=validation_service,
            upload_folder=temp_upload_dir
        )
    
    @pytest.mark.asyncio
    async def test_start_upload_service_success(self, app_service, temp_upload_dir):
        """Test successful upload service startup."""
        result = await app_service.start_upload_service()
        
        assert result["status"] == "success"
        assert "Upload service started" in result["message"]
        assert result["upload_folder"] == temp_upload_dir
        assert "supported_formats" in result
        
        # Upload folder should be created
        assert Path(temp_upload_dir).exists()
    
    @pytest.mark.asyncio
    async def test_start_upload_service_with_cleanup_task(self, app_service):
        """Test service startup initializes cleanup task."""
        await app_service.start_upload_service()
        
        assert app_service._cleanup_task is not None
        assert not app_service._cleanup_task.done()
        
        # Cleanup
        app_service._cleanup_task.cancel()
        try:
            await app_service._cleanup_task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_create_upload_session_success(self, app_service):
        """Test successful upload session creation."""
        result = await app_service.create_upload_session_use_case(
            filename="test_song.mp3",
            total_size=1024000,  # 1MB
            total_chunks=10,
            playlist_id="playlist-123"
        )
        
        assert result["status"] == "success"
        assert "Upload session created" in result["message"]
        assert "session" in result
        
        session_data = result["session"]
        assert session_data["filename"] == "test_song.mp3"
        assert session_data["total_size_bytes"] == 1024000
        assert session_data["total_chunks"] == 10
        assert session_data["playlist_id"] == "playlist-123"
        assert session_data["status"] == UploadStatus.CREATED.value
        
        # Session should be tracked
        session_id = session_data["session_id"]
        assert session_id in app_service._active_sessions
    
    @pytest.mark.asyncio
    async def test_create_upload_session_validation_error(self, app_service):
        """Test upload session creation with validation error."""
        result = await app_service.create_upload_session_use_case(
            filename="",  # Empty filename
            total_size=1024000,
            total_chunks=10
        )
        
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "validation failed" in result["message"]
        assert "errors" in result
    
    @pytest.mark.asyncio
    async def test_create_upload_session_storage_error(self, app_service, mock_storage):
        """Test upload session creation with storage error."""
        mock_storage.should_fail = True
        
        result = await app_service.create_upload_session_use_case(
            filename="test.mp3",
            total_size=1024,
            total_chunks=1
        )
        
        assert result["status"] == "error"
        assert result["error_type"] == "application_error"
    
    @pytest.mark.asyncio
    async def test_upload_chunk_success(self, app_service):
        """Test successful chunk upload."""
        # Create session first
        session_result = await app_service.create_upload_session_use_case(
            filename="test.mp3",
            total_size=200,
            total_chunks=2
        )
        session_id = session_result["session"]["session_id"]
        
        # Upload first chunk
        chunk_data = b"x" * 100
        result = await app_service.upload_chunk_use_case(session_id, 0, chunk_data)
        
        assert result["status"] == "success"
        assert "Chunk uploaded successfully" in result["message"]
        assert result["chunk_index"] == 0
        assert result["progress"] == 50.0  # 1 of 2 chunks
        
        session_data = result["session"]
        assert session_data["status"] == UploadStatus.IN_PROGRESS.value
        assert session_data["received_chunks"] == 1
    
    @pytest.mark.asyncio
    async def test_upload_chunk_session_not_found(self, app_service):
        """Test chunk upload with non-existent session."""
        result = await app_service.upload_chunk_use_case(
            "nonexistent-session", 0, b"data"
        )
        
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert "session not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_upload_chunk_validation_error(self, app_service):
        """Test chunk upload with validation error."""
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="test.mp3",
            total_size=200,
            total_chunks=2
        )
        session_id = session_result["session"]["session_id"]
        
        # Try to upload chunk with invalid index
        result = await app_service.upload_chunk_use_case(session_id, 10, b"data")  # Index out of range
        
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "validation failed" in result["message"]
    
    @pytest.mark.asyncio
    async def test_upload_chunk_complete_session(self, app_service, mock_storage, temp_upload_dir):
        """Test chunk upload completing a session."""
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="complete_test.mp3",
            total_size=200,
            total_chunks=2,
            playlist_id="playlist-123"
        )
        session_id = session_result["session"]["session_id"]
        
        # Upload both chunks
        await app_service.upload_chunk_use_case(session_id, 0, b"x" * 100)
        result = await app_service.upload_chunk_use_case(session_id, 1, b"y" * 100)
        
        # Should complete the session
        assert result["status"] == "success"
        assert result["progress"] == 100.0
        assert result["completion_status"] == "success"
        assert "file_path" in result
        assert "metadata" in result
        
        # File should be assembled
        expected_path = Path(temp_upload_dir) / "playlist-123" / "complete_test.mp3"
        assert expected_path.exists()
        assert expected_path.stat().st_size == 200
    
    @pytest.mark.asyncio
    async def test_upload_chunk_completion_failure(self, app_service, mock_storage):
        """Test chunk upload with completion failure."""
        mock_storage.should_fail = True
        
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="fail_test.mp3",
            total_size=200,
            total_chunks=2,
            playlist_id="playlist-123"
        )
        session_id = session_result["session"]["session_id"]
        
        # Reset failure for chunk uploads
        mock_storage.should_fail = False
        
        # Upload both chunks
        await app_service.upload_chunk_use_case(session_id, 0, b"x" * 100)
        
        # Enable failure for assembly
        mock_storage.should_fail = True
        
        result = await app_service.upload_chunk_use_case(session_id, 1, b"y" * 100)
        
        # Should fail completion
        assert result["status"] == "success"  # Chunk upload succeeds
        assert result["completion_status"] == "failed"
        assert "completion_errors" in result
        
        # Session should be marked as failed
        session = app_service._active_sessions[session_id]
        assert session.status == UploadStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_get_upload_status_success(self, app_service):
        """Test successful upload status retrieval."""
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="status_test.mp3",
            total_size=1000,
            total_chunks=5
        )
        session_id = session_result["session"]["session_id"]
        
        # Get status
        result = await app_service.get_upload_status_use_case(session_id)
        
        assert result["status"] == "success"
        assert "session" in result
        assert result["session"]["session_id"] == session_id
        assert result["session"]["filename"] == "status_test.mp3"
    
    @pytest.mark.asyncio
    async def test_get_upload_status_not_found(self, app_service):
        """Test upload status for non-existent session."""
        result = await app_service.get_upload_status_use_case("nonexistent-session")
        
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert "session not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_cancel_upload_success(self, app_service, mock_storage):
        """Test successful upload cancellation."""
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="cancel_test.mp3",
            total_size=1000,
            total_chunks=5
        )
        session_id = session_result["session"]["session_id"]
        
        # Cancel upload
        result = await app_service.cancel_upload_use_case(session_id)
        
        assert result["status"] == "success"
        assert "cancelled" in result["message"]
        assert result["session_id"] == session_id
        
        # Session should be marked as cancelled
        session = app_service._active_sessions[session_id]
        assert session.status == UploadStatus.CANCELLED
        
        # Storage cleanup should have been called
        assert session_id not in mock_storage.sessions
    
    @pytest.mark.asyncio
    async def test_cancel_upload_not_found(self, app_service):
        """Test cancelling non-existent upload."""
        result = await app_service.cancel_upload_use_case("nonexistent-session")
        
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert "session not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_list_active_uploads_success(self, app_service):
        """Test listing active uploads."""
        # Create multiple sessions
        session1_result = await app_service.create_upload_session_use_case(
            "test1.mp3", 1000, 5
        )
        session2_result = await app_service.create_upload_session_use_case(
            "test2.mp3", 2000, 10
        )
        
        # Cancel one session
        await app_service.cancel_upload_use_case(session2_result["session"]["session_id"])
        
        # List active uploads
        result = await app_service.list_active_uploads_use_case()
        
        assert result["status"] == "success"
        assert result["count"] == 1  # Only one active
        assert len(result["active_sessions"]) == 1
        assert result["active_sessions"][0]["filename"] == "test1.mp3"
    
    @pytest.mark.asyncio
    async def test_list_active_uploads_empty(self, app_service):
        """Test listing active uploads when none exist."""
        result = await app_service.list_active_uploads_use_case()
        
        assert result["status"] == "success"
        assert result["count"] == 0
        assert result["active_sessions"] == []
    
    @pytest.mark.asyncio
    async def test_handle_upload_completion_validation_failure(self, app_service):
        """Test upload completion with validation failure."""
        # Create session
        session = UploadSession(
            filename="test.mp3",
            total_chunks=2,
            total_size_bytes=200,
            playlist_id="playlist-123"
        )
        
        # Add one chunk (incomplete)
        chunk = FileChunk.create(0, b"x" * 100)
        session.add_chunk(chunk)
        
        # Try to complete (should fail validation)
        result = await app_service._handle_upload_completion(session)
        
        assert result["completion_status"] == "failed"
        assert "completion_errors" in result
        assert session.status == UploadStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_handle_upload_completion_integrity_failure(self, app_service, mock_storage):
        """Test upload completion with integrity failure."""
        # Create complete session
        session = UploadSession(
            filename="integrity_test.mp3",
            total_chunks=2,
            total_size_bytes=200,
            playlist_id="playlist-123"
        )
        
        chunk1 = FileChunk.create(0, b"x" * 100)
        chunk2 = FileChunk.create(1, b"y" * 100)
        session.add_chunk(chunk1)
        session.add_chunk(chunk2)
        
        # Setup storage to fail integrity check
        original_verify = mock_storage.verify_file_integrity
        mock_storage.verify_file_integrity = AsyncMock(return_value=False)
        
        result = await app_service._handle_upload_completion(session)
        
        assert result["completion_status"] == "failed"
        assert any("integrity" in error for error in result["completion_errors"])
        assert session.status == UploadStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_handle_upload_completion_metadata_extraction_failure(self, app_service, mock_metadata_extractor):
        """Test upload completion with metadata extraction failure."""
        mock_metadata_extractor.should_fail = True
        
        # Create complete session
        session = UploadSession(
            filename="metadata_fail_test.mp3",
            total_chunks=1,
            total_size_bytes=100,
            playlist_id="playlist-123"
        )
        
        chunk = FileChunk.create(0, b"x" * 100)
        session.add_chunk(chunk)
        
        result = await app_service._handle_upload_completion(session)
        
        assert result["completion_status"] == "failed"
        assert session.status == UploadStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_periodic_cleanup_expired_sessions(self, app_service, mock_storage):
        """Test periodic cleanup of expired sessions."""
        # Start the service to initiate cleanup task
        await app_service.start_upload_service()
        
        # Create session with short timeout
        session = UploadSession(
            filename="expired_test.mp3",
            total_chunks=1,
            total_size_bytes=100,
            timeout_seconds=1
        )
        app_service._active_sessions[session.session_id] = session
        
        # Simulate time passage
        session.created_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        # Manually run cleanup once
        expired_sessions = []
        for session_id, session in app_service._active_sessions.items():
            if session.is_expired() and session.status in [UploadStatus.CREATED, UploadStatus.IN_PROGRESS]:
                session.mark_expired()
                expired_sessions.append(session_id)
        
        # Cleanup expired sessions
        for session_id in expired_sessions:
            await app_service._file_storage.cleanup_session(session_id)
        
        assert len(expired_sessions) == 1
        assert session.status == UploadStatus.EXPIRED
        
        # Cleanup task
        app_service._cleanup_task.cancel()
        try:
            await app_service._cleanup_task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_storage_error_handling_in_chunk_upload(self, app_service, mock_storage):
        """Test error handling when storage fails during chunk upload."""
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="storage_error_test.mp3",
            total_size=100,
            total_chunks=1
        )
        session_id = session_result["session"]["session_id"]
        
        # Enable storage failure
        mock_storage.should_fail = True
        
        result = await app_service.upload_chunk_use_case(session_id, 0, b"x" * 100)
        
        assert result["status"] == "error"
        assert result["error_type"] == "application_error"
        
        # Session should be marked as failed
        session = app_service._active_sessions[session_id]
        assert session.status == UploadStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_custom_validation_service(self, mock_storage, mock_metadata_extractor, temp_upload_dir):
        """Test using custom validation service."""
        custom_validation = UploadValidationService(
            max_file_size=5 * 1024 * 1024,  # 5MB
            allowed_extensions={"mp3", "wav"}
        )
        
        app_service = UploadApplicationService(
            file_storage=mock_storage,
            metadata_extractor=mock_metadata_extractor,
            validation_service=custom_validation,
            upload_folder=temp_upload_dir
        )
        
        assert app_service._validation_service is custom_validation
    
    @pytest.mark.asyncio
    async def test_session_warnings_propagation(self, app_service):
        """Test that validation warnings are propagated to response."""
        # Create session with a filename that generates warnings
        result = await app_service.create_upload_session_use_case(
            filename="song<with>bad:chars.mp3",  # Problematic characters
            total_size=1024,
            total_chunks=1
        )
        
        assert result["status"] == "success"  # Should still succeed
        assert "warnings" in result
        assert len(result["warnings"]) > 0
    
    @pytest.mark.asyncio
    async def test_upload_folder_creation(self, mock_storage, mock_metadata_extractor):
        """Test upload folder is created on service start."""
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "test_uploads"
            
            app_service = UploadApplicationService(
                file_storage=mock_storage,
                metadata_extractor=mock_metadata_extractor,
                upload_folder=str(upload_dir)
            )
            
            # Folder shouldn't exist initially
            assert not upload_dir.exists()
            
            # Start service
            await app_service.start_upload_service()
            
            # Folder should be created
            assert upload_dir.exists()
            assert upload_dir.is_dir()
    
    @pytest.mark.asyncio
    async def test_concurrent_chunk_uploads(self, app_service):
        """Test handling concurrent chunk uploads to same session."""
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="concurrent_test.mp3",
            total_size=300,
            total_chunks=3
        )
        session_id = session_result["session"]["session_id"]
        
        # Upload chunks concurrently
        tasks = [
            app_service.upload_chunk_use_case(session_id, 0, b"a" * 100),
            app_service.upload_chunk_use_case(session_id, 1, b"b" * 100),
            app_service.upload_chunk_use_case(session_id, 2, b"c" * 100)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All uploads should succeed
        for result in results:
            assert result["status"] == "success"
        
        # Session should be complete
        final_status = await app_service.get_upload_status_use_case(session_id)
        assert final_status["session"]["status"] == UploadStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_session_directory_creation_error_handling(self, app_service, mock_storage):
        """Test error handling when session directory creation fails."""
        # Mock storage to fail on directory creation
        original_create = mock_storage.create_session_directory
        mock_storage.create_session_directory = AsyncMock(side_effect=Exception("Directory creation failed"))
        
        result = await app_service.create_upload_session_use_case(
            filename="test.mp3",
            total_size=1024,
            total_chunks=1
        )
        
        assert result["status"] == "error"
        assert result["error_type"] == "application_error"
        assert "Failed to create upload session" in result["message"]
    
    @pytest.mark.asyncio
    async def test_metadata_validation_in_completion(self, app_service, mock_metadata_extractor):
        """Test metadata validation during upload completion."""
        # Setup extractor to return metadata with warnings
        async def extract_incomplete_metadata(file_path: Path) -> FileMetadata:
            return FileMetadata(
                filename=file_path.name,
                size_bytes=100,
                mime_type="audio/mpeg",
                duration_seconds=0.5  # Too short, will generate warning
            )
        
        mock_metadata_extractor.extract_metadata = extract_incomplete_metadata
        
        # Create and complete session
        session_result = await app_service.create_upload_session_use_case(
            filename="metadata_validation_test.mp3",
            total_size=100,
            total_chunks=1,
            playlist_id="playlist-123"
        )
        session_id = session_result["session"]["session_id"]
        
        result = await app_service.upload_chunk_use_case(session_id, 0, b"x" * 100)
        
        # Should complete successfully but with metadata validation warnings
        assert result["status"] == "success"
        assert result["completion_status"] == "success"
        assert "metadata_validation" in result
        assert not result["metadata_validation"]["valid"]  # Should fail validation
    
    @pytest.mark.asyncio
    async def test_duplicate_chunk_handling(self, app_service):
        """Test handling of duplicate chunk uploads."""
        # Create session
        session_result = await app_service.create_upload_session_use_case(
            filename="duplicate_test.mp3",
            total_size=200,
            total_chunks=2
        )
        session_id = session_result["session"]["session_id"]
        
        # Upload chunk first time
        result1 = await app_service.upload_chunk_use_case(session_id, 0, b"x" * 100)
        assert result1["status"] == "success"
        
        # Upload same chunk again (should fail)
        result2 = await app_service.upload_chunk_use_case(session_id, 0, b"y" * 100)
        assert result2["status"] == "error"
        assert result2["error_type"] == "validation_error"