# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""NFC domain tests based on actual implementation."""

import pytest
from datetime import datetime, timezone
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
            assert str(identifier) == uid  # No case conversion in actual implementation

    def test_tag_identifier_equality(self):
        """Test equality comparison between identifiers."""
        id1 = TagIdentifier("04f7eda4df6181")
        id2 = TagIdentifier("04f7eda4df6181")  # Same case
        id3 = TagIdentifier("aabbccdd")

        assert id1 == id2  # Same values
        assert id1 != id3  # Different values

    def test_tag_identifier_validation(self):
        """Test tag identifier validation."""
        # Valid identifiers should work
        valid_id = TagIdentifier("04f7eda4df6181")
        assert valid_id.is_valid()

        # Invalid identifiers should raise errors
        with pytest.raises(ValueError):
            TagIdentifier("")  # Empty

        with pytest.raises(ValueError):
            TagIdentifier("123")  # Too short

        with pytest.raises(ValueError):
            TagIdentifier("GHIJKLMN")  # Non-hex characters

    def test_tag_identifier_from_raw_data(self):
        """Test creating identifier from raw data."""
        raw = "04 f7 ed a4"
        identifier = TagIdentifier.from_raw_data(raw)
        assert str(identifier) == "04f7eda4"


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
        assert tag.get_associated_playlist_id() == playlist_id

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

        before_detection = datetime.now(timezone.utc)
        tag.mark_detected()
        after_detection = datetime.now(timezone.utc)

        assert tag.detection_count == 1
        assert before_detection <= tag.last_detected_at <= after_detection

    def test_recently_detected(self):
        """Test recent detection logic."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        # Not detected yet
        assert not tag.is_recently_detected()

        # Just detected
        tag.mark_detected()
        assert tag.is_recently_detected()

    def test_tag_equality(self):
        """Test tag equality based on identifier."""
        id1 = TagIdentifier("04f7eda4df6181")
        id2 = TagIdentifier("04f7eda4df6181")
        id3 = TagIdentifier("aabbccdd")

        tag1 = NfcTag(id1)
        tag2 = NfcTag(id2)
        tag3 = NfcTag(id3)

        assert tag1 == tag2  # Same identifier
        assert tag1 != tag3  # Different identifier


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
        assert session.timeout_seconds == timeout_seconds

    def test_session_validation(self):
        """Test session validation."""
        with pytest.raises(ValueError):
            AssociationSession("")  # Empty playlist ID

    def test_session_timeout_behavior(self):
        """Test session timeout calculation."""
        session = AssociationSession("playlist-456", timeout_seconds=1)

        # Initially not expired
        assert not session.is_expired()
        assert session.is_active()

        # Should expire after timeout
        import time
        time.sleep(1.1)
        assert session.is_expired()
        assert not session.is_active()

    def test_session_state_transitions(self):
        """Test valid session state transitions."""
        session = AssociationSession("playlist-456", timeout_seconds=60)

        # Start in LISTENING state
        assert session.state == SessionState.LISTENING

        # Can detect tag and mark successful
        tag_id = TagIdentifier("04f7eda4df6181")
        session.detect_tag(tag_id)
        session.mark_successful()
        assert session.state == SessionState.SUCCESS
        assert session.detected_tag == tag_id

        # Create new session for duplicate test
        session2 = AssociationSession("playlist-789", timeout_seconds=60)
        tag_id_2 = TagIdentifier("aabbccdd")
        session2.detect_tag(tag_id_2)
        session2.mark_duplicate("existing-playlist-123")
        assert session2.state == SessionState.DUPLICATE
        assert session2.detected_tag == tag_id_2
        assert session2.conflict_playlist_id == "existing-playlist-123"

        # Test other states
        session3 = AssociationSession("playlist-012", timeout_seconds=60)
        session3.mark_stopped()
        assert session3.state == SessionState.STOPPED

        session4 = AssociationSession("playlist-345", timeout_seconds=60)
        session4.mark_timeout()
        assert session4.state == SessionState.TIMEOUT

        session5 = AssociationSession("playlist-678", timeout_seconds=60)
        session5.mark_error("Test error message")
        assert session5.state == SessionState.ERROR
        assert session5.error_message == "Test error message"

    def test_session_serialization(self):
        """Test session serialization to dictionary."""
        session = AssociationSession("playlist-456", timeout_seconds=60)
        tag_id = TagIdentifier("04f7eda4df6181")
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
        assert data['detected_tag'] == "04f7eda4df6181"


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

        await self.repository.save_tag(tag)

        retrieved_tag = await self.repository.find_by_identifier(identifier)
        assert retrieved_tag is not None
        assert retrieved_tag.identifier == identifier
        assert retrieved_tag.associated_playlist_id == "playlist-123"

    @pytest.mark.asyncio
    async def test_find_by_playlist_id(self):
        """Test finding tags by associated playlist."""
        tag1 = NfcTag(TagIdentifier("04f7eda4df6181"))
        tag1.associate_with_playlist("playlist-123")

        tag2 = NfcTag(TagIdentifier("aabbccdd"))
        tag2.associate_with_playlist("playlist-456")

        await self.repository.save_tag(tag1)
        await self.repository.save_tag(tag2)

        # Find by first playlist
        found_tag = await self.repository.find_by_playlist_id("playlist-123")
        assert found_tag is not None
        assert str(found_tag.identifier) == "04f7eda4df6181"

        # Find by second playlist
        found_tag2 = await self.repository.find_by_playlist_id("playlist-456")
        assert found_tag2 is not None
        assert str(found_tag2.identifier) == "aabbccdd"

        # Non-existent playlist
        not_found = await self.repository.find_by_playlist_id("nonexistent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_delete_tag(self):
        """Test deleting tags from repository."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)

        await self.repository.save_tag(tag)
        assert await self.repository.find_by_identifier(identifier) is not None

        result = await self.repository.delete_tag(identifier)
        assert result is True

        assert await self.repository.find_by_identifier(identifier) is None

        # Deleting non-existent tag
        result2 = await self.repository.delete_tag(identifier)
        assert result2 is False

    def test_clear_all_tags(self):
        """Test clearing all tags."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)
        self.repository._tags[identifier.uid] = tag

        assert len(self.repository._tags) == 1
        self.repository.clear_all()
        assert len(self.repository._tags) == 0

    def test_get_all_tags(self):
        """Test getting all tags."""
        identifier = TagIdentifier("04f7eda4df6181")
        tag = NfcTag(identifier)
        self.repository._tags[identifier.uid] = tag

        all_tags = self.repository.get_all_tags()
        assert len(all_tags) == 1
        assert identifier.uid in all_tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])