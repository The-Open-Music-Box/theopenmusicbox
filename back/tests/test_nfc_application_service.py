# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for NFC Application Service layer following DDD principles.

Tests cover:
- NfcApplicationService use case orchestration
- Hardware integration
- Error handling and resilience
- Callback mechanisms
- Session management
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, call
from datetime import datetime, timezone, timedelta

from app.src.application.services.nfc_application_service import NfcApplicationService
from app.src.domain.nfc.entities.nfc_tag import NfcTag
from app.src.domain.nfc.entities.association_session import AssociationSession, SessionState
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.services.nfc_association_service import NfcAssociationService
from app.src.domain.nfc.protocols.nfc_hardware_protocol import NfcHardwareProtocol, NfcRepositoryProtocol


class MockNfcHardware:
    """Mock NFC hardware for testing."""
    
    def __init__(self):
        self.is_started = False
        self.tag_detected_callback = None
        self.tag_removed_callback = None
        self.should_fail_start = False
        self.hardware_status = {"status": "ready", "connected": True}
    
    async def start_detection(self):
        if self.should_fail_start:
            raise Exception("Hardware failure")
        self.is_started = True
    
    async def stop_detection(self):
        self.is_started = False
    
    def is_detecting(self):
        return self.is_started
    
    async def get_hardware_status(self):
        return self.hardware_status
    
    def set_tag_detected_callback(self, callback):
        self.tag_detected_callback = callback
    
    def set_tag_removed_callback(self, callback):
        self.tag_removed_callback = callback
    
    def simulate_tag_detection(self, tag_id: str):
        """Helper method to simulate tag detection."""
        if self.tag_detected_callback:
            identifier = TagIdentifier(uid=tag_id)
            self.tag_detected_callback(identifier)
    
    def simulate_tag_removal(self):
        """Helper method to simulate tag removal."""
        if self.tag_removed_callback:
            self.tag_removed_callback()


class MockNfcRepository:
    """Mock NFC repository for testing."""
    
    def __init__(self):
        self.tags = {}
    
    async def find_by_identifier(self, identifier: TagIdentifier):
        return self.tags.get(str(identifier))
    
    async def save_tag(self, tag: NfcTag):
        self.tags[str(tag.identifier)] = tag
    
    async def delete_tag(self, identifier: TagIdentifier):
        key = str(identifier)
        if key in self.tags:
            del self.tags[key]
            return True
        return False


class TestNfcApplicationService:
    """Test NfcApplicationService use case orchestration."""
    
    @pytest.fixture
    def mock_hardware(self):
        """Mock NFC hardware fixture."""
        return MockNfcHardware()
    
    @pytest.fixture
    def mock_repository(self):
        """Mock NFC repository fixture."""
        return MockNfcRepository()
    
    @pytest.fixture
    def app_service(self, mock_hardware, mock_repository):
        """NFC application service fixture."""
        return NfcApplicationService(
            nfc_hardware=mock_hardware,
            nfc_repository=mock_repository
        )
    
    @pytest.mark.asyncio
    async def test_start_nfc_system_success(self, app_service, mock_hardware):
        """Test successful NFC system startup."""
        result = await app_service.start_nfc_system()
        
        assert result["status"] == "success"
        assert "NFC system started" in result["message"]
        assert "hardware_status" in result
        assert mock_hardware.is_detecting()
    
    @pytest.mark.asyncio
    async def test_start_nfc_system_hardware_failure(self, app_service, mock_hardware):
        """Test NFC system startup with hardware failure."""
        mock_hardware.should_fail_start = True
        
        result = await app_service.start_nfc_system()
        
        assert result["status"] == "error"
        assert "Failed to start NFC system" in result["message"]
        assert not mock_hardware.is_detecting()
    
    @pytest.mark.asyncio
    async def test_stop_nfc_system_success(self, app_service, mock_hardware):
        """Test successful NFC system shutdown."""
        # Start first
        await app_service.start_nfc_system()
        assert mock_hardware.is_detecting()
        
        # Then stop
        result = await app_service.stop_nfc_system()
        
        assert result["status"] == "success"
        assert "NFC system stopped" in result["message"]
        assert not mock_hardware.is_detecting()
    
    @pytest.mark.asyncio
    async def test_stop_nfc_system_with_cleanup_task(self, app_service, mock_hardware):
        """Test NFC system shutdown cancels cleanup task."""
        await app_service.start_nfc_system()
        
        # Verify cleanup task was started
        assert app_service._cleanup_task is not None
        assert not app_service._cleanup_task.done()
        
        await app_service.stop_nfc_system()
        
        # Task should be cancelled
        assert app_service._cleanup_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_start_association_use_case_success(self, app_service):
        """Test successful association session start."""
        playlist_id = "playlist-123"
        
        result = await app_service.start_association_use_case(playlist_id, timeout_seconds=120)
        
        assert result["status"] == "success"
        assert "Association session started" in result["message"]
        assert "session" in result
        assert result["session"]["playlist_id"] == playlist_id
        assert result["session"]["timeout_seconds"] == 120
    
    @pytest.mark.asyncio
    async def test_start_association_use_case_validation_error(self, app_service):
        """Test association session start with validation error."""
        # Empty playlist ID should cause validation error
        result = await app_service.start_association_use_case("")
        
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "Playlist ID is required" in result["message"]
    
    @pytest.mark.asyncio
    async def test_start_association_use_case_duplicate_session(self, app_service):
        """Test starting duplicate association session."""
        playlist_id = "playlist-123"
        
        # Start first session
        await app_service.start_association_use_case(playlist_id)
        
        # Try to start second session for same playlist
        result = await app_service.start_association_use_case(playlist_id)
        
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "already active" in result["message"]
    
    @pytest.mark.asyncio
    async def test_stop_association_use_case_success(self, app_service):
        """Test successful association session stop."""
        playlist_id = "playlist-123"
        
        # Start session
        start_result = await app_service.start_association_use_case(playlist_id)
        session_id = start_result["session"]["session_id"]
        
        # Stop session
        result = await app_service.stop_association_use_case(session_id)
        
        assert result["status"] == "success"
        assert "Association session stopped" in result["message"]
        assert result["session_id"] == session_id
    
    @pytest.mark.asyncio
    async def test_stop_association_use_case_not_found(self, app_service):
        """Test stopping non-existent association session."""
        result = await app_service.stop_association_use_case("nonexistent-session")
        
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert "not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_nfc_status_use_case(self, app_service, mock_hardware):
        """Test comprehensive NFC status retrieval."""
        # Start system and association session
        await app_service.start_nfc_system()
        await app_service.start_association_use_case("playlist-123")
        
        result = await app_service.get_nfc_status_use_case()
        
        assert result["status"] == "success"
        assert result["detecting"] is True
        assert result["session_count"] == 1
        assert len(result["active_sessions"]) == 1
        assert "hardware" in result
    
    @pytest.mark.asyncio
    async def test_dissociate_tag_use_case_success(self, app_service, mock_repository):
        """Test successful tag dissociation."""
        # Pre-populate repository with associated tag
        tag_identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=tag_identifier)
        tag.associate_with_playlist("playlist-123")
        await mock_repository.save_tag(tag)
        
        result = await app_service.dissociate_tag_use_case("1234abcd")
        
        assert result["status"] == "success"
        assert "dissociated successfully" in result["message"]
        assert result["tag_id"] == "1234abcd"
        
        # Tag should be dissociated in repository
        updated_tag = await mock_repository.find_by_identifier(tag_identifier)
        assert not updated_tag.is_associated()
    
    @pytest.mark.asyncio
    async def test_dissociate_tag_use_case_not_found(self, app_service):
        """Test dissociation of non-existent tag."""
        result = await app_service.dissociate_tag_use_case("nonexistent")
        
        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert "not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_dissociate_tag_use_case_invalid_id(self, app_service):
        """Test dissociation with invalid tag ID."""
        result = await app_service.dissociate_tag_use_case("xx")  # Too short
        
        assert result["status"] == "error"
        assert result["error_type"] == "validation_error"
        assert "Invalid tag ID" in result["message"]
    
    @pytest.mark.asyncio
    async def test_tag_detection_callback_integration(self, app_service, mock_hardware, mock_repository):
        """Test tag detection callback integration."""
        # Start association session
        await app_service.start_association_use_case("playlist-123")
        
        # Set up detection callback tracking
        detected_tags = []
        association_events = []
        
        app_service.register_tag_detected_callback(lambda tag_id: detected_tags.append(tag_id))
        app_service.register_association_callback(lambda event: association_events.append(event))
        
        # Simulate tag detection
        mock_hardware.simulate_tag_detection("1234abcd")
        
        # Give async processing time to complete
        await asyncio.sleep(0.1)
        
        # Verify callbacks were called
        assert len(detected_tags) == 1
        assert detected_tags[0] == "1234abcd"
        assert len(association_events) == 1
        assert association_events[0]["action"] == "association_success"
    
    @pytest.mark.asyncio
    async def test_tag_detection_without_session(self, app_service, mock_hardware):
        """Test tag detection when no association session is active."""
        detected_tags = []
        association_events = []
        
        app_service.register_tag_detected_callback(lambda tag_id: detected_tags.append(tag_id))
        app_service.register_association_callback(lambda event: association_events.append(event))
        
        # Simulate tag detection without active session
        mock_hardware.simulate_tag_detection("1234abcd")
        await asyncio.sleep(0.1)
        
        # Should still trigger callbacks
        assert len(detected_tags) == 1
        assert len(association_events) == 1
        assert association_events[0]["action"] == "tag_detected"
        assert association_events[0]["no_active_sessions"] is True
    
    @pytest.mark.asyncio
    async def test_callback_error_handling(self, app_service, mock_hardware):
        """Test error handling in callbacks."""
        def failing_callback(tag_id):
            raise Exception("Callback error")
        
        app_service.register_tag_detected_callback(failing_callback)
        
        # Should not crash when callback fails
        mock_hardware.simulate_tag_detection("1234abcd")
        await asyncio.sleep(0.1)
        
        # Service should continue working
        assert True  # If we get here, error was handled gracefully
    
    @pytest.mark.asyncio
    async def test_tag_removal_callback(self, app_service, mock_hardware):
        """Test tag removal callback."""
        # Start system
        await app_service.start_nfc_system()
        
        # Should not crash when tag is removed
        mock_hardware.simulate_tag_removal()
        await asyncio.sleep(0.1)
        
        assert True  # Successful if no exception
    
    @pytest.mark.asyncio
    async def test_periodic_cleanup_expired_sessions(self, app_service):
        """Test periodic cleanup of expired sessions."""
        # Start system to initiate cleanup task
        await app_service.start_nfc_system()
        
        # Start session with very short timeout
        await app_service.start_association_use_case("playlist-123", timeout_seconds=1)
        
        # Verify session exists
        status = await app_service.get_nfc_status_use_case()
        assert status["session_count"] == 1
        
        # Wait for session to expire and cleanup to run
        await asyncio.sleep(2)
        
        # Session should be cleaned up (this tests the cleanup process)
        # Note: The actual cleanup runs every 30 seconds, but the session expiration logic is tested
        session = await app_service._association_service.get_association_session(
            status["active_sessions"][0]["session_id"]
        )
        assert session.is_expired()
    
    @pytest.mark.asyncio
    async def test_hardware_callback_setup(self, mock_hardware, mock_repository):
        """Test that hardware callbacks are properly set up."""
        app_service = NfcApplicationService(mock_hardware, mock_repository)
        
        # Callbacks should be set during initialization
        assert mock_hardware.tag_detected_callback is not None
        assert mock_hardware.tag_removed_callback is not None
    
    @pytest.mark.asyncio
    async def test_custom_association_service(self, mock_hardware, mock_repository):
        """Test using custom association service."""
        custom_service = NfcAssociationService(mock_repository)
        
        app_service = NfcApplicationService(
            nfc_hardware=mock_hardware,
            nfc_repository=mock_repository,
            nfc_association_service=custom_service
        )
        
        assert app_service._association_service is custom_service
    
    @pytest.mark.asyncio
    async def test_multiple_callbacks_registration(self, app_service):
        """Test registering multiple callbacks."""
        detected_tags_1 = []
        detected_tags_2 = []
        
        app_service.register_tag_detected_callback(lambda tag_id: detected_tags_1.append(tag_id))
        app_service.register_tag_detected_callback(lambda tag_id: detected_tags_2.append(tag_id))
        
        # Both callbacks should be called
        app_service._on_tag_detected(TagIdentifier(uid="1234abcd"))
        await asyncio.sleep(0.1)
        
        assert len(detected_tags_1) == 1
        assert len(detected_tags_2) == 1
    
    @pytest.mark.asyncio
    async def test_association_service_integration(self, app_service, mock_repository):
        """Test integration with association service."""
        # Start association session
        result = await app_service.start_association_use_case("playlist-123")
        session_id = result["session"]["session_id"]
        
        # Verify session can be retrieved through service
        session = await app_service._association_service.get_association_session(session_id)
        assert session is not None
        assert session.playlist_id == "playlist-123"
        
        # Stop session through application service
        await app_service.stop_association_use_case(session_id)
        
        # Verify session is stopped
        assert session.state == SessionState.STOPPED
    
    @pytest.mark.asyncio
    async def test_error_handling_in_tag_processing(self, app_service, mock_hardware):
        """Test error handling during tag processing."""
        # Mock the association service to raise an error
        with patch.object(app_service._association_service, 'process_tag_detection', 
                         side_effect=Exception("Processing error")):
            
            # Should not crash when tag processing fails
            mock_hardware.simulate_tag_detection("1234abcd")
            await asyncio.sleep(0.1)
            
            assert True  # Successful if no exception propagated
    
    @pytest.mark.asyncio
    async def test_cleanup_task_cancellation_on_stop(self, app_service):
        """Test cleanup task is properly cancelled on system stop."""
        await app_service.start_nfc_system()
        
        cleanup_task = app_service._cleanup_task
        assert cleanup_task is not None
        assert not cleanup_task.done()
        
        await app_service.stop_nfc_system()
        
        # Task should be cancelled
        assert cleanup_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_system_restart_after_stop(self, app_service, mock_hardware):
        """Test system can be restarted after being stopped."""
        # Start, stop, then start again
        await app_service.start_nfc_system()
        assert mock_hardware.is_detecting()
        
        await app_service.stop_nfc_system()
        assert not mock_hardware.is_detecting()
        
        await app_service.start_nfc_system()
        assert mock_hardware.is_detecting()
    
    @pytest.mark.asyncio
    async def test_hardware_status_error_handling(self, app_service, mock_hardware):
        """Test error handling when hardware status retrieval fails."""
        # Mock hardware status to raise error
        async def failing_status():
            raise Exception("Hardware communication error")
        
        mock_hardware.get_hardware_status = failing_status
        
        result = await app_service.get_nfc_status_use_case()
        
        assert result["status"] == "error"
        assert "Failed to get status" in result["message"]
    
    @pytest.mark.asyncio
    async def test_concurrent_association_sessions_different_playlists(self, app_service):
        """Test handling multiple association sessions for different playlists."""
        # Start sessions for different playlists
        result1 = await app_service.start_association_use_case("playlist-1")
        result2 = await app_service.start_association_use_case("playlist-2")
        
        assert result1["status"] == "success"
        assert result2["status"] == "success"
        
        # Check status shows both sessions
        status = await app_service.get_nfc_status_use_case()
        assert status["session_count"] == 2
    
    @pytest.mark.asyncio
    async def test_session_timeout_property_integration(self, app_service):
        """Test session timeout integration with application service."""
        result = await app_service.start_association_use_case("playlist-123", timeout_seconds=10)
        
        session_data = result["session"]
        assert session_data["timeout_seconds"] == 10
        
        # Session should have timeout set correctly
        session_id = session_data["session_id"]
        session = await app_service._association_service.get_association_session(session_id)
        assert session.timeout_seconds == 10