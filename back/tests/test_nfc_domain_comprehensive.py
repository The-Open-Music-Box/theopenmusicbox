# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Comprehensive tests for NFC domain business logic."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

from app.src.domain.nfc.entities.nfc_tag import NfcTag
from app.src.domain.nfc.entities.association_session import AssociationSession, AssociationState
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.services.nfc_association_service import NfcAssociationService
from app.src.domain.nfc.repositories.nfc_memory_repository import NfcMemoryRepository


class TestTagIdentifierValueObject:
    """Tests for TagIdentifier value object business rules."""

    def test_valid_tag_identifier_creation(self):
        """Test creating valid tag identifiers."""
        valid_identifiers = [
            "04f7eda4df6181",
            "AABBCCDD",
            "1234567890ABCDEF",
            "a1b2c3d4"
        ]

        for uid in valid_identifiers:
            identifier = TagIdentifier(uid)
            assert str(identifier) == uid.lower()
            assert identifier.raw_value == uid.lower()

    def test_invalid_tag_identifier_rejection(self):
        """Test rejection of invalid tag identifiers."""
        invalid_identifiers = [
            "",           # Empty
            "123",        # Too short
            "GHIJKLMN",   # Non-hex characters
            "12 34 56",   # Spaces
            None,         # None type
        ]

        for uid in invalid_identifiers:
            with pytest.raises(ValueError):
                TagIdentifier(uid)

    def test_tag_identifier_normalization(self):
        """Test that identifiers are normalized to lowercase."""
        identifier = TagIdentifier("AABBCCDD")
        assert str(identifier) == "aabbccdd"

    def test_tag_identifier_equality(self):
        """Test equality comparison between identifiers."""
        id1 = TagIdentifier("04f7eda4df6181")
        id2 = TagIdentifier("04F7EDA4DF6181")  # Same but uppercase
        id3 = TagIdentifier("aabbccdd")

        assert id1 == id2  # Case insensitive
        assert id1 != id3  # Different values
        assert hash(id1) == hash(id2)  # Same hash for equal objects


class TestNfcTagEntity:
    """Tests for NfcTag domain entity business logic."""

    def test_nfc_tag_creation(self):
        """Test creating NFC tag entity."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        assert tag.identifier == identifier
        assert tag.associated_playlist_id is None
        assert tag.last_detected_at is None
        assert tag.detection_count == 0

    def test_associate_playlist(self):
        """Test associating playlist with tag."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)
        playlist_id = "playlist-123"

        tag.associate_playlist(playlist_id)

        assert tag.associated_playlist_id == playlist_id
        assert tag.is_associated()

    def test_dissociate_playlist(self):
        """Test dissociating playlist from tag."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)
        tag.associate_playlist("playlist-123")

        tag.dissociate_playlist()

        assert tag.associated_playlist_id is None
        assert not tag.is_associated()

    def test_record_detection(self):
        """Test recording tag detection."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        before_detection = datetime.now()
        tag.record_detection()
        after_detection = datetime.now()

        assert tag.detection_count == 1
        assert before_detection <= tag.last_detected_at <= after_detection

        # Second detection
        tag.record_detection()
        assert tag.detection_count == 2

    def test_recently_detected(self):
        """Test recent detection logic."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        # Not detected yet
        assert not tag.was_recently_detected()

        # Just detected
        tag.record_detection()
        assert tag.was_recently_detected()

        # Manually set old detection time
        tag.last_detected_at = datetime.now() - timedelta(minutes=10)
        assert not tag.was_recently_detected()


class TestAssociationSessionEntity:
    """Tests for AssociationSession domain entity business logic."""

    def test_session_creation(self):
        """Test creating association session."""
        session_id = "session-123"
        playlist_id = "playlist-456"
        timeout_seconds = 60

        session = AssociationSession(session_id, playlist_id, timeout_seconds)

        assert session.session_id == session_id
        assert session.playlist_id == playlist_id
        assert session.state == AssociationState.LISTENING
        assert not session.is_expired()
        assert session.tag_id is None

    def test_session_timeout_calculation(self):
        """Test session timeout calculation."""
        session = AssociationSession("session-123", "playlist-456", 60)

        # Should expire in approximately 60 seconds
        expected_expiry = datetime.now() + timedelta(seconds=60)
        actual_expiry = session.timeout_at

        # Allow for small timing differences
        assert abs((actual_expiry - expected_expiry).total_seconds()) < 1

    def test_session_expiration_detection(self):
        """Test session expiration detection."""
        session = AssociationSession("session-123", "playlist-456", 1)

        # Not expired initially
        assert not session.is_expired()

        # Manually set expired time
        session.timeout_at = datetime.now() - timedelta(seconds=1)
        assert session.is_expired()

    def test_session_state_transitions(self):
        """Test valid session state transitions."""
        session = AssociationSession("session-123", "playlist-456", 60)

        # Start in LISTENING state
        assert session.state == AssociationState.LISTENING

        # Can transition to SUCCESS
        session.mark_successful("tag-123")
        assert session.state == AssociationState.SUCCESS
        assert session.tag_id == "tag-123"

        # Create new session for other transitions
        session2 = AssociationSession("session-456", "playlist-789", 60)
        session2.mark_duplicate("tag-456", "existing-playlist-123")
        assert session2.state == AssociationState.DUPLICATE
        assert session2.tag_id == "tag-456"
        assert session2.conflict_playlist_id == "existing-playlist-123"

        # Test STOPPED state
        session3 = AssociationSession("session-789", "playlist-012", 60)
        session3.mark_stopped()
        assert session3.state == AssociationState.STOPPED

        # Test TIMEOUT state
        session4 = AssociationSession("session-012", "playlist-345", 60)
        session4.mark_timeout()
        assert session4.state == AssociationState.TIMEOUT

        # Test ERROR state
        session5 = AssociationSession("session-345", "playlist-678", 60)
        session5.mark_error("Test error message")
        assert session5.state == AssociationState.ERROR
        assert session5.error_message == "Test error message"

    def test_session_serialization(self):
        """Test session serialization to dictionary."""
        session = AssociationSession("session-123", "playlist-456", 60)
        session.mark_successful("tag-123")

        data = session.to_dict()

        expected_keys = {
            'session_id', 'playlist_id', 'state', 'tag_id',
            'started_at', 'timeout_at', 'conflict_playlist_id', 'error_message'
        }
        assert set(data.keys()) == expected_keys
        assert data['session_id'] == "session-123"
        assert data['playlist_id'] == "playlist-456"
        assert data['state'] == "SUCCESS"
        assert data['tag_id'] == "tag-123"


class TestNfcAssociationService:
    """Tests for NFC Association Service domain business logic."""

    def setup_method(self):
        """Setup test dependencies."""
        self.repository = NfcMemoryRepository()
        self.playlist_repository = AsyncMock()
        self.service = NfcAssociationService(self.repository, self.playlist_repository)

    @pytest.mark.asyncio
    async def test_start_association_session(self):
        """Test starting new association session."""
        playlist_id = "playlist-123"
        timeout_seconds = 60

        session = await self.service.start_association_session(playlist_id, timeout_seconds)

        assert session is not None
        assert session.playlist_id == playlist_id
        assert session.state == AssociationState.LISTENING
        assert not session.is_expired()

    @pytest.mark.asyncio
    async def test_process_tag_detection_new_association(self):
        """Test processing tag detection for new association."""
        # Start association session
        playlist_id = "playlist-123"
        session = await self.service.start_association_session(playlist_id)

        # Mock playlist repository sync
        self.playlist_repository.update_nfc_tag_association.return_value = True

        # Process tag detection
        tag_identifier = TagIdentifier("04f7eda4df6181")
        result = await self.service.process_tag_detection(tag_identifier)

        assert result['success'] is True
        assert result['session_id'] == session.session_id
        assert result['state'] == AssociationState.SUCCESS

        # Verify tag was stored and associated
        stored_tag = await self.repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None
        assert stored_tag.associated_playlist_id == playlist_id

        # Verify playlist repository was called
        self.playlist_repository.update_nfc_tag_association.assert_called_once_with(
            playlist_id, str(tag_identifier)
        )

    @pytest.mark.asyncio
    async def test_process_tag_detection_duplicate_conflict(self):
        """Test processing tag detection with existing association."""
        # Create existing tag with different playlist
        existing_identifier = TagIdentifier("04f7eda4df6181")
        existing_tag = NfcTag(existing_identifier)
        existing_tag.associate_playlist("existing-playlist-456")
        await self.repository.save(existing_tag)

        # Start new association session for different playlist
        new_playlist_id = "new-playlist-123"
        session = await self.service.start_association_session(new_playlist_id)

        # Process same tag
        result = await self.service.process_tag_detection(existing_identifier)

        assert result['success'] is False
        assert result['session_id'] == session.session_id
        assert result['state'] == AssociationState.DUPLICATE
        assert result['conflict_playlist_id'] == "existing-playlist-456"

    @pytest.mark.asyncio
    async def test_process_tag_detection_no_active_session(self):
        """Test processing tag detection without active session."""
        tag_identifier = TagIdentifier("04f7eda4df6181")

        result = await self.service.process_tag_detection(tag_identifier)

        # Should still record the detection but no association
        assert result['success'] is False
        assert 'session_id' not in result

        # Tag should be recorded
        stored_tag = await self.repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None
        assert stored_tag.detection_count == 1

    @pytest.mark.asyncio
    async def test_stop_association_session(self):
        """Test stopping association session."""
        session = await self.service.start_association_session("playlist-123")
        session_id = session.session_id

        result = await self.service.stop_association_session(session_id)

        assert result is True

        # Verify session is stopped
        active_sessions = await self.service.get_active_sessions()
        assert len(active_sessions) == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test automatic cleanup of expired sessions."""
        # Create expired session
        expired_session = await self.service.start_association_session("playlist-123", 1)
        expired_session.timeout_at = datetime.now() - timedelta(seconds=1)

        # Create active session
        active_session = await self.service.start_association_session("playlist-456", 300)

        # Cleanup expired sessions
        cleanup_count = await self.service.cleanup_expired_sessions()

        assert cleanup_count == 1

        # Verify only active session remains
        active_sessions = await self.service.get_active_sessions()
        assert len(active_sessions) == 1
        assert active_sessions[0].session_id == active_session.session_id

    @pytest.mark.asyncio
    async def test_get_session_status(self):
        """Test getting session status information."""
        playlist_id = "playlist-123"
        session = await self.service.start_association_session(playlist_id)

        status = await self.service.get_session_status()

        assert len(status['active_sessions']) == 1
        session_info = status['active_sessions'][0]
        assert session_info['playlist_id'] == playlist_id
        assert session_info['state'] == 'LISTENING'

    @pytest.mark.asyncio
    async def test_concurrent_sessions_different_playlists(self):
        """Test multiple concurrent association sessions."""
        session1 = await self.service.start_association_session("playlist-123")
        session2 = await self.service.start_association_session("playlist-456")
        session3 = await self.service.start_association_session("playlist-789")

        active_sessions = await self.service.get_active_sessions()
        assert len(active_sessions) == 3

        playlist_ids = {s.playlist_id for s in active_sessions}
        assert playlist_ids == {"playlist-123", "playlist-456", "playlist-789"}

    @pytest.mark.asyncio
    async def test_tag_association_business_rules(self):
        """Test core business rules for tag associations."""
        tag_id = TagIdentifier("04f7eda4df6181")

        # Rule 1: One-to-one mapping (one tag, one playlist)
        session1 = await self.service.start_association_session("playlist-123")
        self.playlist_repository.update_nfc_tag_association.return_value = True

        result1 = await self.service.process_tag_detection(tag_id)
        assert result1['success'] is True

        # Rule 2: Attempting to associate same tag with different playlist should fail
        session2 = await self.service.start_association_session("playlist-456")
        result2 = await self.service.process_tag_detection(tag_id)
        assert result2['success'] is False
        assert result2['state'] == AssociationState.DUPLICATE

    @pytest.mark.asyncio
    async def test_repository_sync_failure_handling(self):
        """Test handling of playlist repository synchronization failures."""
        session = await self.service.start_association_session("playlist-123")
        self.playlist_repository.update_nfc_tag_association.return_value = False

        tag_identifier = TagIdentifier("04f7eda4df6181")
        result = await self.service.process_tag_detection(tag_identifier)

        # Should fail if repository sync fails
        assert result['success'] is False

        # Tag should still be stored in NFC repository
        stored_tag = await self.repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None


class TestNfcMemoryRepository:
    """Tests for NFC memory repository implementation."""

    def setup_method(self):
        """Setup test dependencies."""
        self.repository = NfcMemoryRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_tag(self):
        """Test saving and retrieving tags."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)
        tag.associate_playlist("playlist-123")

        await self.repository.save(tag)

        retrieved_tag = await self.repository.find_by_identifier(identifier)
        assert retrieved_tag is not None
        assert retrieved_tag.identifier == identifier
        assert retrieved_tag.associated_playlist_id == "playlist-123"

    @pytest.mark.asyncio
    async def test_find_by_playlist_id(self):
        """Test finding tags by associated playlist."""
        tag1 = NfcTag(TagIdentifier("tag001"))
        tag1.associate_playlist("playlist-123")

        tag2 = NfcTag(TagIdentifier("tag002"))
        tag2.associate_playlist("playlist-123")

        tag3 = NfcTag(TagIdentifier("tag003"))
        tag3.associate_playlist("playlist-456")

        await self.repository.save(tag1)
        await self.repository.save(tag2)
        await self.repository.save(tag3)

        playlist_123_tags = await self.repository.find_by_playlist_id("playlist-123")
        assert len(playlist_123_tags) == 2

        tag_ids = {str(tag.identifier) for tag in playlist_123_tags}
        assert tag_ids == {"tag001", "tag002"}

    @pytest.mark.asyncio
    async def test_remove_tag(self):
        """Test removing tags from repository."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        await self.repository.save(tag)
        assert await self.repository.find_by_identifier(identifier) is not None

        result = await self.repository.remove(identifier)
        assert result is True

        assert await self.repository.find_by_identifier(identifier) is None

    @pytest.mark.asyncio
    async def test_find_all_associated_tags(self):
        """Test finding all associated tags."""
        tag1 = NfcTag(TagIdentifier("tag001"))
        tag1.associate_playlist("playlist-123")

        tag2 = NfcTag(TagIdentifier("tag002"))  # Not associated

        tag3 = NfcTag(TagIdentifier("tag003"))
        tag3.associate_playlist("playlist-456")

        await self.repository.save(tag1)
        await self.repository.save(tag2)
        await self.repository.save(tag3)

        associated_tags = await self.repository.find_all_associated()
        assert len(associated_tags) == 2

        associated_ids = {str(tag.identifier) for tag in associated_tags}
        assert associated_ids == {"tag001", "tag003"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])