# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for NFC Domain layer components following DDD principles.

Tests cover:
- NfcTag entity (business logic and state management)
- TagIdentifier value object (immutability and validation)
- NfcAssociationService domain service (core business rules)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock
from typing import Optional

from app.src.domain.nfc.entities.nfc_tag import NfcTag
from app.src.domain.nfc.entities.association_session import AssociationSession, SessionState
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.services.nfc_association_service import NfcAssociationService
from app.src.domain.nfc.protocols.nfc_hardware_protocol import NfcRepositoryProtocol


class TestTagIdentifierValueObject:
    """Test TagIdentifier value object for immutability and validation."""
    
    def test_valid_tag_identifier_creation(self):
        """Test creation of valid tag identifiers."""
        # Basic hexadecimal UID
        tag_id = TagIdentifier(uid="1234abcd")
        assert tag_id.uid == "1234abcd"
        assert str(tag_id) == "1234abcd"
    
    def test_tag_identifier_immutability(self):
        """Test that TagIdentifier is immutable."""
        tag_id = TagIdentifier(uid="1234abcd")
        
        # Should not be able to modify uid
        with pytest.raises(AttributeError):
            tag_id.uid = "modified"
    
    def test_tag_identifier_validation_empty_uid(self):
        """Test validation fails for empty UID."""
        with pytest.raises(ValueError, match="Tag UID cannot be empty"):
            TagIdentifier(uid="")
        
        with pytest.raises(ValueError, match="Tag UID cannot be empty"):
            TagIdentifier(uid=None)
    
    def test_tag_identifier_validation_short_uid(self):
        """Test validation fails for UID too short."""
        with pytest.raises(ValueError, match="Tag UID too short"):
            TagIdentifier(uid="abc")  # Only 3 characters
        
        with pytest.raises(ValueError, match="Tag UID too short"):
            TagIdentifier(uid="ab")   # Only 2 characters
    
    def test_tag_identifier_validation_non_hexadecimal(self):
        """Test validation fails for non-hexadecimal UID."""
        with pytest.raises(ValueError, match="Tag UID must be hexadecimal"):
            TagIdentifier(uid="12xg34")  # Contains 'x' and 'g'
        
        with pytest.raises(ValueError, match="Tag UID must be hexadecimal"):
            TagIdentifier(uid="hello!")  # Contains letters and special chars
    
    def test_tag_identifier_valid_hexadecimal_cases(self):
        """Test various valid hexadecimal cases."""
        # Lowercase
        tag1 = TagIdentifier(uid="abcdef01")
        assert tag1.uid == "abcdef01"
        
        # Uppercase
        tag2 = TagIdentifier(uid="ABCDEF01")
        assert tag2.uid == "ABCDEF01"
        
        # Mixed case
        tag3 = TagIdentifier(uid="AbCdEf01")
        assert tag3.uid == "AbCdEf01"
        
        # Numbers only
        tag4 = TagIdentifier(uid="12345678")
        assert tag4.uid == "12345678"
        
        # Long UID
        tag5 = TagIdentifier(uid="0123456789abcdef0123456789abcdef")
        assert tag5.uid == "0123456789abcdef0123456789abcdef"
    
    def test_from_raw_data_factory(self):
        """Test factory method for creating from raw NFC data."""
        # Raw data with spaces
        tag1 = TagIdentifier.from_raw_data("12 34 AB CD")
        assert tag1.uid == "1234abcd"
        
        # Raw data with colons
        tag2 = TagIdentifier.from_raw_data("12:34:ab:cd")
        assert tag2.uid == "1234abcd"
        
        # Raw data with mixed separators
        tag3 = TagIdentifier.from_raw_data("12 34:AB CD")
        assert tag3.uid == "1234abcd"
        
        # Uppercase input becomes lowercase
        tag4 = TagIdentifier.from_raw_data("ABCDEF01")
        assert tag4.uid == "abcdef01"
    
    def test_is_valid_method(self):
        """Test is_valid method for validation checking."""
        # Valid identifier
        valid_tag = TagIdentifier(uid="1234abcd")
        assert valid_tag.is_valid() is True
        
        # Test is_valid with factory method
        valid_from_raw = TagIdentifier.from_raw_data("12 34 AB CD")
        assert valid_from_raw.is_valid() is True
    
    def test_tag_identifier_equality(self):
        """Test equality and hashing for use in collections."""
        tag1 = TagIdentifier(uid="1234abcd")
        tag2 = TagIdentifier(uid="1234abcd")
        tag3 = TagIdentifier(uid="5678efgh")
        
        # Equality
        assert tag1 == tag2
        assert tag1 != tag3
        
        # Hashable (can be used in sets/dicts) - dataclass frozen=True provides hash
        tag_set = {tag1, tag2, tag3}
        assert len(tag_set) == 2  # tag1 and tag2 are the same
    
    def test_edge_case_minimum_valid_uid(self):
        """Test minimum valid UID length."""
        min_tag = TagIdentifier(uid="1234")  # Exactly 4 characters
        assert min_tag.uid == "1234"
        assert min_tag.is_valid() is True


class TestNfcTagEntity:
    """Test NfcTag entity for business logic and state management."""
    
    def test_nfc_tag_creation(self):
        """Test basic NFC tag creation."""
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        
        assert tag.identifier == identifier
        assert tag.associated_playlist_id is None
        assert tag.last_detected_at is None
        assert tag.detection_count == 0
        assert tag.metadata == {}
    
    def test_nfc_tag_association_business_logic(self):
        """Test playlist association business logic."""
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        
        # Initially not associated
        assert not tag.is_associated()
        assert tag.get_associated_playlist_id() is None
        
        # Associate with playlist
        playlist_id = "playlist-123"
        tag.associate_with_playlist(playlist_id)
        
        assert tag.is_associated()
        assert tag.get_associated_playlist_id() == playlist_id
        assert tag.associated_playlist_id == playlist_id
    
    def test_nfc_tag_association_validation(self):
        """Test association validation rules."""
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        
        # Empty playlist ID should raise error
        with pytest.raises(ValueError, match="Playlist ID cannot be empty"):
            tag.associate_with_playlist("")
        
        with pytest.raises(ValueError, match="Playlist ID cannot be empty"):
            tag.associate_with_playlist("   ")  # Whitespace only
        
        with pytest.raises(ValueError, match="Playlist ID cannot be empty"):
            tag.associate_with_playlist(None)
    
    def test_nfc_tag_dissociation(self):
        """Test playlist dissociation."""
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        
        # Associate then dissociate
        tag.associate_with_playlist("playlist-123")
        assert tag.is_associated()
        
        tag.dissociate_from_playlist()
        assert not tag.is_associated()
        assert tag.get_associated_playlist_id() is None
    
    def test_nfc_tag_detection_tracking(self):
        """Test detection tracking business logic."""
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        
        # Initially not detected
        assert tag.detection_count == 0
        assert tag.last_detected_at is None
        assert not tag.is_recently_detected()
        
        # Mark as detected
        before_detection = datetime.now(timezone.utc)
        tag.mark_detected()
        after_detection = datetime.now(timezone.utc)
        
        assert tag.detection_count == 1
        assert tag.last_detected_at is not None
        assert before_detection <= tag.last_detected_at <= after_detection
        assert tag.is_recently_detected()
        
        # Mark as detected again
        tag.mark_detected()
        assert tag.detection_count == 2
    
    def test_nfc_tag_recent_detection_time_window(self):
        """Test recent detection with custom time windows."""
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        
        # Set detection time to 45 seconds ago
        past_time = datetime.now(timezone.utc) - timedelta(seconds=45)
        tag.last_detected_at = past_time
        
        # Should not be recent with default 30 second window
        assert not tag.is_recently_detected()
        assert not tag.is_recently_detected(30)
        
        # Should be recent with 60 second window
        assert tag.is_recently_detected(60)
        
        # Should be recent with 1 second if just detected
        tag.mark_detected()
        assert tag.is_recently_detected(1)
    
    def test_nfc_tag_equality_and_hashing(self):
        """Test tag equality based on identifier."""
        identifier1 = TagIdentifier(uid="1234abcd")
        identifier2 = TagIdentifier(uid="1234abcd")
        identifier3 = TagIdentifier(uid="5678efgh")
        
        tag1 = NfcTag(identifier=identifier1)
        tag2 = NfcTag(identifier=identifier2)
        tag3 = NfcTag(identifier=identifier3)
        
        # Same identifier = equal tags
        assert tag1 == tag2
        assert tag1 != tag3
        
        # Can be used in sets/dicts
        tag_set = {tag1, tag2, tag3}
        assert len(tag_set) == 2  # tag1 and tag2 are the same
        
        # Hash consistency - dataclass frozen=True provides hash
        assert hash(tag1) == hash(tag2)
    
    def test_nfc_tag_with_metadata(self):
        """Test tag with metadata."""
        identifier = TagIdentifier(uid="1234abcd")
        metadata = {"color": "blue", "size": "small"}
        tag = NfcTag(identifier=identifier, metadata=metadata)
        
        assert tag.metadata == metadata
        assert tag.metadata["color"] == "blue"
        
        # Metadata can be modified
        tag.metadata["new_field"] = "value"
        assert tag.metadata["new_field"] == "value"
    
    def test_nfc_tag_state_consistency(self):
        """Test tag state remains consistent across operations."""
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        
        # Associate, detect, dissociate sequence
        tag.associate_with_playlist("playlist-123")
        tag.mark_detected()
        original_count = tag.detection_count
        original_time = tag.last_detected_at
        
        tag.dissociate_from_playlist()
        
        # Detection history should remain
        assert tag.detection_count == original_count
        assert tag.last_detected_at == original_time
        
        # But association should be gone
        assert not tag.is_associated()


class MockNfcRepository:
    """Mock implementation of NfcRepositoryProtocol for testing."""
    
    def __init__(self):
        self.tags = {}
    
    async def find_by_identifier(self, identifier: TagIdentifier) -> Optional[NfcTag]:
        return self.tags.get(str(identifier))
    
    async def save_tag(self, tag: NfcTag) -> None:
        self.tags[str(tag.identifier)] = tag
    
    async def delete_tag(self, identifier: TagIdentifier) -> bool:
        key = str(identifier)
        if key in self.tags:
            del self.tags[key]
            return True
        return False


class TestNfcAssociationServiceDomainService:
    """Test NfcAssociationService domain service for business rules."""
    
    @pytest.fixture
    def mock_repository(self):
        """Fixture providing mock NFC repository."""
        return MockNfcRepository()
    
    @pytest.fixture
    def association_service(self, mock_repository):
        """Fixture providing NFC association service with mock repository."""
        return NfcAssociationService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_start_association_session(self, association_service):
        """Test starting an association session."""
        playlist_id = "playlist-123"
        
        session = await association_service.start_association_session(playlist_id)
        
        assert session is not None
        assert session.playlist_id == playlist_id
        assert session.state == SessionState.LISTENING
        assert session.is_active()
        
        # Should be in active sessions
        active_sessions = association_service.get_active_sessions()
        assert len(active_sessions) == 1
        assert active_sessions[0] == session
    
    @pytest.mark.asyncio
    async def test_start_association_session_validation(self, association_service):
        """Test association session start validation."""
        # Empty playlist ID should fail
        with pytest.raises(ValueError, match="Playlist ID is required"):
            await association_service.start_association_session("")
        
        with pytest.raises(ValueError, match="Playlist ID is required"):
            await association_service.start_association_session(None)
    
    @pytest.mark.asyncio
    async def test_duplicate_association_session_prevention(self, association_service):
        """Test prevention of duplicate association sessions."""
        playlist_id = "playlist-123"
        
        # Start first session
        session1 = await association_service.start_association_session(playlist_id)
        assert session1 is not None
        
        # Attempt to start second session for same playlist should fail
        with pytest.raises(ValueError, match="Association session already active"):
            await association_service.start_association_session(playlist_id)
    
    @pytest.mark.asyncio
    async def test_process_new_tag_detection(self, association_service, mock_repository):
        """Test processing detection of new tag."""
        # Start association session
        playlist_id = "playlist-123"
        session = await association_service.start_association_session(playlist_id)
        
        # Process tag detection
        tag_identifier = TagIdentifier(uid="1234abcd")
        result = await association_service.process_tag_detection(tag_identifier)
        
        # Should result in successful association
        assert result["action"] == "association_success"
        assert result["playlist_id"] == playlist_id
        assert result["tag_id"] == str(tag_identifier)
        assert result["session_state"] == SessionState.SUCCESS.value
        
        # Tag should be saved in repository
        saved_tag = await mock_repository.find_by_identifier(tag_identifier)
        assert saved_tag is not None
        assert saved_tag.is_associated()
        assert saved_tag.get_associated_playlist_id() == playlist_id
        assert saved_tag.detection_count == 1
    
    @pytest.mark.asyncio
    async def test_process_existing_tag_detection(self, association_service, mock_repository):
        """Test processing detection of existing tag."""
        # Pre-populate repository with existing tag
        existing_identifier = TagIdentifier(uid="1234abcd")
        existing_tag = NfcTag(
            identifier=existing_identifier,
            associated_playlist_id="old-playlist",
            detection_count=5
        )
        await mock_repository.save_tag(existing_tag)
        
        # Start association session for different playlist
        new_playlist_id = "new-playlist-456"
        session = await association_service.start_association_session(new_playlist_id)
        
        # Process detection of existing tag
        result = await association_service.process_tag_detection(existing_identifier)
        
        # Should detect duplicate association
        assert result["action"] == "duplicate_association"
        assert result["existing_playlist_id"] == "old-playlist"
        assert result["playlist_id"] == new_playlist_id
        assert result["session_state"] == SessionState.DUPLICATE.value
        
        # Original tag should remain unchanged
        tag_after = await mock_repository.find_by_identifier(existing_identifier)
        assert tag_after.get_associated_playlist_id() == "old-playlist"
        assert tag_after.detection_count == 6  # Should increment detection count
    
    @pytest.mark.asyncio
    async def test_process_tag_detection_without_active_session(self, association_service, mock_repository):
        """Test tag detection when no association session is active."""
        tag_identifier = TagIdentifier(uid="1234abcd")
        
        # Process detection with no active sessions
        result = await association_service.process_tag_detection(tag_identifier)
        
        # Should just record detection
        assert result["action"] == "tag_detected"
        assert result["tag_id"] == str(tag_identifier)
        assert result["no_active_sessions"] is True
        assert result["associated_playlist"] is None
        
        # Tag should be saved
        saved_tag = await mock_repository.find_by_identifier(tag_identifier)
        assert saved_tag is not None
        assert not saved_tag.is_associated()
        assert saved_tag.detection_count == 1
    
    @pytest.mark.asyncio
    async def test_stop_association_session(self, association_service):
        """Test stopping an association session."""
        # Start session
        playlist_id = "playlist-123"
        session = await association_service.start_association_session(playlist_id)
        session_id = session.session_id
        
        # Stop session
        success = await association_service.stop_association_session(session_id)
        assert success is True
        
        # Session should be marked as stopped
        stopped_session = await association_service.get_association_session(session_id)
        assert stopped_session.state == SessionState.STOPPED
        assert not stopped_session.is_active()
        
        # Should not be in active sessions
        active_sessions = association_service.get_active_sessions()
        assert len(active_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_stop_nonexistent_session(self, association_service):
        """Test stopping a session that doesn't exist."""
        success = await association_service.stop_association_session("nonexistent-session")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, association_service):
        """Test cleanup of expired sessions."""
        # Start session with very short timeout
        playlist_id = "playlist-123"
        session = await association_service.start_association_session(playlist_id, timeout_seconds=1)
        
        # Initially active
        active_sessions = association_service.get_active_sessions()
        assert len(active_sessions) == 1
        
        # Simulate time passage by modifying started_at
        session.started_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        # Run cleanup
        cleaned_count = await association_service.cleanup_expired_sessions()
        assert cleaned_count == 1
        
        # Session should be marked as timeout
        assert session.state == SessionState.TIMEOUT
        assert not session.is_active()
        
        # No more active sessions
        active_sessions = association_service.get_active_sessions()
        assert len(active_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_dissociate_tag(self, association_service, mock_repository):
        """Test tag dissociation business logic."""
        # Create associated tag
        identifier = TagIdentifier(uid="1234abcd")
        tag = NfcTag(identifier=identifier)
        tag.associate_with_playlist("playlist-123")
        await mock_repository.save_tag(tag)
        
        # Dissociate tag
        success = await association_service.dissociate_tag(identifier)
        assert success is True
        
        # Tag should be dissociated
        updated_tag = await mock_repository.find_by_identifier(identifier)
        assert not updated_tag.is_associated()
        assert updated_tag.get_associated_playlist_id() is None
    
    @pytest.mark.asyncio
    async def test_dissociate_nonexistent_tag(self, association_service):
        """Test dissociation of non-existent tag."""
        identifier = TagIdentifier(uid="nonexistent")
        success = await association_service.dissociate_tag(identifier)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_process_tag_for_specific_session(self, association_service):
        """Test processing tag detection for specific session."""
        # Start two sessions
        session1 = await association_service.start_association_session("playlist-1")
        session2 = await association_service.start_association_session("playlist-2")
        
        # Process tag for specific session
        tag_identifier = TagIdentifier(uid="1234abcd")
        result = await association_service.process_tag_detection(
            tag_identifier, 
            session_id=session1.session_id
        )
        
        # Should associate with session1's playlist only
        assert result["action"] == "association_success"
        assert result["playlist_id"] == "playlist-1"
        assert result["session_id"] == session1.session_id
        
        # Session1 should be successful, session2 still listening
        assert session1.state == SessionState.SUCCESS
        assert session2.state == SessionState.LISTENING
    
    @pytest.mark.asyncio
    async def test_multiple_active_sessions_processing(self, association_service):
        """Test tag processing with multiple active sessions."""
        # Start multiple sessions for different playlists (should work)
        session1 = await association_service.start_association_session("playlist-1")
        session2 = await association_service.start_association_session("playlist-2") 
        
        # Process tag detection (should process for first active session found)
        tag_identifier = TagIdentifier(uid="1234abcd")
        result = await association_service.process_tag_detection(tag_identifier)
        
        # Should associate with one of the playlists
        assert result["action"] == "association_success"
        assert result["playlist_id"] in ["playlist-1", "playlist-2"]
    
    def test_find_active_session_for_playlist(self, association_service):
        """Test finding active session for specific playlist."""
        # No sessions initially
        session = association_service._find_active_session_for_playlist("playlist-123")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_session_timeout_property(self, association_service):
        """Test session timeout calculation."""
        session = await association_service.start_association_session("playlist-123", timeout_seconds=3600)
        
        # Should not be expired immediately
        assert not session.is_expired()
        assert session.is_active()
        
        # Timeout should be approximately 1 hour from now
        timeout_at = session.timeout_at
        now = datetime.now(timezone.utc)
        time_diff = timeout_at - now
        
        # Should be close to 1 hour (allow some variance for test execution time)
        assert 3590 <= time_diff.total_seconds() <= 3600


class TestAssociationSessionEntity:
    """Test AssociationSession entity business logic."""
    
    def test_association_session_creation(self):
        """Test basic association session creation."""
        session = AssociationSession(playlist_id="playlist-123")
        
        assert session.playlist_id == "playlist-123"
        assert session.state == SessionState.LISTENING
        assert session.session_id is not None
        assert len(session.session_id) > 0
        assert session.started_at is not None
        assert session.detected_tag is None
        assert session.conflict_playlist_id is None
        assert session.timeout_seconds == 60  # default
        assert session.is_active()
        assert not session.is_expired()
    
    def test_association_session_custom_timeout(self):
        """Test session creation with custom timeout."""
        session = AssociationSession(playlist_id="playlist-123", timeout_seconds=300)
        assert session.timeout_seconds == 300
        
        # Timeout should be 5 minutes from creation
        expected_timeout = session.started_at.timestamp() + 300
        actual_timeout = session.timeout_at.timestamp()
        assert abs(actual_timeout - expected_timeout) < 1  # Allow 1 second variance
    
    def test_association_session_detect_tag(self):
        """Test tag detection in session."""
        session = AssociationSession(playlist_id="playlist-123")
        tag_identifier = TagIdentifier(uid="1234abcd")
        
        session.detect_tag(tag_identifier)
        
        assert session.detected_tag == tag_identifier
        assert session.state == SessionState.LISTENING  # Still listening until marked successful
    
    def test_association_session_mark_successful(self):
        """Test marking session as successful."""
        session = AssociationSession(playlist_id="playlist-123")
        tag_identifier = TagIdentifier(uid="1234abcd")
        
        session.detect_tag(tag_identifier)
        session.mark_successful()
        
        assert session.state == SessionState.SUCCESS
        assert not session.is_active()
    
    def test_association_session_mark_duplicate(self):
        """Test marking session with duplicate tag."""
        session = AssociationSession(playlist_id="playlist-123")
        tag_identifier = TagIdentifier(uid="1234abcd")
        
        session.detect_tag(tag_identifier)
        session.mark_duplicate("existing-playlist")
        
        assert session.state == SessionState.DUPLICATE
        assert session.conflict_playlist_id == "existing-playlist"
        assert not session.is_active()
    
    def test_association_session_mark_stopped(self):
        """Test manually stopping session."""
        session = AssociationSession(playlist_id="playlist-123")
        
        session.mark_stopped()
        
        assert session.state == SessionState.STOPPED
        assert not session.is_active()
    
    def test_association_session_mark_timeout(self):
        """Test marking session as timed out."""
        session = AssociationSession(playlist_id="playlist-123")
        
        session.mark_timeout()
        
        assert session.state == SessionState.TIMEOUT
        assert not session.is_active()
    
    def test_association_session_expiration(self):
        """Test session expiration logic."""
        session = AssociationSession(playlist_id="playlist-123", timeout_seconds=1)
        
        # Should not be expired initially
        assert not session.is_expired()
        
        # Simulate time passage
        session.started_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        # Should now be expired
        assert session.is_expired()
        assert not session.is_active()  # Expired sessions are not active
    
    def test_association_session_to_dict(self):
        """Test session serialization."""
        session = AssociationSession(
            playlist_id="playlist-123", 
            timeout_seconds=300
        )
        tag_identifier = TagIdentifier(uid="1234abcd")
        session.detect_tag(tag_identifier)
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == session.session_id
        assert session_dict["playlist_id"] == "playlist-123"
        assert session_dict["state"] == SessionState.LISTENING.value
        assert "remaining_seconds" in session_dict
        assert session_dict["detected_tag"] == str(tag_identifier)
        assert session_dict["conflict_playlist_id"] is None
        assert "started_at" in session_dict
        assert "timeout_at" in session_dict
        
        # Test with duplicate state
        session.mark_duplicate("other-playlist")
        session_dict = session.to_dict()
        assert session_dict["state"] == SessionState.DUPLICATE.value
        assert session_dict["conflict_playlist_id"] == "other-playlist"