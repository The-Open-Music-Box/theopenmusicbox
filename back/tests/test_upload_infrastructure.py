# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for Upload Infrastructure layer following DDD principles.

Tests cover:
- LocalFileStorageAdapter protocol compliance
- MutagenMetadataExtractor protocol compliance
- MockMetadataExtractor implementation
- File operations and error handling
- Protocol contract adherence
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from app.src.infrastructure.upload.adapters.file_storage_adapter import LocalFileStorageAdapter
from app.src.infrastructure.upload.adapters.metadata_extractor import (
    MutagenMetadataExtractor,
    MockMetadataExtractor
)
from app.src.domain.upload.protocols.file_storage_protocol import (
    FileStorageProtocol,
    MetadataExtractionProtocol
)
from app.src.domain.upload.value_objects.file_chunk import FileChunk
from app.src.domain.upload.value_objects.file_metadata import FileMetadata
from app.src.domain.upload.entities.upload_session import UploadSession


class TestLocalFileStorageAdapter:
    """Test LocalFileStorageAdapter protocol compliance and functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def storage_adapter(self, temp_dir):
        """File storage adapter fixture."""
        return LocalFileStorageAdapter(temp_dir)
    
    def test_adapter_implements_protocol(self, storage_adapter):
        """Test that adapter implements FileStorageProtocol."""
        assert isinstance(storage_adapter, FileStorageProtocol)
    
    def test_adapter_initialization(self, temp_dir):
        """Test adapter initialization."""
        adapter = LocalFileStorageAdapter(temp_dir)
        
        assert adapter._base_temp_path == Path(temp_dir)
        assert adapter._base_temp_path.exists()
        assert adapter._base_temp_path.is_dir()
    
    def test_adapter_initialization_creates_directory(self, temp_dir):
        """Test adapter creates base directory if it doesn't exist."""
        nonexistent_dir = Path(temp_dir) / "nonexistent"
        assert not nonexistent_dir.exists()
        
        adapter = LocalFileStorageAdapter(str(nonexistent_dir))
        
        assert nonexistent_dir.exists()
        assert nonexistent_dir.is_dir()
    
    @pytest.mark.asyncio
    async def test_create_session_directory_success(self, storage_adapter):
        """Test successful session directory creation."""
        session_id = "test-session-123"
        
        result_path = await storage_adapter.create_session_directory(session_id)
        
        assert result_path.exists()
        assert result_path.is_dir()
        assert result_path.name == session_id
        assert result_path.parent == storage_adapter._base_temp_path
    
    @pytest.mark.asyncio
    async def test_create_session_directory_already_exists(self, storage_adapter):
        """Test creating directory that already exists."""
        session_id = "existing-session"
        
        # Create directory first
        await storage_adapter.create_session_directory(session_id)
        
        # Create again - should not fail
        result_path = await storage_adapter.create_session_directory(session_id)
        
        assert result_path.exists()
        assert result_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_store_chunk_success(self, storage_adapter):
        """Test successful chunk storage."""
        session_id = "chunk-test-session"
        await storage_adapter.create_session_directory(session_id)
        
        chunk_data = b"Hello, World! This is chunk data."
        chunk = FileChunk.create(0, chunk_data)
        
        await storage_adapter.store_chunk(session_id, chunk)
        
        # Verify chunk file was created
        session_dir = storage_adapter._base_temp_path / session_id
        chunk_file = session_dir / "chunk_000000.dat"
        
        assert chunk_file.exists()
        assert chunk_file.read_bytes() == chunk_data
    
    @pytest.mark.asyncio
    async def test_store_multiple_chunks(self, storage_adapter):
        """Test storing multiple chunks."""
        session_id = "multi-chunk-session"
        await storage_adapter.create_session_directory(session_id)
        
        chunks = [
            FileChunk.create(0, b"First chunk data"),
            FileChunk.create(1, b"Second chunk data"),
            FileChunk.create(2, b"Third chunk data")
        ]
        
        for chunk in chunks:
            await storage_adapter.store_chunk(session_id, chunk)
        
        # Verify all chunk files were created
        session_dir = storage_adapter._base_temp_path / session_id
        for i, chunk in enumerate(chunks):
            chunk_file = session_dir / f"chunk_{i:06d}.dat"
            assert chunk_file.exists()
            assert chunk_file.read_bytes() == chunk.data
    
    @pytest.mark.asyncio
    async def test_store_chunk_directory_not_exists(self, storage_adapter):
        """Test storing chunk when directory doesn't exist."""
        session_id = "nonexistent-session"
        chunk = FileChunk.create(0, b"test data")
        
        # Should create directory automatically
        await storage_adapter.store_chunk(session_id, chunk)
        
        session_dir = storage_adapter._base_temp_path / session_id
        chunk_file = session_dir / "chunk_000000.dat"
        
        assert session_dir.exists()
        assert chunk_file.exists()
    
    @pytest.mark.asyncio
    async def test_store_chunk_write_error(self, storage_adapter):
        """Test chunk storage with write error."""
        session_id = "error-session"
        chunk = FileChunk.create(0, b"test data")
        
        # Mock open to raise an exception
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with pytest.raises(IOError, match="Disk full"):
                await storage_adapter.store_chunk(session_id, chunk)
    
    @pytest.mark.asyncio
    async def test_assemble_file_success(self, storage_adapter, temp_dir):
        """Test successful file assembly."""
        # Setup session and chunks
        session = UploadSession(
            filename="test_file.mp3",
            total_chunks=3,
            total_size_bytes=45  # 15 bytes per chunk
        )
        
        await storage_adapter.create_session_directory(session.session_id)
        
        chunks = [
            FileChunk.create(0, b"First chunk!!!"),   # 15 bytes
            FileChunk.create(1, b"Second chunk!!"),   # 15 bytes  
            FileChunk.create(2, b"Third chunk!!!"),   # 15 bytes
        ]
        
        for chunk in chunks:
            await storage_adapter.store_chunk(session.session_id, chunk)
        
        # Assemble file
        output_path = Path(temp_dir) / "output" / "assembled_file.mp3"
        result_path = await storage_adapter.assemble_file(session, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size == 45
        
        # Verify content
        expected_content = b"First chunk!!!Second chunk!!Third chunk!!!"
        assert output_path.read_bytes() == expected_content
    
    @pytest.mark.asyncio
    async def test_assemble_file_missing_chunk(self, storage_adapter, temp_dir):
        """Test file assembly with missing chunk."""
        session = UploadSession(
            filename="incomplete_file.mp3",
            total_chunks=3,
            total_size_bytes=30
        )
        
        await storage_adapter.create_session_directory(session.session_id)
        
        # Store only 2 chunks
        chunks = [
            FileChunk.create(0, b"First chunk" + b"x" * 5),
            FileChunk.create(2, b"Third chunk" + b"x" * 5)  # Skip chunk 1
        ]
        
        for chunk in chunks:
            await storage_adapter.store_chunk(session.session_id, chunk)
        
        output_path = Path(temp_dir) / "incomplete.mp3"
        
        with pytest.raises(FileNotFoundError, match="Missing chunk file"):
            await storage_adapter.assemble_file(session, output_path)
        
        # Output file should not exist after failure
        assert not output_path.exists()
    
    @pytest.mark.asyncio
    async def test_assemble_file_size_mismatch(self, storage_adapter, temp_dir):
        """Test file assembly with size mismatch."""
        session = UploadSession(
            filename="size_mismatch.mp3",
            total_chunks=2,
            total_size_bytes=50  # Expected size
        )
        
        await storage_adapter.create_session_directory(session.session_id)
        
        # Store chunks with different total size
        chunks = [
            FileChunk.create(0, b"Short"),       # 5 bytes
            FileChunk.create(1, b"AlsoShort")    # 9 bytes, total 14 != 50
        ]
        
        for chunk in chunks:
            await storage_adapter.store_chunk(session.session_id, chunk)
        
        output_path = Path(temp_dir) / "size_mismatch.mp3"
        
        with pytest.raises(ValueError, match="does not match expected size"):
            await storage_adapter.assemble_file(session, output_path)
        
        # File should be cleaned up after error
        assert not output_path.exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_session_success(self, storage_adapter):
        """Test successful session cleanup."""
        session_id = "cleanup-test-session"
        
        # Create session directory with some files
        await storage_adapter.create_session_directory(session_id)
        chunk = FileChunk.create(0, b"test data")
        await storage_adapter.store_chunk(session_id, chunk)
        
        session_dir = storage_adapter._base_temp_path / session_id
        assert session_dir.exists()
        
        # Cleanup
        await storage_adapter.cleanup_session(session_id)
        
        assert not session_dir.exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_session_nonexistent(self, storage_adapter):
        """Test cleanup of nonexistent session."""
        # Should not fail when session doesn't exist
        await storage_adapter.cleanup_session("nonexistent-session")
    
    @pytest.mark.asyncio
    async def test_cleanup_session_error(self, storage_adapter):
        """Test cleanup with filesystem error."""
        session_id = "error-cleanup-session"
        await storage_adapter.create_session_directory(session_id)
        
        # Mock rmtree to raise an error
        with patch('shutil.rmtree', side_effect=OSError("Permission denied")):
            # Should not raise exception, just log warning
            await storage_adapter.cleanup_session(session_id)
    
    @pytest.mark.asyncio
    async def test_get_chunk_info_success(self, storage_adapter):
        """Test getting chunk information."""
        session_id = "chunk-info-session"
        await storage_adapter.create_session_directory(session_id)
        
        chunk = FileChunk.create(5, b"chunk info test data")
        await storage_adapter.store_chunk(session_id, chunk)
        
        info = await storage_adapter.get_chunk_info(session_id, 5)
        
        assert info is not None
        assert info["chunk_index"] == 5
        assert info["size_bytes"] == len(chunk.data)
        assert "modified_time" in info
        assert "file_path" in info
    
    @pytest.mark.asyncio
    async def test_get_chunk_info_not_found(self, storage_adapter):
        """Test getting info for nonexistent chunk."""
        session_id = "chunk-info-session"
        await storage_adapter.create_session_directory(session_id)
        
        info = await storage_adapter.get_chunk_info(session_id, 99)
        
        assert info is None
    
    @pytest.mark.asyncio
    async def test_get_chunk_info_error(self, storage_adapter):
        """Test getting chunk info with filesystem error."""
        session_id = "chunk-info-error-session"
        await storage_adapter.create_session_directory(session_id)
        
        # Create chunk file but mock stat to fail
        chunk = FileChunk.create(0, b"test")
        await storage_adapter.store_chunk(session_id, chunk)
        
        with patch('pathlib.Path.stat', side_effect=OSError("Access denied")):
            info = await storage_adapter.get_chunk_info(session_id, 0)
            assert info is None
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_success(self, storage_adapter, temp_dir):
        """Test successful file integrity verification."""
        test_file = Path(temp_dir) / "integrity_test.dat"
        test_data = b"Test file content for integrity check"
        test_file.write_bytes(test_data)
        
        result = await storage_adapter.verify_file_integrity(test_file, len(test_data))
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_file_not_exists(self, storage_adapter, temp_dir):
        """Test integrity verification for nonexistent file."""
        nonexistent_file = Path(temp_dir) / "nonexistent.dat"
        
        result = await storage_adapter.verify_file_integrity(nonexistent_file, 100)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_size_mismatch(self, storage_adapter, temp_dir):
        """Test integrity verification with size mismatch."""
        test_file = Path(temp_dir) / "size_test.dat"
        test_data = b"Short content"
        test_file.write_bytes(test_data)
        
        result = await storage_adapter.verify_file_integrity(test_file, 1000)  # Wrong size
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_error(self, storage_adapter, temp_dir):
        """Test integrity verification with filesystem error."""
        test_file = Path(temp_dir) / "error_test.dat"
        
        with patch('pathlib.Path.exists', side_effect=OSError("I/O error")):
            result = await storage_adapter.verify_file_integrity(test_file, 100)
            assert result is False


class TestMutagenMetadataExtractor:
    """Test MutagenMetadataExtractor protocol compliance and functionality."""
    
    @pytest.fixture
    def metadata_extractor(self):
        """Metadata extractor fixture."""
        return MutagenMetadataExtractor()
    
    @pytest.fixture
    def temp_audio_file(self):
        """Create temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            # Write some fake MP3 data
            f.write(b"ID3" + b"\x00" * 100 + b"fake mp3 data" * 50)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    def test_extractor_implements_protocol(self, metadata_extractor):
        """Test that extractor implements MetadataExtractionProtocol."""
        assert isinstance(metadata_extractor, MetadataExtractionProtocol)
    
    def test_extractor_initialization(self, metadata_extractor):
        """Test extractor initialization."""
        expected_formats = {'mp3', 'wav', 'flac', 'ogg', 'oga', 'm4a', 'aac', 'wma'}
        assert metadata_extractor._supported_formats == expected_formats
    
    def test_get_supported_formats(self, metadata_extractor):
        """Test getting supported formats."""
        formats = metadata_extractor.get_supported_formats()
        
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'mp3' in formats
        assert 'wav' in formats
        assert 'flac' in formats
        assert formats == sorted(formats)  # Should be sorted
    
    @pytest.mark.asyncio
    async def test_extract_metadata_basic_file_info(self, metadata_extractor, temp_audio_file):
        """Test extracting basic file metadata."""
        metadata = await metadata_extractor.extract_metadata(temp_audio_file)
        
        assert isinstance(metadata, FileMetadata)
        assert metadata.filename == temp_audio_file.name
        assert metadata.size_bytes > 0
        assert metadata.mime_type is not None
    
    @pytest.mark.asyncio
    @patch('mutagen.File')
    async def test_extract_metadata_with_mutagen_data(self, mock_mutagen_file, metadata_extractor, temp_audio_file):
        """Test metadata extraction with mocked Mutagen data."""
        # Mock Mutagen file object
        mock_audio = Mock()
        mock_audio.info.length = 180.5  # 3 minutes
        mock_audio.info.bitrate = 320
        mock_audio.info.sample_rate = 44100
        mock_audio.tags = {
            'TIT2': ['Test Song Title'],
            'TPE1': ['Test Artist'],
            'TALB': ['Test Album']
        }
        
        mock_mutagen_file.return_value = mock_audio
        
        metadata = await metadata_extractor.extract_metadata(temp_audio_file)
        
        assert metadata.title == "Test Song Title"
        assert metadata.artist == "Test Artist"
        assert metadata.album == "Test Album"
        assert metadata.duration_seconds == 180.5
        assert metadata.bitrate == 320
        assert metadata.sample_rate == 44100
    
    @pytest.mark.asyncio
    @patch('mutagen.File')
    async def test_extract_metadata_mutagen_returns_none(self, mock_mutagen_file, metadata_extractor, temp_audio_file):
        """Test metadata extraction when Mutagen returns None."""
        mock_mutagen_file.return_value = None
        
        metadata = await metadata_extractor.extract_metadata(temp_audio_file)
        
        # Should return basic metadata without audio info
        assert isinstance(metadata, FileMetadata)
        assert metadata.filename == temp_audio_file.name
        assert metadata.title is None
        assert metadata.artist is None
        assert metadata.duration_seconds is None
    
    @pytest.mark.asyncio
    @patch('mutagen.File')
    async def test_extract_metadata_mutagen_exception(self, mock_mutagen_file, metadata_extractor, temp_audio_file):
        """Test metadata extraction when Mutagen raises exception."""
        mock_mutagen_file.side_effect = Exception("Mutagen error")
        
        metadata = await metadata_extractor.extract_metadata(temp_audio_file)
        
        # Should return basic metadata despite error
        assert isinstance(metadata, FileMetadata)
        assert metadata.filename == temp_audio_file.name
    
    @pytest.mark.asyncio
    async def test_extract_metadata_file_error(self, metadata_extractor):
        """Test metadata extraction with file access error."""
        nonexistent_file = Path("/nonexistent/file.mp3")
        
        metadata = await metadata_extractor.extract_metadata(nonexistent_file)
        
        # Should return minimal metadata
        assert isinstance(metadata, FileMetadata)
        assert metadata.filename == "file.mp3"
        assert metadata.size_bytes == 0
        assert metadata.mime_type == "application/octet-stream"
    
    def test_get_tag_value_success(self, metadata_extractor):
        """Test successful tag value extraction."""
        mock_audio = Mock()
        mock_audio.tags = {
            'TIT2': ['Song Title'],
            'TITLE': ['Alternative Title']
        }
        
        # Should return first matching tag
        value = metadata_extractor._get_tag_value(mock_audio, ['TIT2', 'TITLE'])
        assert value == "Song Title"
        
        # Should try alternative if first not found
        value = metadata_extractor._get_tag_value(mock_audio, ['UNKNOWN', 'TITLE'])
        assert value == "Alternative Title"
    
    def test_get_tag_value_no_tags(self, metadata_extractor):
        """Test tag value extraction with no tags."""
        mock_audio = Mock()
        mock_audio.tags = None
        
        value = metadata_extractor._get_tag_value(mock_audio, ['TIT2'])
        assert value is None
    
    def test_get_tag_value_not_found(self, metadata_extractor):
        """Test tag value extraction when tag not found."""
        mock_audio = Mock()
        mock_audio.tags = {'OTHER': ['Other Value']}
        
        value = metadata_extractor._get_tag_value(mock_audio, ['TIT2', 'TITLE'])
        assert value is None
    
    def test_get_tag_value_non_list(self, metadata_extractor):
        """Test tag value extraction with non-list value."""
        mock_audio = Mock()
        mock_audio.tags = {'TIT2': 'Direct String Value'}
        
        value = metadata_extractor._get_tag_value(mock_audio, ['TIT2'])
        assert value == "Direct String Value"
    
    def test_extract_audio_metadata_complete(self, metadata_extractor):
        """Test audio metadata extraction with complete info."""
        base_metadata = FileMetadata.create_minimal("test.mp3", 1024, "audio/mpeg")
        
        mock_audio = Mock()
        mock_audio.info.length = 240.0
        mock_audio.info.bitrate = 192
        mock_audio.info.sample_rate = 44100
        mock_audio.tags = {
            'TIT2': ['Complete Song'],
            'TPE1': ['Complete Artist'],
            'TALB': ['Complete Album'],
            'EXTRA': ['Extra Info']
        }
        
        result = metadata_extractor._extract_audio_metadata(mock_audio, base_metadata)
        
        assert result.title == "Complete Song"
        assert result.artist == "Complete Artist"
        assert result.album == "Complete Album"
        assert result.duration_seconds == 240.0
        assert result.bitrate == 192
        assert result.sample_rate == 44100
        assert "EXTRA" in result.extra_attributes
        assert result.extra_attributes["EXTRA"] == "Extra Info"
    
    def test_extract_audio_metadata_minimal(self, metadata_extractor):
        """Test audio metadata extraction with minimal info."""
        base_metadata = FileMetadata.create_minimal("minimal.mp3", 512, "audio/mpeg")
        
        mock_audio = Mock()
        mock_audio.info = None  # No audio info
        mock_audio.tags = {}    # No tags
        
        result = metadata_extractor._extract_audio_metadata(mock_audio, base_metadata)
        
        assert result.title is None
        assert result.artist is None
        assert result.album is None
        assert result.duration_seconds is None
        assert result.bitrate is None
        assert result.sample_rate is None
        assert result.extra_attributes == {}
    
    @pytest.mark.asyncio
    @patch('mutagen.File')
    async def test_validate_audio_file_success(self, mock_mutagen_file, metadata_extractor, temp_audio_file):
        """Test successful audio file validation."""
        mock_audio = Mock()
        mock_audio.info.length = 120.0  # Valid duration
        mock_mutagen_file.return_value = mock_audio
        
        result = await metadata_extractor.validate_audio_file(temp_audio_file)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_audio_file_unsupported_extension(self, metadata_extractor):
        """Test audio file validation with unsupported extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            result = await metadata_extractor.validate_audio_file(temp_path)
            assert result is False
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    @patch('mutagen.File')
    async def test_validate_audio_file_mutagen_returns_none(self, mock_mutagen_file, metadata_extractor, temp_audio_file):
        """Test validation when Mutagen returns None."""
        mock_mutagen_file.return_value = None
        
        result = await metadata_extractor.validate_audio_file(temp_audio_file)
        assert result is False
    
    @pytest.mark.asyncio
    @patch('mutagen.File')
    async def test_validate_audio_file_no_duration(self, mock_mutagen_file, metadata_extractor, temp_audio_file):
        """Test validation with zero duration."""
        mock_audio = Mock()
        mock_audio.info.length = 0  # No duration
        mock_mutagen_file.return_value = mock_audio
        
        result = await metadata_extractor.validate_audio_file(temp_audio_file)
        assert result is False
    
    @pytest.mark.asyncio
    @patch('mutagen.File')
    async def test_validate_audio_file_exception(self, mock_mutagen_file, metadata_extractor, temp_audio_file):
        """Test validation when Mutagen raises exception."""
        mock_mutagen_file.side_effect = Exception("Validation error")
        
        result = await metadata_extractor.validate_audio_file(temp_audio_file)
        assert result is False


class TestMockMetadataExtractor:
    """Test MockMetadataExtractor implementation."""
    
    @pytest.fixture
    def mock_extractor(self):
        """Mock metadata extractor fixture."""
        return MockMetadataExtractor()
    
    def test_mock_extractor_implements_protocol(self, mock_extractor):
        """Test that mock extractor implements MetadataExtractionProtocol."""
        assert isinstance(mock_extractor, MetadataExtractionProtocol)
    
    def test_mock_extractor_initialization(self, mock_extractor):
        """Test mock extractor initialization."""
        assert mock_extractor._supported_formats == ['mp3', 'wav', 'flac']
    
    @pytest.mark.asyncio
    async def test_mock_extract_metadata_with_file(self, mock_extractor):
        """Test mock metadata extraction with existing file."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b"test data" * 100)
            temp_path = Path(f.name)
        
        try:
            metadata = await mock_extractor.extract_metadata(temp_path)
            
            assert metadata.filename == temp_path.name
            assert metadata.size_bytes == 900  # 9 bytes * 100
            assert metadata.mime_type == "audio/mpeg"
            assert metadata.title == f"Mock Title for {temp_path.stem}"
            assert metadata.artist == "Mock Artist"
            assert metadata.album == "Mock Album"
            assert metadata.duration_seconds == 180.0
            assert metadata.bitrate == 192
            assert metadata.sample_rate == 44100
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_mock_extract_metadata_nonexistent_file(self, mock_extractor):
        """Test mock metadata extraction with nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.mp3")
        
        metadata = await mock_extractor.extract_metadata(nonexistent_path)
        
        assert metadata.filename == "file.mp3"
        assert metadata.size_bytes == 1024  # Mock size
        assert metadata.title == "Mock Title for file"
    
    def test_mock_get_supported_formats(self, mock_extractor):
        """Test mock supported formats."""
        formats = mock_extractor.get_supported_formats()
        
        assert formats == ['mp3', 'wav', 'flac']
        assert isinstance(formats, list)
        assert formats is not mock_extractor._supported_formats  # Should be copy
    
    @pytest.mark.asyncio
    async def test_mock_validate_audio_file_supported(self, mock_extractor):
        """Test mock validation for supported format."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            result = await mock_extractor.validate_audio_file(temp_path)
            assert result is True
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_mock_validate_audio_file_unsupported(self, mock_extractor):
        """Test mock validation for unsupported format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            result = await mock_extractor.validate_audio_file(temp_path)
            assert result is False
        finally:
            temp_path.unlink()


class TestInfrastructureProtocolCompliance:
    """Test infrastructure adapters meet all protocol requirements."""
    
    def test_file_storage_protocol_methods(self):
        """Test FileStorageProtocol method compliance."""
        storage = LocalFileStorageAdapter("test")
        
        required_methods = [
            'create_session_directory', 'store_chunk', 'assemble_file',
            'cleanup_session', 'get_chunk_info', 'verify_file_integrity'
        ]
        
        for method_name in required_methods:
            assert hasattr(storage, method_name)
            assert callable(getattr(storage, method_name))
    
    def test_metadata_extraction_protocol_methods(self):
        """Test MetadataExtractionProtocol method compliance."""
        extractor = MutagenMetadataExtractor()
        
        required_methods = [
            'extract_metadata', 'get_supported_formats', 'validate_audio_file'
        ]
        
        for method_name in required_methods:
            assert hasattr(extractor, method_name)
            assert callable(getattr(extractor, method_name))
    
    @pytest.mark.asyncio
    async def test_adapters_integration(self):
        """Test adapters working together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalFileStorageAdapter(temp_dir)
            extractor = MockMetadataExtractor()
            
            # Create session and store chunks
            session = UploadSession(
                filename="integration_test.mp3",
                total_chunks=2,
                total_size_bytes=20
            )
            
            await storage.create_session_directory(session.session_id)
            
            chunk1 = FileChunk.create(0, b"first_chunk!!")   # 12 bytes
            chunk2 = FileChunk.create(1, b"second!!")        # 8 bytes, total 20
            
            await storage.store_chunk(session.session_id, chunk1)
            await storage.store_chunk(session.session_id, chunk2)
            
            # Assemble file
            output_path = Path(temp_dir) / "final" / "integrated.mp3"
            assembled_path = await storage.assemble_file(session, output_path)
            
            # Extract metadata
            metadata = await extractor.extract_metadata(assembled_path)
            
            # Verify integration
            assert assembled_path.exists()
            assert metadata.filename == "integrated.mp3"
            assert metadata.size_bytes == 20
            assert await extractor.validate_audio_file(assembled_path)
            
            # Cleanup
            await storage.cleanup_session(session.session_id)