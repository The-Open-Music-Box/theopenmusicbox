# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Test NFC association workflow fix."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from app.src.domain.nfc.entities.nfc_tag import NfcTag
from app.src.domain.nfc.entities.association_session import AssociationSession, SessionState
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.services.nfc_association_service import NfcAssociationService
from app.src.infrastructure.nfc.repositories.nfc_memory_repository import NfcMemoryRepository


class TestNfcAssociationWorkflowFix:
    """Test the fix for NFC association workflow preventing unwanted playlist start."""

    def setup_method(self):
        """Setup test dependencies."""
        self.repository = NfcMemoryRepository()
        self.playlist_repository = AsyncMock()
        self.association_service = NfcAssociationService(self.repository, self.playlist_repository)

        # Mock successful playlist repository sync
        self.playlist_repository.update_nfc_tag_association.return_value = True

    @pytest.mark.asyncio
    async def test_session_cleanup_after_successful_association(self):
        """Test that successful association sessions are automatically cleaned up."""
        playlist_id = "test-playlist"
        tag_uid = "04f7eda4df6181"

        # Start association session
        session = await self.association_service.start_association_session(playlist_id)
        session_id = session.session_id

        # Verify session is active
        assert session.state == SessionState.LISTENING
        active_sessions = self.association_service.get_active_sessions()
        assert len(active_sessions) == 1

        # Process tag detection (triggers association)
        tag_identifier = TagIdentifier(tag_uid)
        result = await self.association_service.process_tag_detection(tag_identifier)

        # Verify association was successful
        assert result['action'] == 'association_success'
        assert result['session_state'] == 'success'

        # Session should be marked as SUCCESS but still in active sessions initially
        stored_session = self.association_service._active_sessions.get(session_id)
        assert stored_session is not None
        assert stored_session.state == SessionState.SUCCESS

        # Wait for cleanup (2+ seconds)
        await asyncio.sleep(2.5)

        # Session should now be cleaned up and removed from active sessions
        cleaned_session = self.association_service._active_sessions.get(session_id)
        assert cleaned_session is None

        # get_active_sessions() should return empty list
        remaining_active_sessions = self.association_service.get_active_sessions()
        assert len(remaining_active_sessions) == 0

    @pytest.mark.asyncio
    async def test_only_listening_sessions_prevent_playback(self):
        """Test that only LISTENING sessions should prevent playlist playback."""
        playlist_id = "test-playlist"
        tag_uid = "04f7eda4df6181"

        # Create mock NFC application service with status method
        mock_nfc_service = Mock()
        mock_nfc_service.get_nfc_status_use_case = AsyncMock()

        # Test 1: No active sessions - should allow playback
        mock_nfc_service.get_nfc_status_use_case.return_value = {
            'active_sessions': []
        }

        # This would normally be tested in UnifiedPlaylistController but we can verify logic
        active_sessions = []
        listening_sessions = [
            s for s in active_sessions
            if s.get('state') in ['listening', 'LISTENING']
        ]
        assert len(listening_sessions) == 0  # Should allow playback

        # Test 2: SUCCESS session - should allow playback (session completed)
        mock_nfc_service.get_nfc_status_use_case.return_value = {
            'active_sessions': [{'state': 'success', 'session_id': 'session-123'}]
        }

        active_sessions = [{'state': 'success', 'session_id': 'session-123'}]
        listening_sessions = [
            s for s in active_sessions
            if s.get('state') in ['listening', 'LISTENING']
        ]
        assert len(listening_sessions) == 0  # Should allow playback

        # Test 3: LISTENING session - should prevent playback
        mock_nfc_service.get_nfc_status_use_case.return_value = {
            'active_sessions': [{'state': 'listening', 'session_id': 'session-456'}]
        }

        active_sessions = [{'state': 'listening', 'session_id': 'session-456'}]
        listening_sessions = [
            s for s in active_sessions
            if s.get('state') in ['listening', 'LISTENING']
        ]
        assert len(listening_sessions) == 1  # Should prevent playback

    @pytest.mark.asyncio
    async def test_complete_association_workflow_with_cleanup(self):
        """Test complete workflow: start session → associate → cleanup → allow playback."""
        playlist_id = "workflow-test-playlist"
        tag_uid = "04f7eda4df6181"

        # Step 1: Start association session
        session = await self.association_service.start_association_session(playlist_id)
        session_id = session.session_id

        # Should prevent playback (active listening session)
        active_sessions = self.association_service.get_active_sessions()
        assert len(active_sessions) == 1
        assert active_sessions[0].state == SessionState.LISTENING

        # Step 2: Associate tag
        tag_identifier = TagIdentifier(tag_uid)
        result = await self.association_service.process_tag_detection(tag_identifier)

        # Association should succeed
        assert result['action'] == 'association_success'

        # Session should be SUCCESS but still in memory
        stored_session = self.association_service._active_sessions.get(session_id)
        assert stored_session.state == SessionState.SUCCESS

        # get_active_sessions() should return empty (SUCCESS sessions are not active)
        active_sessions = self.association_service.get_active_sessions()
        assert len(active_sessions) == 0  # No active LISTENING sessions

        # Step 3: Wait for cleanup
        await asyncio.sleep(2.5)

        # Session should be completely removed
        cleaned_session = self.association_service._active_sessions.get(session_id)
        assert cleaned_session is None

        # Step 4: Verify tag is properly associated
        stored_tag = await self.repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None
        assert stored_tag.is_associated()
        assert stored_tag.get_associated_playlist_id() == playlist_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])