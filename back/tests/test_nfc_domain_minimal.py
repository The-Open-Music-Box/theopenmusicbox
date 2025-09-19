# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Minimal NFC domain tests based on actual implementation."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

from app.src.domain.nfc.entities.nfc_tag import NfcTag
from app.src.domain.nfc.entities.association_session import AssociationSession, SessionState
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.infrastructure.nfc.repositories.nfc_memory_repository import NfcMemoryRepository


class TestTagIdentifierValueObject:
    """Tests for TagIdentifier value object business rules."""

    def test_valid_tag_identifier_creation(self):
        """Test creating valid tag identifiers."""
        valid_identifiers = [
            "04f7eda4df6181",
            "AABBCCDD",
            "1234567890ABCDEF"
        ]

        for uid in valid_identifiers:
            identifier = TagIdentifier(uid)
            assert str(identifier) == uid.lower()

    def test_tag_identifier_equality(self):
        """Test equality comparison between identifiers."""
        id1 = TagIdentifier("04f7eda4df6181")
        id2 = TagIdentifier("04F7EDA4DF6181")  # Same but uppercase
        id3 = TagIdentifier("aabbccdd")

        assert id1 == id2  # Case insensitive
        assert id1 != id3  # Different values


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

        tag.associate_with_playlist(playlist_id)

        assert tag.associated_playlist_id == playlist_id
        assert tag.is_associated()

    def test_dissociate_playlist(self):
        """Test dissociating playlist from tag."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)
        tag.associate_with_playlist("playlist-123")

        tag.dissociate_from_playlist()

        assert tag.associated_playlist_id is None
        assert not tag.is_associated()

    def test_record_detection(self):
        """Test recording tag detection."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        before_detection = datetime.now()
        tag.mark_detected()
        after_detection = datetime.now()

        assert tag.detection_count == 1
        assert before_detection <= tag.last_detected_at.replace(tzinfo=None) <= after_detection

    def test_recently_detected(self):
        """Test recent detection logic."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        # Not detected yet
        assert not tag.is_recently_detected()

        # Just detected
        tag.mark_detected()
        assert tag.is_recently_detected()


class TestAssociationSessionEntity:
    """Tests for AssociationSession domain entity business logic."""

    def test_session_creation(self):
        """Test creating association session."""
        playlist_id = "playlist-456"
        timeout_seconds = 60

        session = AssociationSession(playlist_id, timeout_seconds=timeout_seconds)

        assert session.playlist_id == playlist_id
        assert session.state == SessionState.LISTENING
        assert not session.is_expired()
        assert session.detected_tag is None

    def test_session_state_transitions(self):
        """Test valid session state transitions."""
        session = AssociationSession("playlist-456", timeout_seconds=60)

        # Start in LISTENING state
        assert session.state == SessionState.LISTENING

        # Can transition to SUCCESS
        tag_id = TagIdentifier("tag-123")
        session.detect_tag(tag_id)
        session.mark_successful()
        assert session.state == SessionState.SUCCESS
        assert str(session.detected_tag) == "tag-123"

        # Create new session for other transitions
        session2 = AssociationSession("playlist-789", timeout_seconds=60)
        tag_id_2 = TagIdentifier("tag-456")
        session2.detect_tag(tag_id_2)
        session2.mark_duplicate("existing-playlist-123")
        assert session2.state == SessionState.DUPLICATE
        assert str(session2.detected_tag) == "tag-456"
        assert session2.conflict_playlist_id == "existing-playlist-123"

        # Test STOPPED state
        session3 = AssociationSession("playlist-012", timeout_seconds=60)
        session3.mark_stopped()
        assert session3.state == SessionState.STOPPED

        # Test TIMEOUT state
        session4 = AssociationSession("playlist-345", timeout_seconds=60)
        session4.mark_timeout()
        assert session4.state == SessionState.TIMEOUT

        # Test ERROR state
        session5 = AssociationSession("playlist-678", timeout_seconds=60)
        session5.mark_error("Test error message")
        assert session5.state == SessionState.ERROR
        assert session5.error_message == "Test error message"

    def test_session_serialization(self):
        """Test session serialization to dictionary."""
        session = AssociationSession("playlist-456", timeout_seconds=60)
        tag_id = TagIdentifier("tag-123")
        session.detect_tag(tag_id)
        session.mark_successful()

        data = session.to_dict()

        expected_keys = {
            'session_id', 'playlist_id', 'state', 'detected_tag',
            'started_at', 'timeout_at', 'remaining_seconds',
            'conflict_playlist_id', 'error_message'
        }
        assert set(data.keys()) == expected_keys
        assert data['playlist_id'] == "playlist-456"
        assert data['state'] == "success"
        assert data['detected_tag'] == "tag-123"


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
        tag.associate_with_playlist("playlist-123")

        await self.repository.save(tag)

        retrieved_tag = await self.repository.find_by_identifier(identifier)
        assert retrieved_tag is not None
        assert retrieved_tag.identifier == identifier
        assert retrieved_tag.associated_playlist_id == "playlist-123"

    @pytest.mark.asyncio
    async def test_find_by_playlist_id(self):
        """Test finding tags by associated playlist."""
        tag1 = NfcTag(TagIdentifier("tag001"))
        tag1.associate_with_playlist("playlist-123")

        tag2 = NfcTag(TagIdentifier("tag002"))
        tag2.associate_with_playlist("playlist-123")

        tag3 = NfcTag(TagIdentifier("tag003"))
        tag3.associate_with_playlist("playlist-456")

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])