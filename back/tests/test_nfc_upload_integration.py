# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive integration tests for NFC and Upload DDD modules.

Tests cover:
- End-to-end NFC tag association workflows
- End-to-end file upload workflows
- Cross-module interactions
- Real-world scenarios
- Error resilience and recovery
- Performance under load
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone, timedelta

# NFC Module Imports
from app.src.application.services.nfc_application_service import NfcApplicationService
from app.src.domain.nfc.services.nfc_association_service import NfcAssociationService
from app.src.infrastructure.nfc.adapters.nfc_hardware_adapter import MockNfcHardwareAdapter
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.entities.nfc_tag import NfcTag

# Upload Module Imports
from app.src.application.services.upload_application_service import UploadApplicationService
from app.src.domain.upload.services.upload_validation_service import UploadValidationService
from app.src.infrastructure.upload.adapters.file_storage_adapter import LocalFileStorageAdapter
from app.src.infrastructure.upload.adapters.metadata_extractor import MockMetadataExtractor
from app.src.domain.upload.value_objects.file_chunk import FileChunk
from app.src.domain.upload.entities.upload_session import UploadStatus

# Repository Mocks
from tests.test_nfc_domain import MockNfcRepository


class TestNfcSystemIntegration:
    """Integration tests for complete NFC system workflows."""
    
    @pytest.fixture
    def mock_hardware(self):
        """Mock NFC hardware fixture."""
        return MockNfcHardwareAdapter()
    
    @pytest.fixture
    def mock_repository(self):
        """Mock NFC repository fixture."""
        return MockNfcRepository()
    
    @pytest.fixture
    def nfc_app_service(self, mock_hardware, mock_repository):
        """Complete NFC application service fixture."""
        return NfcApplicationService(
            nfc_hardware=mock_hardware,
            nfc_repository=mock_repository
        )
    
    @pytest.mark.asyncio
    async def test_complete_nfc_association_workflow(self, nfc_app_service, mock_hardware):
        """Test complete NFC tag association workflow from start to finish."""
        # Step 1: Start NFC system
        start_result = await nfc_app_service.start_nfc_system()
        assert start_result["status"] == "success"
        
        # Step 2: Start association session
        playlist_id = "integration-playlist-123"
        association_result = await nfc_app_service.start_association_use_case(playlist_id)
        assert association_result["status"] == "success"
        session_id = association_result["session"]["session_id"]
        
        # Step 3: Simulate tag detection
        test_tag_uid = "1234567890abcdef"
        mock_hardware.simulate_tag_detection(test_tag_uid)
        
        # Give async processing time
        await asyncio.sleep(0.1)
        
        # Step 4: Verify association was successful
        status_result = await nfc_app_service.get_nfc_status_use_case()
        assert status_result["status"] == "success"
        
        # Find the completed session
        session_found = False
        for session in status_result["active_sessions"]:
            if session["session_id"] == session_id:
                if session["state"] == "successful":
                    session_found = True
                    break
        
        # If session is no longer active, it completed successfully
        assert session_found or len(status_result["active_sessions"]) == 0
        
        # Step 5: Verify tag is in repository
        tag_identifier = TagIdentifier(uid=test_tag_uid)
        stored_tag = await nfc_app_service._nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None
        assert stored_tag.is_associated()
        assert stored_tag.get_associated_playlist_id() == playlist_id
        
        # Step 6: Stop NFC system
        stop_result = await nfc_app_service.stop_nfc_system()
        assert stop_result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_nfc_duplicate_tag_handling(self, nfc_app_service, mock_hardware, mock_repository):
        """Test handling of duplicate tag associations."""
        # Pre-populate repository with associated tag
        existing_tag_uid = "existing1234abcd"
        existing_tag = NfcTag(identifier=TagIdentifier(uid=existing_tag_uid))
        existing_tag.associate_with_playlist("existing-playlist")
        await mock_repository.save_tag(existing_tag)
        
        await nfc_app_service.start_nfc_system()
        
        # Start association for different playlist
        new_playlist_id = "new-playlist-456"
        await nfc_app_service.start_association_use_case(new_playlist_id)
        
        # Setup callback to capture association events
        association_events = []
        nfc_app_service.register_association_callback(lambda event: association_events.append(event))
        
        # Simulate detection of already-associated tag
        mock_hardware.simulate_tag_detection(existing_tag_uid)
        await asyncio.sleep(0.1)
        
        # Should detect duplicate association
        assert len(association_events) > 0
        event = association_events[0]
        assert event["action"] == "duplicate_association"
        assert event["existing_playlist_id"] == "existing-playlist"
        assert event["playlist_id"] == new_playlist_id
        
        # Original association should remain unchanged
        stored_tag = await mock_repository.find_by_identifier(TagIdentifier(uid=existing_tag_uid))
        assert stored_tag.get_associated_playlist_id() == "existing-playlist"
        
        await nfc_app_service.stop_nfc_system()
    
    @pytest.mark.asyncio
    async def test_nfc_session_timeout_integration(self, nfc_app_service):
        """Test complete session timeout handling."""
        await nfc_app_service.start_nfc_system()
        
        # Start session with very short timeout
        result = await nfc_app_service.start_association_use_case("timeout-test", timeout_seconds=1)
        session_id = result["session"]["session_id"]
        
        # Wait for timeout
        await asyncio.sleep(2)
        
        # Manually trigger cleanup
        cleaned = await nfc_app_service._association_service.cleanup_expired_sessions()
        assert cleaned == 1
        
        # Session should no longer be active
        status = await nfc_app_service.get_nfc_status_use_case()
        assert status["session_count"] == 0
        
        await nfc_app_service.stop_nfc_system()
    
    @pytest.mark.asyncio
    async def test_nfc_concurrent_sessions_integration(self, nfc_app_service, mock_hardware):
        """Test handling multiple concurrent association sessions."""
        await nfc_app_service.start_nfc_system()
        
        # Start multiple sessions for different playlists
        playlists = ["concurrent-1", "concurrent-2", "concurrent-3"]
        sessions = []
        
        for playlist_id in playlists:
            result = await nfc_app_service.start_association_use_case(playlist_id)
            assert result["status"] == "success"
            sessions.append(result["session"])
        
        # Verify all sessions are active
        status = await nfc_app_service.get_nfc_status_use_case()
        assert status["session_count"] == 3
        
        # Test tag detection affects first matching session
        test_tags = ["tag001122", "tag334455", "tag667788"]
        for i, tag_uid in enumerate(test_tags):
            mock_hardware.simulate_tag_detection(tag_uid)
            await asyncio.sleep(0.1)
        
        await nfc_app_service.stop_nfc_system()


class TestUploadSystemIntegration:
    """Integration tests for complete upload system workflows."""
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Temporary upload directory fixture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def upload_app_service(self, temp_upload_dir):
        """Complete upload application service fixture."""
        storage = LocalFileStorageAdapter(temp_upload_dir)
        metadata_extractor = MockMetadataExtractor()
        validation_service = UploadValidationService()
        
        return UploadApplicationService(
            file_storage=storage,
            metadata_extractor=metadata_extractor,
            validation_service=validation_service,
            upload_folder=temp_upload_dir
        )
    
    @pytest.mark.asyncio
    async def test_complete_file_upload_workflow(self, upload_app_service, temp_upload_dir):
        """Test complete file upload workflow from start to finish."""
        # Step 1: Start upload service
        start_result = await upload_app_service.start_upload_service()
        assert start_result["status"] == "success"
        
        # Step 2: Create upload session
        filename = "integration_test.mp3"
        total_size = 300
        total_chunks = 3
        playlist_id = "upload-integration-playlist"
        
        session_result = await upload_app_service.create_upload_session_use_case(
            filename=filename,
            total_size=total_size,
            total_chunks=total_chunks,
            playlist_id=playlist_id
        )
        assert session_result["status"] == "success"
        session_id = session_result["session"]["session_id"]
        
        # Step 3: Upload chunks
        chunks_data = [
            b"First chunk data!!!",    # 20 bytes
            b"Second chunk data!!",    # 19 bytes
            b"Third chunk data!!!!"    # 21 bytes (total 60, but we'll pad to 300)
        ]
        
        # Pad to match expected total size
        chunks_data = [
            b"x" * 100,  # 100 bytes
            b"y" * 100,  # 100 bytes
            b"z" * 100   # 100 bytes (total 300)
        ]
        
        for i, chunk_data in enumerate(chunks_data):
            chunk_result = await upload_app_service.upload_chunk_use_case(
                session_id, i, chunk_data
            )
            assert chunk_result["status"] == "success"
        
        # Step 4: Verify completion
        final_result = chunk_result  # Last chunk upload should complete session
        assert final_result["completion_status"] == "success"
        assert "file_path" in final_result
        assert "metadata" in final_result
        
        # Step 5: Verify file was created
        expected_file_path = Path(temp_upload_dir) / playlist_id / filename
        assert expected_file_path.exists()
        assert expected_file_path.stat().st_size == total_size
        
        # Step 6: Verify metadata was extracted
        metadata = final_result["metadata"]
        assert metadata["filename"] == filename
        assert metadata["size_bytes"] == total_size
        assert metadata["title"] is not None
        assert metadata["artist"] is not None
    
    @pytest.mark.asyncio
    async def test_upload_error_recovery_workflow(self, upload_app_service):
        """Test upload error recovery and resilience."""
        await upload_app_service.start_upload_service()
        
        # Create session
        session_result = await upload_app_service.create_upload_session_use_case(
            filename="error_recovery_test.mp3",
            total_size=200,
            total_chunks=2,
            playlist_id="error-test"
        )
        session_id = session_result["session"]["session_id"]
        
        # Upload first chunk successfully
        chunk1_result = await upload_app_service.upload_chunk_use_case(
            session_id, 0, b"x" * 100
        )
        assert chunk1_result["status"] == "success"
        
        # Try to upload invalid chunk (duplicate)
        duplicate_result = await upload_app_service.upload_chunk_use_case(
            session_id, 0, b"y" * 100
        )
        assert duplicate_result["status"] == "error"
        assert duplicate_result["error_type"] == "validation_error"
        
        # Upload second chunk successfully
        chunk2_result = await upload_app_service.upload_chunk_use_case(
            session_id, 1, b"z" * 100
        )
        assert chunk2_result["status"] == "success"
        assert chunk2_result["completion_status"] == "success"
        
        # Session should be completed despite error
        status_result = await upload_app_service.get_upload_status_use_case(session_id)
        assert status_result["session"]["status"] == UploadStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_upload_cancellation_workflow(self, upload_app_service):
        """Test upload cancellation workflow."""
        await upload_app_service.start_upload_service()
        
        # Create session
        session_result = await upload_app_service.create_upload_session_use_case(
            filename="cancellation_test.mp3",
            total_size=300,
            total_chunks=3
        )
        session_id = session_result["session"]["session_id"]
        
        # Upload partial chunks
        await upload_app_service.upload_chunk_use_case(session_id, 0, b"x" * 100)
        
        # Cancel upload
        cancel_result = await upload_app_service.cancel_upload_use_case(session_id)
        assert cancel_result["status"] == "success"
        
        # Verify session is cancelled
        status_result = await upload_app_service.get_upload_status_use_case(session_id)
        assert status_result["session"]["status"] == UploadStatus.CANCELLED.value
        
        # Try to upload to cancelled session (should fail)
        failed_result = await upload_app_service.upload_chunk_use_case(
            session_id, 1, b"y" * 100
        )
        assert failed_result["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_upload_concurrent_sessions(self, upload_app_service):
        """Test handling multiple concurrent upload sessions."""
        await upload_app_service.start_upload_service()
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            result = await upload_app_service.create_upload_session_use_case(
                filename=f"concurrent_{i}.mp3",
                total_size=100,
                total_chunks=1,
                playlist_id=f"concurrent-playlist-{i}"
            )
            assert result["status"] == "success"
            sessions.append(result["session"])
        
        # Upload chunks to all sessions concurrently
        upload_tasks = [
            upload_app_service.upload_chunk_use_case(
                session["session_id"], 0, f"data{i}".encode() + b"x" * 96
            )
            for i, session in enumerate(sessions)
        ]
        
        results = await asyncio.gather(*upload_tasks)
        
        # All should succeed
        for result in results:
            assert result["status"] == "success"
            assert result["completion_status"] == "success"
        
        # List active uploads should show none (all completed)
        active_result = await upload_app_service.list_active_uploads_use_case()
        assert active_result["count"] == 0


class TestCrossModuleIntegration:
    """Integration tests for NFC and Upload modules working together."""
    
    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for integration tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def integrated_services(self, temp_dir):
        """Both NFC and Upload services configured together."""
        # NFC Service
        nfc_hardware = MockNfcHardwareAdapter()
        nfc_repository = MockNfcRepository()
        nfc_service = NfcApplicationService(nfc_hardware, nfc_repository)
        
        # Upload Service
        storage = LocalFileStorageAdapter(temp_dir)
        metadata_extractor = MockMetadataExtractor()
        upload_service = UploadApplicationService(
            storage, metadata_extractor, upload_folder=temp_dir
        )
        
        return {
            "nfc": nfc_service,
            "upload": upload_service,
            "nfc_hardware": nfc_hardware,
            "nfc_repository": nfc_repository,
            "temp_dir": temp_dir
        }
    
    @pytest.mark.asyncio
    async def test_nfc_triggered_upload_workflow(self, integrated_services):
        """Test workflow where NFC tag detection triggers upload process."""
        nfc_service = integrated_services["nfc"]
        upload_service = integrated_services["upload"]
        nfc_hardware = integrated_services["nfc_hardware"]
        
        # Start both services
        await nfc_service.start_nfc_system()
        await upload_service.start_upload_service()
        
        # Create a playlist identifier
        playlist_id = "nfc-upload-integration"
        
        # Step 1: Upload a file for the playlist
        session_result = await upload_service.create_upload_session_use_case(
            filename="nfc_triggered_upload.mp3",
            total_size=150,
            total_chunks=1,
            playlist_id=playlist_id
        )
        session_id = session_result["session"]["session_id"]
        
        # Complete the upload
        upload_result = await upload_service.upload_chunk_use_case(
            session_id, 0, b"x" * 150
        )
        assert upload_result["completion_status"] == "success"
        
        # Step 2: Associate NFC tag with the same playlist
        association_result = await nfc_service.start_association_use_case(playlist_id)
        assert association_result["status"] == "success"
        
        # Simulate tag detection
        test_tag_uid = "nfc-upload-integration-tag"
        nfc_hardware.simulate_tag_detection(test_tag_uid)
        await asyncio.sleep(0.1)
        
        # Step 3: Verify both systems are aware of the playlist
        # Check NFC tag is associated
        tag_identifier = TagIdentifier(uid=test_tag_uid)
        stored_tag = await integrated_services["nfc_repository"].find_by_identifier(tag_identifier)
        assert stored_tag.get_associated_playlist_id() == playlist_id
        
        # Check upload file exists
        expected_file = Path(integrated_services["temp_dir"]) / playlist_id / "nfc_triggered_upload.mp3"
        assert expected_file.exists()
        
        await nfc_service.stop_nfc_system()
    
    @pytest.mark.asyncio
    async def test_upload_metadata_for_nfc_playlist(self, integrated_services):
        """Test uploading files with metadata that will be used by NFC system."""
        nfc_service = integrated_services["nfc"]
        upload_service = integrated_services["upload"]
        
        await nfc_service.start_nfc_system()
        await upload_service.start_upload_service()
        
        playlist_id = "metadata-integration-playlist"
        
        # Upload multiple files to create a playlist
        files_to_upload = [
            ("song1.mp3", b"Song 1 data " * 10),
            ("song2.mp3", b"Song 2 data " * 12),
            ("song3.mp3", b"Song 3 data " * 8)
        ]
        
        uploaded_files = []
        
        for filename, data in files_to_upload:
            # Create and complete upload
            session_result = await upload_service.create_upload_session_use_case(
                filename=filename,
                total_size=len(data),
                total_chunks=1,
                playlist_id=playlist_id
            )
            
            upload_result = await upload_service.upload_chunk_use_case(
                session_result["session"]["session_id"], 0, data
            )
            
            assert upload_result["completion_status"] == "success"
            uploaded_files.append(upload_result)
        
        # Associate NFC tag with this playlist
        association_result = await nfc_service.start_association_use_case(playlist_id)
        test_tag_uid = "metadata-playlist-tag"
        integrated_services["nfc_hardware"].simulate_tag_detection(test_tag_uid)
        await asyncio.sleep(0.1)
        
        # Verify integration
        assert len(uploaded_files) == 3
        for file_result in uploaded_files:
            metadata = file_result["metadata"]
            assert metadata["title"] is not None
            assert metadata["artist"] == "Mock Artist"  # From MockMetadataExtractor
        
        # Verify NFC tag is associated with playlist containing these files
        tag_identifier = TagIdentifier(uid=test_tag_uid)
        stored_tag = await integrated_services["nfc_repository"].find_by_identifier(tag_identifier)
        assert stored_tag.get_associated_playlist_id() == playlist_id
        
        await nfc_service.stop_nfc_system()
    
    @pytest.mark.asyncio
    async def test_system_resilience_integration(self, integrated_services):
        """Test system resilience when both modules encounter errors."""
        nfc_service = integrated_services["nfc"]
        upload_service = integrated_services["upload"]
        nfc_hardware = integrated_services["nfc_hardware"]
        
        await nfc_service.start_nfc_system()
        await upload_service.start_upload_service()
        
        playlist_id = "resilience-test-playlist"
        
        # Test 1: Upload failure doesn't affect NFC
        failed_session_result = await upload_service.create_upload_session_use_case(
            filename="", # Invalid filename should fail
            total_size=100,
            total_chunks=1,
            playlist_id=playlist_id
        )
        assert failed_session_result["status"] == "error"
        
        # NFC should still work
        nfc_result = await nfc_service.start_association_use_case(playlist_id)
        assert nfc_result["status"] == "success"
        
        # Test 2: NFC error doesn't affect uploads
        # Simulate hardware error in NFC
        original_callback = nfc_hardware._tag_detected_callback
        nfc_hardware._tag_detected_callback = Mock(side_effect=Exception("Hardware error"))
        
        # Upload should still work
        upload_session_result = await upload_service.create_upload_session_use_case(
            filename="resilience_test.mp3",
            total_size=100,
            total_chunks=1,
            playlist_id=playlist_id
        )
        assert upload_session_result["status"] == "success"
        
        # Restore callback
        nfc_hardware._tag_detected_callback = original_callback
        
        await nfc_service.stop_nfc_system()


class TestPerformanceIntegration:
    """Performance and load integration tests."""
    
    @pytest.fixture
    def performance_services(self):
        """Services configured for performance testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nfc_hardware = MockNfcHardwareAdapter()
            nfc_repository = MockNfcRepository()
            nfc_service = NfcApplicationService(nfc_hardware, nfc_repository)
            
            storage = LocalFileStorageAdapter(temp_dir)
            metadata_extractor = MockMetadataExtractor()
            upload_service = UploadApplicationService(storage, metadata_extractor)
            
            yield {
                "nfc": nfc_service,
                "upload": upload_service,
                "nfc_hardware": nfc_hardware
            }
    
    @pytest.mark.asyncio
    async def test_concurrent_nfc_and_upload_operations(self, performance_services):
        """Test concurrent NFC and upload operations."""
        nfc_service = performance_services["nfc"]
        upload_service = performance_services["upload"]
        nfc_hardware = performance_services["nfc_hardware"]
        
        await nfc_service.start_nfc_system()
        await upload_service.start_upload_service()
        
        # Create concurrent operations
        async def nfc_operations():
            """Perform multiple NFC operations."""
            operations = []
            for i in range(5):
                playlist_id = f"perf-nfc-{i}"
                operations.append(nfc_service.start_association_use_case(playlist_id))
            
            results = await asyncio.gather(*operations)
            
            # Simulate tag detections
            for i in range(5):
                nfc_hardware.simulate_tag_detection(f"perf-tag-{i}")
                await asyncio.sleep(0.01)  # Small delay between detections
            
            return results
        
        async def upload_operations():
            """Perform multiple upload operations."""
            operations = []
            for i in range(5):
                operations.append(
                    upload_service.create_upload_session_use_case(
                        filename=f"perf_test_{i}.mp3",
                        total_size=100,
                        total_chunks=1,
                        playlist_id=f"perf-upload-{i}"
                    )
                )
            
            session_results = await asyncio.gather(*operations)
            
            # Upload chunks
            upload_ops = []
            for result in session_results:
                if result["status"] == "success":
                    session_id = result["session"]["session_id"]
                    upload_ops.append(
                        upload_service.upload_chunk_use_case(
                            session_id, 0, b"x" * 100
                        )
                    )
            
            return await asyncio.gather(*upload_ops)
        
        # Run both operation types concurrently
        nfc_results, upload_results = await asyncio.gather(
            nfc_operations(),
            upload_operations()
        )
        
        # Verify all operations succeeded
        for result in nfc_results:
            assert result["status"] == "success"
        
        for result in upload_results:
            assert result["status"] == "success"
            assert result.get("completion_status") == "success"
        
        await nfc_service.stop_nfc_system()
    
    @pytest.mark.asyncio 
    async def test_memory_efficiency_with_large_operations(self, performance_services):
        """Test memory efficiency with larger operations."""
        upload_service = performance_services["upload"]
        await upload_service.start_upload_service()
        
        # Test larger file uploads
        large_file_size = 10 * 1024  # 10KB chunks
        session_result = await upload_service.create_upload_session_use_case(
            filename="large_test.mp3",
            total_size=large_file_size,
            total_chunks=1,
            playlist_id="large-test"
        )
        
        assert session_result["status"] == "success"
        session_id = session_result["session"]["session_id"]
        
        # Upload large chunk
        large_data = b"x" * large_file_size
        upload_result = await upload_service.upload_chunk_use_case(
            session_id, 0, large_data
        )
        
        assert upload_result["status"] == "success"
        assert upload_result["completion_status"] == "success"
        
        # Verify memory was released by checking we can do it again
        session_result2 = await upload_service.create_upload_session_use_case(
            filename="large_test_2.mp3",
            total_size=large_file_size,
            total_chunks=1,
            playlist_id="large-test-2"
        )
        
        assert session_result2["status"] == "success"


class TestRealWorldScenarios:
    """Integration tests simulating real-world usage scenarios."""
    
    @pytest.fixture
    def real_world_services(self):
        """Services configured for real-world simulation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure services with realistic settings
            nfc_hardware = MockNfcHardwareAdapter()
            nfc_repository = MockNfcRepository()
            nfc_service = NfcApplicationService(nfc_hardware, nfc_repository)
            
            storage = LocalFileStorageAdapter(temp_dir)
            metadata_extractor = MockMetadataExtractor()
            validation_service = UploadValidationService(
                max_file_size=50 * 1024 * 1024,  # 50MB
                allowed_extensions={"mp3", "wav", "flac"}
            )
            upload_service = UploadApplicationService(
                storage, metadata_extractor, validation_service, temp_dir
            )
            
            yield {
                "nfc": nfc_service,
                "upload": upload_service,
                "nfc_hardware": nfc_hardware,
                "nfc_repository": nfc_repository,
                "temp_dir": temp_dir
            }
    
    @pytest.mark.asyncio
    async def test_music_library_creation_scenario(self, real_world_services):
        """Test realistic music library creation scenario."""
        nfc_service = real_world_services["nfc"]
        upload_service = real_world_services["upload"]
        nfc_hardware = real_world_services["nfc_hardware"]
        
        await nfc_service.start_nfc_system()
        await upload_service.start_upload_service()
        
        # Scenario: User creates multiple playlists with NFC tags
        playlists = [
            {"name": "Rock Classics", "tag": "rock123456"},
            {"name": "Jazz Standards", "tag": "jazz789abc"},
            {"name": "Electronic Beats", "tag": "electdef012"}
        ]
        
        # Create playlists by uploading songs and associating tags
        for playlist in playlists:
            playlist_id = playlist["name"].lower().replace(" ", "-")
            
            # Upload some songs to the playlist
            songs = [
                f"{playlist['name']}_song1.mp3",
                f"{playlist['name']}_song2.mp3"
            ]
            
            for song in songs:
                session_result = await upload_service.create_upload_session_use_case(
                    filename=song,
                    total_size=500,  # Simulated song size
                    total_chunks=5,
                    playlist_id=playlist_id
                )
                
                assert session_result["status"] == "success"
                session_id = session_result["session"]["session_id"]
                
                # Upload chunks
                for chunk_idx in range(5):
                    chunk_data = f"chunk{chunk_idx}".encode() + b"x" * 95
                    await upload_service.upload_chunk_use_case(
                        session_id, chunk_idx, chunk_data
                    )
            
            # Associate NFC tag with playlist
            association_result = await nfc_service.start_association_use_case(playlist_id)
            assert association_result["status"] == "success"
            
            nfc_hardware.simulate_tag_detection(playlist["tag"])
            await asyncio.sleep(0.1)
        
        # Verify all playlists were created
        for playlist in playlists:
            playlist_id = playlist["name"].lower().replace(" ", "-")
            playlist_dir = Path(real_world_services["temp_dir"]) / playlist_id
            assert playlist_dir.exists()
            
            # Should have 2 songs
            songs = list(playlist_dir.glob("*.mp3"))
            assert len(songs) == 2
            
            # NFC tag should be associated
            tag_identifier = TagIdentifier(uid=playlist["tag"])
            stored_tag = await real_world_services["nfc_repository"].find_by_identifier(tag_identifier)
            assert stored_tag.get_associated_playlist_id() == playlist_id
        
        await nfc_service.stop_nfc_system()
    
    @pytest.mark.asyncio
    async def test_user_error_recovery_scenario(self, real_world_services):
        """Test realistic user error recovery scenarios."""
        nfc_service = real_world_services["nfc"]
        upload_service = real_world_services["upload"]
        nfc_hardware = real_world_services["nfc_hardware"]
        
        await nfc_service.start_nfc_system()
        await upload_service.start_upload_service()
        
        # Scenario 1: User accidentally cancels upload and restarts
        session_result = await upload_service.create_upload_session_use_case(
            filename="accidentally_cancelled.mp3",
            total_size=200,
            total_chunks=2,
            playlist_id="user-errors"
        )
        session_id = session_result["session"]["session_id"]
        
        # Upload one chunk
        await upload_service.upload_chunk_use_case(session_id, 0, b"x" * 100)
        
        # User cancels
        await upload_service.cancel_upload_use_case(session_id)
        
        # User restarts with same file
        new_session_result = await upload_service.create_upload_session_use_case(
            filename="accidentally_cancelled.mp3",
            total_size=200,
            total_chunks=2,
            playlist_id="user-errors"
        )
        
        assert new_session_result["status"] == "success"
        new_session_id = new_session_result["session"]["session_id"]
        
        # Complete the upload this time
        await upload_service.upload_chunk_use_case(new_session_id, 0, b"x" * 100)
        final_result = await upload_service.upload_chunk_use_case(new_session_id, 1, b"y" * 100)
        
        assert final_result["completion_status"] == "success"
        
        # Scenario 2: User tries to associate already-associated tag
        await nfc_service.start_association_use_case("first-playlist")
        nfc_hardware.simulate_tag_detection("shared-tag-123")
        await asyncio.sleep(0.1)
        
        # Try to associate same tag with different playlist
        await nfc_service.start_association_use_case("second-playlist")
        nfc_hardware.simulate_tag_detection("shared-tag-123")
        await asyncio.sleep(0.1)
        
        # Tag should still be associated with first playlist
        tag_identifier = TagIdentifier(uid="shared-tag-123")
        stored_tag = await real_world_services["nfc_repository"].find_by_identifier(tag_identifier)
        assert stored_tag.get_associated_playlist_id() == "first-playlist"
        
        await nfc_service.stop_nfc_system()
    
    @pytest.mark.asyncio
    async def test_system_shutdown_and_restart_scenario(self, real_world_services):
        """Test system shutdown and restart with state preservation."""
        nfc_service = real_world_services["nfc"]
        upload_service = real_world_services["upload"]
        nfc_hardware = real_world_services["nfc_hardware"]
        nfc_repository = real_world_services["nfc_repository"]
        
        # Initial system startup
        await nfc_service.start_nfc_system()
        await upload_service.start_upload_service()
        
        # Create some data
        playlist_id = "persistent-playlist"
        
        # Upload a file
        session_result = await upload_service.create_upload_session_use_case(
            filename="persistent_song.mp3",
            total_size=100,
            total_chunks=1,
            playlist_id=playlist_id
        )
        
        upload_result = await upload_service.upload_chunk_use_case(
            session_result["session"]["session_id"], 0, b"x" * 100
        )
        assert upload_result["completion_status"] == "success"
        
        # Associate NFC tag
        await nfc_service.start_association_use_case(playlist_id)
        nfc_hardware.simulate_tag_detection("persistent-tag-456")
        await asyncio.sleep(0.1)
        
        # Verify initial state
        tag_identifier = TagIdentifier(uid="persistent-tag-456")
        stored_tag = await nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag.get_associated_playlist_id() == playlist_id
        
        # Shutdown system
        await nfc_service.stop_nfc_system()
        
        # Restart system (repository should maintain state)
        new_nfc_service = NfcApplicationService(nfc_hardware, nfc_repository)
        await new_nfc_service.start_nfc_system()
        
        # Verify state is preserved
        stored_tag_after_restart = await nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag_after_restart.get_associated_playlist_id() == playlist_id
        
        # Verify uploaded file still exists
        expected_file = Path(real_world_services["temp_dir"]) / playlist_id / "persistent_song.mp3"
        assert expected_file.exists()
        
        await new_nfc_service.stop_nfc_system()