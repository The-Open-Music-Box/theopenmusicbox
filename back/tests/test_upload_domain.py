# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for Upload Domain layer components following DDD principles.

Tests cover:
- FileChunk value object (immutability and validation)
- FileMetadata value object (immutability and business logic)
- UploadSession entity (business logic and state management)
- AudioFile entity (business logic and validation)
- UploadValidationService domain service (business rules)
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from app.src.domain.upload.value_objects.file_chunk import FileChunk
from app.src.domain.upload.value_objects.file_metadata import FileMetadata
from app.src.domain.upload.entities.upload_session import UploadSession, UploadStatus
from app.src.domain.upload.entities.audio_file import AudioFile
from app.src.domain.upload.services.upload_validation_service import UploadValidationService


class TestFileChunkValueObject:
    """Test FileChunk value object for immutability and validation."""
    
    def test_file_chunk_creation(self):
        """Test basic file chunk creation."""
        data = b"Hello, World!"
        chunk = FileChunk(index=0, data=data, size=len(data))
        
        assert chunk.index == 0
        assert chunk.data == data
        assert chunk.size == len(data)
        assert chunk.checksum == ""
    
    def test_file_chunk_immutability(self):
        """Test that FileChunk is immutable."""
        chunk = FileChunk(index=0, data=b"test", size=4)
        
        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            chunk.index = 1
        with pytest.raises(AttributeError):
            chunk.data = b"modified"
        with pytest.raises(AttributeError):
            chunk.size = 10
    
    def test_file_chunk_validation_negative_index(self):
        """Test validation fails for negative index."""
        with pytest.raises(ValueError, match="Chunk index cannot be negative"):
            FileChunk(index=-1, data=b"test", size=4)
    
    def test_file_chunk_validation_negative_size(self):
        """Test validation fails for negative size."""
        with pytest.raises(ValueError, match="Chunk size cannot be negative"):
            FileChunk(index=0, data=b"test", size=-1)
    
    def test_file_chunk_validation_size_mismatch(self):
        """Test validation fails when size doesn't match data length."""
        with pytest.raises(ValueError, match="Chunk size does not match data length"):
            FileChunk(index=0, data=b"test", size=10)  # data is 4 bytes, size is 10
    
    def test_file_chunk_validation_empty_chunk(self):
        """Test validation fails for empty chunk."""
        with pytest.raises(ValueError, match="Chunk cannot be empty"):
            FileChunk(index=0, data=b"", size=0)
    
    def test_file_chunk_create_factory(self):
        """Test factory method with automatic size calculation."""
        data = b"Hello, World!"
        chunk = FileChunk.create(index=5, data=data, checksum="abc123")
        
        assert chunk.index == 5
        assert chunk.data == data
        assert chunk.size == len(data)
        assert chunk.checksum == "abc123"
    
    def test_file_chunk_is_valid_size(self):
        """Test chunk size validation."""
        small_chunk = FileChunk.create(0, b"small")
        large_chunk = FileChunk.create(1, b"x" * 2000)
        
        # Test with 1KB limit
        max_size = 1024
        assert small_chunk.is_valid_size(max_size)
        assert not large_chunk.is_valid_size(max_size)
        
        # Test with very small limit
        assert not small_chunk.is_valid_size(3)  # "small" is 5 bytes
    
    def test_file_chunk_data_preview(self):
        """Test hex preview functionality."""
        data = bytes(range(50))  # 50 bytes: 00 01 02 ... 31
        chunk = FileChunk.create(0, data)
        
        # Default preview (32 bytes)
        preview = chunk.get_data_preview()
        assert len(preview) == 64  # 32 bytes = 64 hex chars
        assert preview.startswith("000102")
        
        # Custom preview length
        short_preview = chunk.get_data_preview(preview_length=4)
        assert len(short_preview) == 8  # 4 bytes = 8 hex chars
        assert short_preview == "00010203"
    
    def test_file_chunk_string_representation(self):
        """Test string representation."""
        chunk = FileChunk.create(3, b"Hello")
        assert str(chunk) == "Chunk(3, 5 bytes)"
    
    def test_file_chunk_with_checksum(self):
        """Test chunk creation with checksum."""
        chunk = FileChunk(index=0, data=b"test", size=4, checksum="md5hash")
        assert chunk.checksum == "md5hash"


class TestFileMetadataValueObject:
    """Test FileMetadata value object for immutability and business logic."""
    
    def test_file_metadata_creation(self):
        """Test basic file metadata creation."""
        metadata = FileMetadata(
            filename="test.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            title="Test Song",
            artist="Test Artist"
        )
        
        assert metadata.filename == "test.mp3"
        assert metadata.size_bytes == 1024
        assert metadata.mime_type == "audio/mpeg"
        assert metadata.title == "Test Song"
        assert metadata.artist == "Test Artist"
        assert metadata.extra_attributes == {}
    
    def test_file_metadata_immutability(self):
        """Test that FileMetadata is immutable."""
        metadata = FileMetadata(filename="test.mp3", size_bytes=1024, mime_type="audio/mpeg")
        
        with pytest.raises(AttributeError):
            metadata.filename = "modified.mp3"
        with pytest.raises(AttributeError):
            metadata.size_bytes = 2048
    
    def test_file_metadata_validation_empty_filename(self):
        """Test validation fails for empty filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            FileMetadata(filename="", size_bytes=1024, mime_type="audio/mpeg")
    
    def test_file_metadata_validation_negative_size(self):
        """Test validation fails for negative size."""
        with pytest.raises(ValueError, match="File size cannot be negative"):
            FileMetadata(filename="test.mp3", size_bytes=-1, mime_type="audio/mpeg")
    
    def test_file_metadata_validation_empty_mime_type(self):
        """Test validation fails for empty MIME type."""
        with pytest.raises(ValueError, match="MIME type is required"):
            FileMetadata(filename="test.mp3", size_bytes=1024, mime_type="")
    
    def test_file_metadata_properties(self):
        """Test computed properties."""
        metadata = FileMetadata(
            filename="test_song.mp3",
            size_bytes=2097152,  # 2MB
            mime_type="audio/mpeg",
            title="My Song",
            duration_seconds=180.5
        )
        
        assert metadata.file_extension == ".mp3"
        assert metadata.display_name == "My Song"  # Uses title
        assert metadata.size_mb == 2.0
        assert metadata.duration_formatted == "03:00"  # 3:00.5 -> 3:00
    
    def test_file_metadata_display_name_fallback(self):
        """Test display name falls back to filename stem."""
        metadata = FileMetadata(
            filename="awesome_track.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg"
            # No title provided
        )
        
        assert metadata.display_name == "awesome_track"
    
    def test_file_metadata_duration_formatting(self):
        """Test duration formatting edge cases."""
        # No duration
        no_duration = FileMetadata(filename="test.mp3", size_bytes=1024, mime_type="audio/mpeg")
        assert no_duration.duration_formatted == "Unknown"
        
        # Various durations
        test_cases = [
            (59, "00:59"),      # 59 seconds
            (60, "01:00"),      # 1 minute
            (125, "02:05"),     # 2:05
            (3661, "61:01"),    # Over 1 hour
            (0, "00:00"),       # Zero seconds
        ]
        
        for seconds, expected in test_cases:
            metadata = FileMetadata(
                filename="test.mp3",
                size_bytes=1024,
                mime_type="audio/mpeg",
                duration_seconds=seconds
            )
            assert metadata.duration_formatted == expected
    
    def test_file_metadata_is_audio_file(self):
        """Test audio file detection."""
        audio_types = [
            "audio/mpeg",
            "audio/wav",
            "audio/flac",
            "audio/ogg"
        ]
        
        non_audio_types = [
            "video/mp4",
            "image/jpeg",
            "text/plain",
            "application/pdf"
        ]
        
        for mime_type in audio_types:
            metadata = FileMetadata(filename="test.mp3", size_bytes=1024, mime_type=mime_type)
            assert metadata.is_audio_file()
        
        for mime_type in non_audio_types:
            metadata = FileMetadata(filename="test.mp3", size_bytes=1024, mime_type=mime_type)
            assert not metadata.is_audio_file()
    
    def test_file_metadata_is_supported_format(self):
        """Test supported format checking."""
        metadata = FileMetadata(filename="test.mp3", size_bytes=1024, mime_type="audio/mpeg")
        
        supported_formats = {"mp3", "wav", "flac"}
        assert metadata.is_supported_format(supported_formats)
        
        unsupported_formats = {"ogg", "m4a"}
        assert not metadata.is_supported_format(unsupported_formats)
    
    def test_file_metadata_has_complete_metadata(self):
        """Test complete metadata checking."""
        # Complete metadata
        complete = FileMetadata(
            filename="test.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            title="Song Title",
            artist="Artist Name",
            duration_seconds=180.0
        )
        assert complete.has_complete_metadata()
        
        # Missing title
        no_title = FileMetadata(
            filename="test.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            artist="Artist Name",
            duration_seconds=180.0
        )
        assert not no_title.has_complete_metadata()
        
        # Missing artist
        no_artist = FileMetadata(
            filename="test.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            title="Song Title",
            duration_seconds=180.0
        )
        assert not no_artist.has_complete_metadata()
        
        # Missing duration
        no_duration = FileMetadata(
            filename="test.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            title="Song Title",
            artist="Artist Name"
        )
        assert not no_duration.has_complete_metadata()
    
    def test_file_metadata_to_dict(self):
        """Test dictionary serialization."""
        metadata = FileMetadata(
            filename="test_song.mp3",
            size_bytes=2097152,
            mime_type="audio/mpeg",
            title="My Song",
            artist="Artist",
            album="Album",
            duration_seconds=180.5,
            bitrate=320,
            sample_rate=44100,
            extra_attributes={"genre": "rock"}
        )
        
        result = metadata.to_dict()
        
        expected_keys = {
            "filename", "size_bytes", "size_mb", "mime_type", "title",
            "artist", "album", "duration_seconds", "duration_formatted",
            "bitrate", "sample_rate", "file_extension", "display_name",
            "extra_attributes"
        }
        
        assert set(result.keys()) == expected_keys
        assert result["filename"] == "test_song.mp3"
        assert result["size_mb"] == 2.0
        assert result["duration_formatted"] == "03:00"
        assert result["extra_attributes"] == {"genre": "rock"}
    
    def test_file_metadata_create_minimal(self):
        """Test minimal metadata factory."""
        metadata = FileMetadata.create_minimal("simple.mp3", 1024, "audio/mpeg")
        
        assert metadata.filename == "simple.mp3"
        assert metadata.size_bytes == 1024
        assert metadata.mime_type == "audio/mpeg"
        assert metadata.title is None
        assert metadata.artist is None
        assert metadata.extra_attributes == {}


class TestUploadSessionEntity:
    """Test UploadSession entity for business logic and state management."""
    
    def test_upload_session_creation(self):
        """Test basic upload session creation."""
        session = UploadSession(
            filename="test.mp3",
            total_chunks=10,
            total_size_bytes=1024,
            playlist_id="playlist-123"
        )
        
        assert session.filename == "test.mp3"
        assert session.total_chunks == 10
        assert session.total_size_bytes == 1024
        assert session.playlist_id == "playlist-123"
        assert session.status == UploadStatus.CREATED
        assert len(session.session_id) > 0
        assert session.received_chunks == set()
        assert session.current_size_bytes == 0
    
    def test_upload_session_validation_empty_filename(self):
        """Test validation fails for empty filename."""
        with pytest.raises(ValueError, match="Filename is required"):
            UploadSession(filename="", total_chunks=10, total_size_bytes=1024)
    
    def test_upload_session_validation_invalid_chunks(self):
        """Test validation fails for invalid chunk count."""
        with pytest.raises(ValueError, match="Total chunks must be positive"):
            UploadSession(filename="test.mp3", total_chunks=0, total_size_bytes=1024)
        
        with pytest.raises(ValueError, match="Total chunks must be positive"):
            UploadSession(filename="test.mp3", total_chunks=-1, total_size_bytes=1024)
    
    def test_upload_session_validation_invalid_size(self):
        """Test validation fails for invalid size."""
        with pytest.raises(ValueError, match="Total size must be positive"):
            UploadSession(filename="test.mp3", total_chunks=10, total_size_bytes=0)
        
        with pytest.raises(ValueError, match="Total size must be positive"):
            UploadSession(filename="test.mp3", total_chunks=10, total_size_bytes=-1)
    
    def test_upload_session_timeout_calculation(self):
        """Test timeout calculation."""
        session = UploadSession(
            filename="test.mp3",
            total_chunks=10,
            total_size_bytes=1024,
            timeout_seconds=3600
        )
        
        timeout_at = session.timeout_at
        expected = datetime.fromtimestamp(
            session.created_at.timestamp() + 3600,
            tz=timezone.utc
        )
        
        # Allow small variance for test execution time
        assert abs((timeout_at - expected).total_seconds()) < 1
    
    def test_upload_session_progress_calculation(self):
        """Test progress percentage calculation."""
        session = UploadSession(filename="test.mp3", total_chunks=10, total_size_bytes=1000)
        
        # Initially 0%
        assert session.progress_percentage == 0.0
        
        # Add some chunks
        session.received_chunks.add(0)
        session.received_chunks.add(1)
        session.received_chunks.add(2)
        
        # Should be 30%
        assert session.progress_percentage == 30.0
        
        # Add all chunks
        for i in range(10):
            session.received_chunks.add(i)
        
        # Should be 100%
        assert session.progress_percentage == 100.0
    
    def test_upload_session_size_progress_calculation(self):
        """Test size-based progress calculation."""
        session = UploadSession(filename="test.mp3", total_chunks=10, total_size_bytes=1000)
        
        # Initially 0%
        assert session.size_progress_percentage == 0.0
        
        # Add some size
        session.current_size_bytes = 300
        assert session.size_progress_percentage == 30.0
        
        # Full size
        session.current_size_bytes = 1000
        assert session.size_progress_percentage == 100.0
    
    def test_upload_session_expiration(self):
        """Test session expiration logic."""
        session = UploadSession(
            filename="test.mp3",
            total_chunks=10,
            total_size_bytes=1024,
            timeout_seconds=1
        )
        
        # Should not be expired initially
        assert not session.is_expired()
        assert session.is_active()
        
        # Simulate time passage
        session.created_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        # Should now be expired
        assert session.is_expired()
        assert not session.is_active()
    
    def test_upload_session_add_chunk(self):
        """Test adding chunks to session."""
        session = UploadSession(filename="test.mp3", total_chunks=3, total_size_bytes=300)
        
        chunk1 = FileChunk.create(0, b"x" * 100)
        chunk2 = FileChunk.create(1, b"y" * 100)
        
        # Add first chunk
        session.add_chunk(chunk1)
        
        assert 0 in session.received_chunks
        assert session.current_size_bytes == 100
        assert session.status == UploadStatus.IN_PROGRESS
        
        # Add second chunk
        session.add_chunk(chunk2)
        
        assert 1 in session.received_chunks
        assert session.current_size_bytes == 200
    
    def test_upload_session_add_chunk_validation(self):
        """Test chunk addition validation."""
        session = UploadSession(filename="test.mp3", total_chunks=3, total_size_bytes=300)
        
        # Invalid chunk index (negative)
        bad_chunk = FileChunk.create(-1, b"test")
        with pytest.raises(ValueError, match="Chunk index .* out of range"):
            session.add_chunk(bad_chunk)
        
        # Invalid chunk index (too high)
        bad_chunk2 = FileChunk.create(10, b"test")
        with pytest.raises(ValueError, match="Chunk index .* out of range"):
            session.add_chunk(bad_chunk2)
        
        # Duplicate chunk
        chunk = FileChunk.create(0, b"test")
        session.add_chunk(chunk)
        
        with pytest.raises(ValueError, match="Chunk .* already received"):
            session.add_chunk(chunk)
    
    def test_upload_session_add_chunk_inactive_session(self):
        """Test adding chunk to inactive session fails."""
        session = UploadSession(filename="test.mp3", total_chunks=3, total_size_bytes=300)
        session.mark_failed("Test failure")
        
        chunk = FileChunk.create(0, b"test")
        with pytest.raises(ValueError, match="Cannot add chunk to inactive session"):
            session.add_chunk(chunk)
    
    def test_upload_session_completion(self):
        """Test session completion."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        chunk1 = FileChunk.create(0, b"x" * 100)
        chunk2 = FileChunk.create(1, b"y" * 100)
        
        # Add chunks
        session.add_chunk(chunk1)
        assert not session.is_complete()
        assert session.status == UploadStatus.IN_PROGRESS
        
        session.add_chunk(chunk2)
        assert session.is_complete()
        assert session.status == UploadStatus.COMPLETED
        assert session.completed_at is not None
    
    def test_upload_session_mark_completed_validation(self):
        """Test mark completed validation."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        # Cannot mark incomplete session as completed
        with pytest.raises(ValueError, match="Cannot mark incomplete session as completed"):
            session.mark_completed()
    
    def test_upload_session_mark_failed(self):
        """Test marking session as failed."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        session.mark_failed("Network error")
        
        assert session.status == UploadStatus.FAILED
        assert session.error_message == "Network error"
        assert session.completed_at is not None
        assert not session.is_active()
    
    def test_upload_session_mark_cancelled(self):
        """Test marking session as cancelled."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        session.mark_cancelled()
        
        assert session.status == UploadStatus.CANCELLED
        assert session.completed_at is not None
        assert not session.is_active()
    
    def test_upload_session_mark_expired(self):
        """Test marking session as expired."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        session.mark_expired()
        
        assert session.status == UploadStatus.EXPIRED
        assert session.completed_at is not None
        assert not session.is_active()
    
    def test_upload_session_set_metadata(self):
        """Test setting file metadata."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        metadata = FileMetadata.create_minimal("test.mp3", 200, "audio/mpeg")
        
        session.set_metadata(metadata)
        
        assert session.file_metadata == metadata
    
    def test_upload_session_get_missing_chunks(self):
        """Test getting missing chunks."""
        session = UploadSession(filename="test.mp3", total_chunks=5, total_size_bytes=500)
        
        # Initially all chunks missing
        missing = session.get_missing_chunks()
        assert missing == {0, 1, 2, 3, 4}
        
        # Add some chunks
        chunk0 = FileChunk.create(0, b"x" * 100)
        chunk2 = FileChunk.create(2, b"z" * 100)
        chunk4 = FileChunk.create(4, b"v" * 100)
        
        session.add_chunk(chunk0)
        session.add_chunk(chunk2)
        session.add_chunk(chunk4)
        
        missing = session.get_missing_chunks()
        assert missing == {1, 3}
    
    def test_upload_session_get_remaining_seconds(self):
        """Test remaining seconds calculation."""
        session = UploadSession(
            filename="test.mp3",
            total_chunks=2,
            total_size_bytes=200,
            timeout_seconds=60
        )
        
        # Should have approximately 60 seconds remaining
        remaining = session.get_remaining_seconds()
        assert 55 <= remaining <= 60  # Allow variance for test execution
        
        # Expired session should have 0 seconds
        session.created_at = datetime.now(timezone.utc) - timedelta(seconds=120)
        assert session.get_remaining_seconds() == 0
    
    def test_upload_session_validate_chunk_size_consistency(self):
        """Test chunk size consistency validation."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        # Add chunks
        chunk1 = FileChunk.create(0, b"x" * 100)
        chunk2 = FileChunk.create(1, b"y" * 100)
        session.add_chunk(chunk1)
        session.add_chunk(chunk2)
        
        # Size should match
        assert session.validate_chunk_size_consistency(200)
        assert not session.validate_chunk_size_consistency(150)
    
    def test_upload_session_to_dict(self):
        """Test session serialization."""
        session = UploadSession(
            filename="test.mp3",
            total_chunks=3,
            total_size_bytes=300,
            playlist_id="playlist-123"
        )
        
        chunk = FileChunk.create(0, b"x" * 100)
        session.add_chunk(chunk)
        
        metadata = FileMetadata.create_minimal("test.mp3", 300, "audio/mpeg")
        session.set_metadata(metadata)
        
        result = session.to_dict()
        
        expected_keys = {
            "session_id", "filename", "playlist_id", "status", "progress_percentage",
            "size_progress_percentage", "total_chunks", "received_chunks",
            "missing_chunks", "total_size_bytes", "current_size_bytes",
            "created_at", "completed_at", "remaining_seconds", "file_metadata",
            "error_message"
        }
        
        assert set(result.keys()) == expected_keys
        assert result["filename"] == "test.mp3"
        assert result["status"] == UploadStatus.IN_PROGRESS.value
        assert result["received_chunks"] == 1
        assert result["missing_chunks"] == 2
        assert result["file_metadata"] is not None


class TestAudioFileEntity:
    """Test AudioFile entity for business logic and validation."""
    
    @pytest.fixture
    def temp_audio_file(self):
        """Create temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b"fake mp3 data" * 100)  # 1300 bytes
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    def test_audio_file_creation(self, temp_audio_file):
        """Test basic audio file creation."""
        metadata = FileMetadata(
            filename=temp_audio_file.name,
            size_bytes=1300,
            mime_type="audio/mpeg",
            title="Test Song"
        )
        
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        assert audio_file.file_path == temp_audio_file
        assert audio_file.metadata == metadata
        assert audio_file.playlist_id is None
        assert not audio_file.is_processed
        assert audio_file.processing_error is None
    
    def test_audio_file_validation_no_path(self):
        """Test validation fails for missing path."""
        metadata = FileMetadata.create_minimal("test.mp3", 1024, "audio/mpeg")
        
        with pytest.raises(ValueError, match="File path is required"):
            AudioFile(file_path=None, metadata=metadata)
    
    def test_audio_file_validation_no_metadata(self):
        """Test validation fails for missing metadata."""
        with pytest.raises(ValueError, match="File metadata is required"):
            AudioFile(file_path=Path("test.mp3"), metadata=None)
    
    def test_audio_file_validation_non_audio_file(self):
        """Test validation fails for non-audio file."""
        metadata = FileMetadata(
            filename="test.txt",
            size_bytes=100,
            mime_type="text/plain"
        )
        
        with pytest.raises(ValueError, match="File must be an audio file"):
            AudioFile(file_path=Path("test.txt"), metadata=metadata)
    
    def test_audio_file_properties(self, temp_audio_file):
        """Test audio file properties."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        assert audio_file.filename == temp_audio_file.name
        assert audio_file.file_exists
        assert audio_file.file_size_matches_metadata
    
    def test_audio_file_file_size_mismatch(self, temp_audio_file):
        """Test detection of file size mismatch."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 999, "audio/mpeg")  # Wrong size
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        assert not audio_file.file_size_matches_metadata
    
    def test_audio_file_nonexistent_file(self):
        """Test behavior with nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.mp3")
        metadata = FileMetadata.create_minimal("file.mp3", 1024, "audio/mpeg")
        audio_file = AudioFile(file_path=nonexistent_path, metadata=metadata)
        
        assert not audio_file.file_exists
        assert not audio_file.file_size_matches_metadata
    
    def test_audio_file_mark_processed(self, temp_audio_file):
        """Test marking file as processed."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        audio_file.mark_processed()
        
        assert audio_file.is_processed
        assert audio_file.processing_error is None
    
    def test_audio_file_mark_processing_failed(self, temp_audio_file):
        """Test marking file processing as failed."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        audio_file.mark_processing_failed("Unsupported codec")
        
        assert not audio_file.is_processed
        assert audio_file.processing_error == "Unsupported codec"
    
    def test_audio_file_set_playlist(self, temp_audio_file):
        """Test playlist association."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        audio_file.set_playlist("playlist-123")
        
        assert audio_file.playlist_id == "playlist-123"
    
    def test_audio_file_set_playlist_validation(self, temp_audio_file):
        """Test playlist association validation."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        with pytest.raises(ValueError, match="Playlist ID cannot be empty"):
            audio_file.set_playlist("")
        
        with pytest.raises(ValueError, match="Playlist ID cannot be empty"):
            audio_file.set_playlist("   ")
    
    def test_audio_file_is_valid_for_playlist(self, temp_audio_file):
        """Test playlist validity checking."""
        complete_metadata = FileMetadata(
            filename=temp_audio_file.name,
            size_bytes=1300,
            mime_type="audio/mpeg",
            title="Test Song",
            artist="Test Artist",
            duration_seconds=180.0
        )
        
        audio_file = AudioFile(file_path=temp_audio_file, metadata=complete_metadata)
        
        # Should be valid with complete metadata and existing file
        assert audio_file.is_valid_for_playlist()
        
        # Mark as having processing error
        audio_file.mark_processing_failed("Test error")
        assert not audio_file.is_valid_for_playlist()
    
    def test_audio_file_get_track_info(self, temp_audio_file):
        """Test track info extraction."""
        metadata = FileMetadata(
            filename=temp_audio_file.name,
            size_bytes=1300,
            mime_type="audio/mpeg",
            title="My Song",
            artist="My Artist",
            album="My Album",
            duration_seconds=240.5
        )
        
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        track_info = audio_file.get_track_info()
        
        expected = {
            "title": "My Song",
            "artist": "My Artist",
            "album": "My Album",
            "filename": temp_audio_file.name,
            "file_path": str(temp_audio_file),
            "duration_ms": 240500,  # 240.5 * 1000
            "size_bytes": 1300
        }
        
        assert track_info == expected
    
    def test_audio_file_get_track_info_no_duration(self, temp_audio_file):
        """Test track info with no duration."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        track_info = audio_file.get_track_info()
        
        assert track_info["duration_ms"] is None
        assert track_info["title"] == temp_audio_file.stem  # Falls back to filename stem
    
    def test_audio_file_validate_integrity(self, temp_audio_file):
        """Test file integrity validation."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        assert audio_file.validate_integrity()
        
        # Test with wrong size
        wrong_size_metadata = FileMetadata.create_minimal(temp_audio_file.name, 999, "audio/mpeg")
        wrong_file = AudioFile(file_path=temp_audio_file, metadata=wrong_size_metadata)
        
        assert not wrong_file.validate_integrity()
    
    def test_audio_file_string_representation(self, temp_audio_file):
        """Test string representation."""
        metadata = FileMetadata.create_minimal(temp_audio_file.name, 1300, "audio/mpeg")
        audio_file = AudioFile(file_path=temp_audio_file, metadata=metadata)
        
        expected = f"AudioFile({temp_audio_file.name}, {1300/(1024*1024):.1f}MB)"
        assert str(audio_file) == expected


class TestUploadValidationServiceDomainService:
    """Test UploadValidationService domain service for business rules."""
    
    @pytest.fixture
    def validation_service(self):
        """Standard validation service with default settings."""
        return UploadValidationService(
            max_file_size=50 * 1024 * 1024,  # 50MB
            max_chunk_size=1024 * 1024,      # 1MB
            allowed_extensions={"mp3", "wav", "flac"},
            min_audio_duration=1.0
        )
    
    def test_validate_upload_request_valid(self, validation_service):
        """Test validation of valid upload request."""
        result = validation_service.validate_upload_request(
            filename="test_song.mp3",
            total_size=1024 * 1024,  # 1MB
            total_chunks=10,
            playlist_id="playlist-123"
        )
        
        assert result["valid"]
        assert result["errors"] == []
        assert result["filename"] == "test_song.mp3"
    
    def test_validate_upload_request_invalid_filename(self, validation_service):
        """Test validation fails for invalid filename."""
        # Empty filename
        result = validation_service.validate_upload_request("", 1024, 10)
        assert not result["valid"]
        assert any("Filename cannot be empty" in error for error in result["errors"])
        
        # Unsupported extension
        result = validation_service.validate_upload_request("song.xyz", 1024, 10)
        assert not result["valid"]
        assert any("not allowed" in error for error in result["errors"])
    
    def test_validate_upload_request_invalid_size(self, validation_service):
        """Test validation fails for invalid file size."""
        # Zero size
        result = validation_service.validate_upload_request("song.mp3", 0, 10)
        assert not result["valid"]
        assert any("File size must be positive" in error for error in result["errors"])
        
        # Too large
        huge_size = 200 * 1024 * 1024  # 200MB
        result = validation_service.validate_upload_request("song.mp3", huge_size, 10)
        assert not result["valid"]
        assert any("exceeds maximum allowed size" in error for error in result["errors"])
    
    def test_validate_upload_request_invalid_chunks(self, validation_service):
        """Test validation fails for invalid chunk configuration."""
        # Zero chunks
        result = validation_service.validate_upload_request("song.mp3", 1024, 0)
        assert not result["valid"]
        assert any("Chunk count must be positive" in error for error in result["errors"])
        
        # Too many chunks
        result = validation_service.validate_upload_request("song.mp3", 1024, 20000)
        assert not result["valid"]
        assert any("Too many chunks" in error for error in result["errors"])
        
        # Chunks too large on average
        result = validation_service.validate_upload_request("song.mp3", 10 * 1024 * 1024, 5)  # 2MB per chunk avg
        assert not result["valid"]
        assert any("Average chunk size" in error for error in result["errors"])
    
    def test_validate_chunk_valid(self, validation_service):
        """Test validation of valid chunk."""
        session = UploadSession(filename="test.mp3", total_chunks=5, total_size_bytes=500)
        chunk = FileChunk.create(0, b"x" * 100)
        
        result = validation_service.validate_chunk(chunk, session)
        
        assert result["valid"]
        assert result["errors"] == []
        assert result["chunk_index"] == 0
    
    def test_validate_chunk_invalid_index(self, validation_service):
        """Test chunk validation fails for invalid index."""
        session = UploadSession(filename="test.mp3", total_chunks=5, total_size_bytes=500)
        
        # Negative index
        bad_chunk = FileChunk.create(-1, b"test")
        result = validation_service.validate_chunk(bad_chunk, session)
        assert not result["valid"]
        assert any("cannot be negative" in error for error in result["errors"])
        
        # Index out of range
        bad_chunk2 = FileChunk.create(10, b"test")
        result = validation_service.validate_chunk(bad_chunk2, session)
        assert not result["valid"]
        assert any("exceeds session total chunks" in error for error in result["errors"])
    
    def test_validate_chunk_size_exceeded(self, validation_service):
        """Test chunk validation fails for oversized chunks."""
        session = UploadSession(filename="test.mp3", total_chunks=5, total_size_bytes=5000000)
        huge_chunk = FileChunk.create(0, b"x" * (2 * 1024 * 1024))  # 2MB chunk
        
        result = validation_service.validate_chunk(huge_chunk, session)
        
        assert not result["valid"]
        assert any("exceeds maximum" in error for error in result["errors"])
    
    def test_validate_chunk_duplicate(self, validation_service):
        """Test chunk validation warns for duplicates."""
        session = UploadSession(filename="test.mp3", total_chunks=5, total_size_bytes=500)
        chunk = FileChunk.create(0, b"x" * 100)
        
        # Mark chunk as already received
        session.received_chunks.add(0)
        
        result = validation_service.validate_chunk(chunk, session)
        
        assert result["valid"]  # Warning, not error
        assert any("already received" in warning for warning in result["warnings"])
    
    def test_validate_chunk_inactive_session(self, validation_service):
        """Test chunk validation fails for inactive session."""
        session = UploadSession(filename="test.mp3", total_chunks=5, total_size_bytes=500)
        session.mark_failed("Test failure")
        
        chunk = FileChunk.create(0, b"x" * 100)
        result = validation_service.validate_chunk(chunk, session)
        
        assert not result["valid"]
        assert any("not active" in error for error in result["errors"])
    
    def test_validate_session_completion_valid(self, validation_service):
        """Test validation of complete session."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        # Add all chunks
        chunk1 = FileChunk.create(0, b"x" * 100)
        chunk2 = FileChunk.create(1, b"y" * 100)
        session.add_chunk(chunk1)
        session.add_chunk(chunk2)
        
        result = validation_service.validate_session_completion(session)
        
        assert result["valid"]
        assert result["errors"] == []
        assert result["progress"] == 100.0
    
    def test_validate_session_completion_missing_chunks(self, validation_service):
        """Test validation fails for incomplete session."""
        session = UploadSession(filename="test.mp3", total_chunks=5, total_size_bytes=500)
        
        # Only add one chunk
        chunk = FileChunk.create(0, b"x" * 100)
        session.add_chunk(chunk)
        
        result = validation_service.validate_session_completion(session)
        
        assert not result["valid"]
        assert any("Missing" in error for error in result["errors"])
    
    def test_validate_session_completion_size_mismatch(self, validation_service):
        """Test validation fails for size mismatch."""
        session = UploadSession(filename="test.mp3", total_chunks=2, total_size_bytes=200)
        
        # Add chunks with wrong total size
        chunk1 = FileChunk.create(0, b"x" * 50)   # 50 bytes
        chunk2 = FileChunk.create(1, b"y" * 50)   # 50 bytes, total 100 != 200
        session.add_chunk(chunk1)
        session.add_chunk(chunk2)
        
        result = validation_service.validate_session_completion(session)
        
        assert not result["valid"]
        assert any("Size mismatch" in error for error in result["errors"])
    
    def test_validate_audio_metadata_valid(self, validation_service):
        """Test validation of valid audio metadata."""
        metadata = FileMetadata(
            filename="song.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            title="My Song",
            artist="My Artist",
            duration_seconds=180.0,
            bitrate=320
        )
        
        result = validation_service.validate_audio_metadata(metadata)
        
        assert result["valid"]
        assert result["has_complete_metadata"]
        assert result["errors"] == []
    
    def test_validate_audio_metadata_non_audio(self, validation_service):
        """Test validation fails for non-audio files."""
        metadata = FileMetadata(
            filename="document.pdf",
            size_bytes=1024,
            mime_type="application/pdf"
        )
        
        result = validation_service.validate_audio_metadata(metadata)
        
        assert not result["valid"]
        assert any("not an audio format" in error for error in result["errors"])
    
    def test_validate_audio_metadata_unsupported_format(self, validation_service):
        """Test validation fails for unsupported audio format."""
        metadata = FileMetadata(
            filename="song.aac",
            size_bytes=1024,
            mime_type="audio/aac"
        )
        
        result = validation_service.validate_audio_metadata(metadata)
        
        assert not result["valid"]
        assert any("not supported" in error for error in result["errors"])
    
    def test_validate_audio_metadata_short_duration(self, validation_service):
        """Test validation fails for too short audio."""
        metadata = FileMetadata(
            filename="short.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            duration_seconds=0.5  # Less than 1 second minimum
        )
        
        result = validation_service.validate_audio_metadata(metadata)
        
        assert not result["valid"]
        assert any("too short" in error for error in result["errors"])
    
    def test_validate_audio_metadata_warnings(self, validation_service):
        """Test metadata validation warnings."""
        # Missing title and artist
        metadata = FileMetadata(
            filename="unnamed.mp3",
            size_bytes=1024,
            mime_type="audio/mpeg",
            duration_seconds=180.0,
            bitrate=32  # Very low bitrate
        )
        
        result = validation_service.validate_audio_metadata(metadata)
        
        assert result["valid"]  # Valid but with warnings
        assert len(result["warnings"]) >= 3  # Missing title, artist, low bitrate
        assert any("title is missing" in warning for warning in result["warnings"])
        assert any("artist is missing" in warning for warning in result["warnings"])
        assert any("very low" in warning for warning in result["warnings"])
    
    def test_validate_filename_problematic_characters(self, validation_service):
        """Test filename validation for problematic characters."""
        result = validation_service._validate_filename("song<with>bad:chars.mp3")
        
        assert len(result["warnings"]) > 0
        assert any("problematic characters" in warning for warning in result["warnings"])
    
    def test_validate_filename_reserved_names(self, validation_service):
        """Test filename validation for reserved names."""
        result = validation_service._validate_filename("CON.mp3")
        
        assert len(result["errors"]) > 0
        assert any("reserved filename" in error for error in result["errors"])
    
    def test_validate_filename_too_long(self, validation_service):
        """Test filename validation for excessive length."""
        long_name = "x" * 300 + ".mp3"
        result = validation_service._validate_filename(long_name)
        
        assert len(result["errors"]) > 0
        assert any("too long" in error for error in result["errors"])