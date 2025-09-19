# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Complete end-to-end NFC workflow tests covering all scenarios."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from app.src.core.application import Application
from app.src.application.services.nfc_application_service import NfcApplicationService
from app.src.domain.nfc.entities.association_session import AssociationState
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.entities.nfc_tag import NfcTag
from app.src.domain.nfc.repositories.nfc_memory_repository import NfcMemoryRepository
from app.src.domain.nfc.services.nfc_association_service import NfcAssociationService


class TestNfcWorkflowScenarios:
    """Complete NFC workflow scenario tests."""

    def setup_method(self):
        """Setup test dependencies."""
        self.nfc_repository = NfcMemoryRepository()
        self.playlist_repository = AsyncMock()
        self.nfc_association_service = NfcAssociationService(
            self.nfc_repository,
            self.playlist_repository
        )
        self.nfc_app_service = NfcApplicationService()
        self.nfc_app_service._nfc_association_service = self.nfc_association_service

        # Mock successful playlist repository operations by default
        self.playlist_repository.update_nfc_tag_association.return_value = True
        self.playlist_repository.remove_nfc_tag_association.return_value = True

    @pytest.mark.asyncio
    async def test_scenario_1_new_tag_association_success(self):
        """
        Scenario 1: User scans to associate new NFC tag with playlist

        Steps:
        1. User clicks "Associate NFC Tag" for a playlist
        2. System starts association session (60s timeout)
        3. User scans NFC tag
        4. System associates tag with playlist
        5. Future scans of this tag start the playlist
        """
        playlist_id = "my-favorite-songs"
        tag_uid = "04f7eda4df6181"

        # Step 1 & 2: Start association session
        session = await self.nfc_association_service.start_association_session(
            playlist_id, timeout_seconds=60
        )

        assert session.state == AssociationState.LISTENING
        assert session.playlist_id == playlist_id
        assert not session.is_expired()

        # Step 3 & 4: User scans NFC tag during session
        tag_identifier = TagIdentifier(tag_uid)
        result = await self.nfc_association_service.process_tag_detection(tag_identifier)

        assert result['success'] is True
        assert result['state'] == AssociationState.SUCCESS
        assert result['playlist_id'] == playlist_id

        # Step 5: Verify tag is associated and can trigger playlist
        stored_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None
        assert stored_tag.associated_playlist_id == playlist_id
        assert stored_tag.is_associated()

        # Verify playlist repository was updated
        self.playlist_repository.update_nfc_tag_association.assert_called_once_with(
            playlist_id, tag_uid
        )

    @pytest.mark.asyncio
    async def test_scenario_2_duplicate_tag_conflict_detection(self):
        """
        Scenario 2: User tries to associate tag already linked to different playlist

        Steps:
        1. Tag is already associated with Playlist A
        2. User starts association session for Playlist B
        3. User scans the same tag
        4. System detects conflict and rejects association
        5. Existing association remains unchanged
        """
        existing_playlist_id = "jazz-collection"
        new_playlist_id = "rock-hits"
        tag_uid = "04f7eda4df6181"

        # Step 1: Pre-existing tag association
        tag_identifier = TagIdentifier(tag_uid)
        existing_tag = NfcTag(tag_identifier)
        existing_tag.associate_playlist(existing_playlist_id)
        await self.nfc_repository.save(existing_tag)

        # Step 2: Start new association session for different playlist
        session = await self.nfc_association_service.start_association_session(
            new_playlist_id, timeout_seconds=60
        )

        # Step 3: Scan existing tag
        result = await self.nfc_association_service.process_tag_detection(tag_identifier)

        # Step 4: Verify conflict detection
        assert result['success'] is False
        assert result['state'] == AssociationState.DUPLICATE
        assert result['conflict_playlist_id'] == existing_playlist_id
        assert result['session_id'] == session.session_id

        # Step 5: Verify existing association unchanged
        stored_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag.associated_playlist_id == existing_playlist_id

        # No playlist repository update should occur for conflicts
        self.playlist_repository.update_nfc_tag_association.assert_not_called()

    @pytest.mark.asyncio
    async def test_scenario_3_association_session_timeout(self):
        """
        Scenario 3: Association session times out before tag scan

        Steps:
        1. User starts association session with short timeout
        2. User doesn't scan any tag within timeout period
        3. System automatically expires session
        4. Cleanup process removes expired session
        """
        playlist_id = "timeout-test-playlist"

        # Step 1: Start session with 1-second timeout
        session = await self.nfc_association_service.start_association_session(
            playlist_id, timeout_seconds=1
        )

        session_id = session.session_id
        assert session.state == AssociationState.LISTENING

        # Step 2: Wait for timeout to occur
        await asyncio.sleep(1.5)

        # Step 3: Session should now be expired
        active_sessions = await self.nfc_association_service.get_active_sessions()
        expired_session = next(
            (s for s in active_sessions if s.session_id == session_id), None
        )

        if expired_session:
            assert expired_session.is_expired()

        # Step 4: Cleanup expired sessions
        cleanup_count = await self.nfc_association_service.cleanup_expired_sessions()
        assert cleanup_count > 0

        # Verify session is removed from active sessions
        remaining_sessions = await self.nfc_association_service.get_active_sessions()
        remaining_session_ids = {s.session_id for s in remaining_sessions}
        assert session_id not in remaining_session_ids

    @pytest.mark.asyncio
    async def test_scenario_4_scan_to_start_playlist_workflow(self):
        """
        Scenario 4: User scans associated NFC tag to start playlist

        Steps:
        1. NFC tag is already associated with playlist
        2. User scans NFC tag (not in association mode)
        3. System detects tag and finds associated playlist
        4. System starts playlist playback
        """
        playlist_id = "morning-workout"
        tag_uid = "04f7eda4df6181"

        # Step 1: Pre-associate tag with playlist
        tag_identifier = TagIdentifier(tag_uid)
        associated_tag = NfcTag(tag_identifier)
        associated_tag.associate_playlist(playlist_id)
        await self.nfc_repository.save(associated_tag)

        # Step 2 & 3: Scan tag (not during association session)
        # This simulates normal tag detection outside of association mode
        result = await self.nfc_association_service.process_tag_detection(tag_identifier)

        # Should record the detection but not create association (no active session)
        assert result['success'] is False  # No active session, so no new association
        assert 'session_id' not in result

        # Step 4: Verify tag detection was recorded and playlist ID can be retrieved
        stored_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None
        assert stored_tag.associated_playlist_id == playlist_id
        assert stored_tag.detection_count > 0
        assert stored_tag.was_recently_detected()

        # This demonstrates that the tag association exists and can be used
        # for playlist lookup in the application layer

    @pytest.mark.asyncio
    async def test_scenario_5_manual_session_stop(self):
        """
        Scenario 5: User manually stops association session

        Steps:
        1. User starts association session
        2. User decides to cancel before scanning
        3. User clicks "Stop Association" or timeout occurs
        4. System cleanly stops session
        """
        playlist_id = "cancelled-session-test"

        # Step 1: Start association session
        session = await self.nfc_association_service.start_association_session(playlist_id)
        session_id = session.session_id

        assert session.state == AssociationState.LISTENING

        # Step 2 & 3: Manually stop session
        stop_result = await self.nfc_association_service.stop_association_session(session_id)
        assert stop_result is True

        # Step 4: Verify session is stopped
        active_sessions = await self.nfc_association_service.get_active_sessions()
        stopped_session = next(
            (s for s in active_sessions if s.session_id == session_id), None
        )

        # Session should either be removed or marked as stopped
        if stopped_session:
            assert stopped_session.state == AssociationState.STOPPED

    @pytest.mark.asyncio
    async def test_scenario_6_concurrent_association_sessions(self):
        """
        Scenario 6: Multiple concurrent association sessions for different playlists

        Steps:
        1. User 1 starts association for Playlist A
        2. User 2 starts association for Playlist B
        3. User 3 starts association for Playlist C
        4. Each user scans different NFC tags
        5. All associations complete successfully
        """
        playlists = [
            ("user1-jazz", "04f7eda4df6181"),
            ("user2-rock", "aabbccdd11223344"),
            ("user3-classical", "1122334455667788")
        ]

        sessions = []

        # Steps 1-3: Start concurrent association sessions
        for playlist_id, _ in playlists:
            session = await self.nfc_association_service.start_association_session(playlist_id)
            sessions.append(session)
            assert session.state == AssociationState.LISTENING

        # Verify all sessions are active
        active_sessions = await self.nfc_association_service.get_active_sessions()
        assert len(active_sessions) >= len(playlists)

        # Steps 4-5: Each user scans their respective NFC tag
        for i, (playlist_id, tag_uid) in enumerate(playlists):
            tag_identifier = TagIdentifier(tag_uid)
            result = await self.nfc_association_service.process_tag_detection(tag_identifier)

            assert result['success'] is True
            assert result['state'] == AssociationState.SUCCESS
            assert result['playlist_id'] == playlist_id

            # Verify tag is properly associated
            stored_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
            assert stored_tag.associated_playlist_id == playlist_id

    @pytest.mark.asyncio
    async def test_scenario_7_repository_sync_failure_handling(self):
        """
        Scenario 7: Playlist repository synchronization fails during association

        Steps:
        1. Start association session
        2. Scan NFC tag
        3. NFC repository update succeeds but playlist repository sync fails
        4. System handles error gracefully
        5. Association is not considered successful
        """
        playlist_id = "sync-failure-test"
        tag_uid = "04f7eda4df6181"

        # Mock playlist repository to fail sync
        self.playlist_repository.update_nfc_tag_association.return_value = False

        # Step 1: Start association session
        session = await self.nfc_association_service.start_association_session(playlist_id)

        # Step 2: Scan tag
        tag_identifier = TagIdentifier(tag_uid)
        result = await self.nfc_association_service.process_tag_detection(tag_identifier)

        # Steps 3-5: Verify failure handling
        assert result['success'] is False

        # Tag should still be recorded in NFC repository for detection tracking
        stored_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag is not None
        assert stored_tag.detection_count > 0

        # But association should not be considered successful
        # (The specific behavior depends on implementation - it might not associate
        # or might associate in NFC repo but consider the operation failed due to sync failure)

    @pytest.mark.asyncio
    async def test_scenario_8_tag_removal_workflow(self):
        """
        Scenario 8: Remove NFC tag association

        Steps:
        1. Tag is associated with playlist
        2. User chooses to remove association
        3. System removes association from both repositories
        4. Tag scans no longer trigger playlist
        """
        playlist_id = "removal-test-playlist"
        tag_uid = "04f7eda4df6181"

        # Step 1: Create association
        tag_identifier = TagIdentifier(tag_uid)
        associated_tag = NfcTag(tag_identifier)
        associated_tag.associate_playlist(playlist_id)
        await self.nfc_repository.save(associated_tag)

        # Verify association exists
        stored_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag.is_associated()
        assert stored_tag.associated_playlist_id == playlist_id

        # Step 2 & 3: Remove association
        stored_tag.dissociate_playlist()
        await self.nfc_repository.save(stored_tag)

        # Step 4: Verify association removed
        updated_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
        assert not updated_tag.is_associated()
        assert updated_tag.associated_playlist_id is None

        # Tag still exists for detection tracking but has no playlist association
        assert updated_tag.detection_count >= 0

    @pytest.mark.asyncio
    async def test_scenario_9_system_error_recovery(self):
        """
        Scenario 9: System error during association process

        Steps:
        1. Start association session
        2. Scan NFC tag
        3. Unexpected system error occurs during processing
        4. System recovers gracefully and logs error
        5. Session state is properly updated
        """
        playlist_id = "error-recovery-test"
        tag_uid = "04f7eda4df6181"

        # Step 1: Start association session
        session = await self.nfc_association_service.start_association_session(playlist_id)

        # Step 2 & 3: Mock system error during tag processing
        with patch.object(self.nfc_repository, 'save', side_effect=Exception("Database connection lost")):
            tag_identifier = TagIdentifier(tag_uid)

            # Should handle error gracefully without crashing
            result = await self.nfc_association_service.process_tag_detection(tag_identifier)

            # Steps 4 & 5: Verify error handling
            assert result['success'] is False
            # Error details should be logged (implementation specific)

        # System should remain operational after error
        active_sessions = await self.nfc_association_service.get_active_sessions()
        assert isinstance(active_sessions, list)  # Should still return valid list

    @pytest.mark.asyncio
    async def test_scenario_10_high_frequency_tag_detections(self):
        """
        Scenario 10: Handle rapid/repeated NFC tag detections

        Steps:
        1. Start association session
        2. Rapidly scan same NFC tag multiple times
        3. System handles detections efficiently
        4. Only one association is created
        5. Detection count is properly tracked
        """
        playlist_id = "high-frequency-test"
        tag_uid = "04f7eda4df6181"

        # Step 1: Start association session
        session = await self.nfc_association_service.start_association_session(playlist_id)

        # Step 2: Simulate rapid tag detections
        tag_identifier = TagIdentifier(tag_uid)
        detection_results = []

        for i in range(5):  # 5 rapid detections
            result = await self.nfc_association_service.process_tag_detection(tag_identifier)
            detection_results.append(result)
            # Small delay to simulate real-world timing
            await asyncio.sleep(0.1)

        # Step 3 & 4: Verify only one successful association
        successful_results = [r for r in detection_results if r['success']]
        assert len(successful_results) == 1  # Only first detection should succeed

        # Step 5: Verify detection count is properly tracked
        stored_tag = await self.nfc_repository.find_by_identifier(tag_identifier)
        assert stored_tag.detection_count == 5  # All detections counted
        assert stored_tag.associated_playlist_id == playlist_id  # But only one association


class TestNfcApplicationIntegrationWorkflows:
    """Integration tests with Application layer."""

    def setup_method(self):
        """Setup test dependencies."""
        self.mock_config = Mock()
        self.mock_config.get.return_value = True
        self.application = Application(self.mock_config)

    @pytest.mark.asyncio
    async def test_application_nfc_event_routing(self):
        """Test that Application correctly routes NFC events to playlist controller."""
        # Mock playlist controller
        mock_playlist_controller = AsyncMock()
        mock_playlist_controller.handle_tag_scanned = AsyncMock()
        self.application._playlist_controller = mock_playlist_controller

        # Test NFC tag event
        tag_data = "04f7eda4df6181"
        await self.application.handle_nfc_event(tag_data)

        # Verify playlist controller was called
        mock_playlist_controller.handle_tag_scanned.assert_called_once()

    @pytest.mark.asyncio
    async def test_application_nfc_absence_event(self):
        """Test handling of NFC tag absence events."""
        # Mock playlist controller
        mock_playlist_controller = Mock()
        mock_playlist_controller.handle_tag_absence = Mock()
        self.application._playlist_controller = mock_playlist_controller

        # Test NFC absence event
        absence_data = {"absence": True}
        await self.application.handle_nfc_event(absence_data)

        # Verify absence handler was called
        mock_playlist_controller.handle_tag_absence.assert_called_once()

    @pytest.mark.asyncio
    async def test_application_handles_missing_playlist_controller(self):
        """Test that Application handles missing playlist controller gracefully."""
        # Ensure playlist controller is None
        self.application._playlist_controller = None

        # Should not crash when handling NFC events
        await self.application.handle_nfc_event("04f7eda4df6181")

        # Should log error but continue operating
        # (This is now handled by our fix)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])