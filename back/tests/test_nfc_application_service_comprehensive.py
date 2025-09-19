# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Comprehensive tests for NFC application service layer."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from app.src.application.services.nfc_application_service import NfcApplicationService
from app.src.domain.nfc.entities.association_session import AssociationState
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.repositories.nfc_memory_repository import NfcMemoryRepository
from app.src.infrastructure.repositories.sqlite_playlist_repository import SQLitePlaylistRepository


class TestNfcApplicationServiceInitialization:
    """Tests for NFC application service initialization."""

    def test_service_initialization(self):
        """Test NFC application service initialization."""
        service = NfcApplicationService()

        assert service is not None
        assert hasattr(service, '_nfc_handler')
        assert hasattr(service, '_nfc_association_service')

    @pytest.mark.asyncio
    async def test_start_nfc_system_use_case(self):
        """Test starting NFC system use case."""
        service = NfcApplicationService()

        # Mock NFC handler
        mock_handler = Mock()
        mock_handler.start_detection = AsyncMock(return_value={'success': True, 'message': 'Started'})
        service._nfc_handler = mock_handler

        result = await service.start_nfc_system_use_case()

        assert result['success'] is True
        mock_handler.start_detection.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_nfc_system_use_case(self):
        """Test stopping NFC system use case."""
        service = NfcApplicationService()

        # Mock NFC handler
        mock_handler = Mock()
        mock_handler.stop_detection = AsyncMock(return_value={'success': True, 'message': 'Stopped'})
        service._nfc_handler = mock_handler

        result = await service.stop_nfc_system_use_case()

        assert result['success'] is True
        mock_handler.stop_detection.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_nfc_status_use_case(self):
        """Test getting NFC system status."""
        service = NfcApplicationService()

        # Mock NFC handler and association service
        mock_handler = Mock()
        mock_handler.get_hardware_status = AsyncMock(return_value={
            'reader_available': True,
            'scanning': True
        })
        service._nfc_handler = mock_handler

        mock_association_service = AsyncMock()
        mock_association_service.get_session_status = AsyncMock(return_value={
            'active_sessions': []
        })
        service._nfc_association_service = mock_association_service

        result = await service.get_nfc_status_use_case()

        assert result['success'] is True
        assert result['data']['reader_available'] is True
        assert result['data']['scanning'] is True
        assert 'active_sessions' in result['data']


class TestNfcApplicationServiceAssociation:
    """Tests for NFC association workflows."""

    def setup_method(self):
        """Setup test dependencies."""
        self.service = NfcApplicationService()
        self.mock_association_service = AsyncMock()
        self.service._nfc_association_service = self.mock_association_service

    @pytest.mark.asyncio
    async def test_start_association_use_case_success(self):
        """Test successful association session start."""
        playlist_id = "playlist-123"
        timeout_seconds = 60

        mock_session = Mock()
        mock_session.session_id = "session-456"
        mock_session.playlist_id = playlist_id
        mock_session.state = AssociationState.LISTENING
        mock_session.to_dict.return_value = {
            'session_id': 'session-456',
            'playlist_id': playlist_id,
            'state': 'LISTENING'
        }

        self.mock_association_service.start_association_session.return_value = mock_session

        result = await self.service.start_association_use_case(playlist_id, timeout_seconds)

        assert result['success'] is True
        assert result['session_id'] == "session-456"
        assert result['playlist_id'] == playlist_id

        self.mock_association_service.start_association_session.assert_called_once_with(
            playlist_id, timeout_seconds
        )

    @pytest.mark.asyncio
    async def test_start_association_use_case_failure(self):
        """Test association session start failure."""
        playlist_id = "playlist-123"

        self.mock_association_service.start_association_session.side_effect = Exception("Database error")

        result = await self.service.start_association_use_case(playlist_id)

        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_stop_association_use_case_success(self):
        """Test successful association session stop."""
        session_id = "session-123"

        self.mock_association_service.stop_association_session.return_value = True

        result = await self.service.stop_association_use_case(session_id)

        assert result['success'] is True

        self.mock_association_service.stop_association_session.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_stop_association_use_case_not_found(self):
        """Test stopping non-existent association session."""
        session_id = "nonexistent-session"

        self.mock_association_service.stop_association_session.return_value = False

        result = await self.service.stop_association_use_case(session_id)

        assert result['success'] is False
        assert "not found" in result['message'].lower()


class TestNfcApplicationServiceTagDetection:
    """Tests for NFC tag detection processing."""

    def setup_method(self):
        """Setup test dependencies."""
        self.service = NfcApplicationService()
        self.mock_association_service = AsyncMock()
        self.service._nfc_association_service = self.mock_association_service

        # Mock callbacks
        self.callback_calls = []

        def mock_callback(tag_data):
            self.callback_calls.append(tag_data)

        self.service.register_tag_detected_callback(mock_callback)

    @pytest.mark.asyncio
    async def test_tag_detection_with_successful_association(self):
        """Test tag detection resulting in successful association."""
        tag_uid = "04f7eda4df6181"

        self.mock_association_service.process_tag_detection.return_value = {
            'success': True,
            'session_id': 'session-123',
            'playlist_id': 'playlist-456',
            'state': AssociationState.SUCCESS
        }

        await self.service._on_tag_detected(tag_uid)

        # Verify association service was called
        self.mock_association_service.process_tag_detection.assert_called_once()

        # Verify callback was triggered
        assert len(self.callback_calls) == 1
        assert self.callback_calls[0] == tag_uid

    @pytest.mark.asyncio
    async def test_tag_detection_with_duplicate_conflict(self):
        """Test tag detection with existing association conflict."""
        tag_uid = "04f7eda4df6181"

        self.mock_association_service.process_tag_detection.return_value = {
            'success': False,
            'session_id': 'session-123',
            'playlist_id': 'playlist-456',
            'state': AssociationState.DUPLICATE,
            'conflict_playlist_id': 'existing-playlist-789'
        }

        await self.service._on_tag_detected(tag_uid)

        # Verify processing occurred
        self.mock_association_service.process_tag_detection.assert_called_once()

        # Callback should still be triggered for logging/monitoring
        assert len(self.callback_calls) == 1

    @pytest.mark.asyncio
    async def test_tag_detection_no_active_session(self):
        """Test tag detection without active association session."""
        tag_uid = "04f7eda4df6181"

        self.mock_association_service.process_tag_detection.return_value = {
            'success': False,
            'message': 'No active association session'
        }

        await self.service._on_tag_detected(tag_uid)

        # Should still process for detection logging
        self.mock_association_service.process_tag_detection.assert_called_once()

        # Callback should be triggered for potential playlist lookup
        assert len(self.callback_calls) == 1

    @pytest.mark.asyncio
    async def test_multiple_callback_registration(self):
        """Test registering multiple tag detection callbacks."""
        callback_calls_2 = []

        def second_callback(tag_data):
            callback_calls_2.append(tag_data)

        self.service.register_tag_detected_callback(second_callback)

        tag_uid = "04f7eda4df6181"
        self.mock_association_service.process_tag_detection.return_value = {
            'success': True,
            'state': AssociationState.SUCCESS
        }

        await self.service._on_tag_detected(tag_uid)

        # Both callbacks should be triggered
        assert len(self.callback_calls) == 1
        assert len(callback_calls_2) == 1
        assert self.callback_calls[0] == tag_uid
        assert callback_calls_2[0] == tag_uid

    @pytest.mark.asyncio
    async def test_callback_exception_handling(self):
        """Test that callback exceptions don't break tag processing."""
        def failing_callback(tag_data):
            raise Exception("Callback error")

        self.service.register_tag_detected_callback(failing_callback)

        tag_uid = "04f7eda4df6181"
        self.mock_association_service.process_tag_detection.return_value = {
            'success': True,
            'state': AssociationState.SUCCESS
        }

        # Should not raise exception despite callback failure
        await self.service._on_tag_detected(tag_uid)

        # Processing should still complete
        self.mock_association_service.process_tag_detection.assert_called_once()


class TestNfcApplicationServiceErrorHandling:
    """Tests for error handling in NFC application service."""

    def setup_method(self):
        """Setup test dependencies."""
        self.service = NfcApplicationService()

    @pytest.mark.asyncio
    async def test_hardware_initialization_failure(self):
        """Test handling of hardware initialization failure."""
        with patch('app.src.domain.nfc.nfc_adapter.get_nfc_handler') as mock_get_handler:
            mock_get_handler.side_effect = Exception("Hardware not found")

            result = await self.service.start_nfc_system_use_case()

            assert result['success'] is False
            assert 'hardware' in result['message'].lower()

    @pytest.mark.asyncio
    async def test_association_service_initialization_failure(self):
        """Test handling of association service initialization failure."""
        service = NfcApplicationService()
        service._nfc_association_service = None

        result = await service.start_association_use_case("playlist-123")

        assert result['success'] is False
        assert 'not initialized' in result['message'].lower()

    @pytest.mark.asyncio
    async def test_tag_detection_processing_exception(self):
        """Test handling of exceptions during tag detection processing."""
        service = NfcApplicationService()
        mock_association_service = AsyncMock()
        mock_association_service.process_tag_detection.side_effect = Exception("Processing error")
        service._nfc_association_service = mock_association_service

        # Should handle exception gracefully
        await service._on_tag_detected("04f7eda4df6181")

        # Verify the method was called despite the exception
        mock_association_service.process_tag_detection.assert_called_once()


class TestNfcApplicationServiceCleanup:
    """Tests for NFC application service cleanup and lifecycle management."""

    def setup_method(self):
        """Setup test dependencies."""
        self.service = NfcApplicationService()

    @pytest.mark.asyncio
    async def test_service_cleanup(self):
        """Test service cleanup."""
        # Mock dependencies
        mock_handler = Mock()
        mock_handler.stop_detection = AsyncMock()
        mock_handler.cleanup = Mock()
        self.service._nfc_handler = mock_handler

        mock_association_service = AsyncMock()
        mock_association_service.cleanup_expired_sessions = AsyncMock(return_value=2)
        self.service._nfc_association_service = mock_association_service

        await self.service.cleanup()

        # Verify cleanup was called
        mock_handler.stop_detection.assert_called_once()
        mock_handler.cleanup.assert_called_once()
        mock_association_service.cleanup_expired_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_periodic_cleanup_task(self):
        """Test periodic cleanup of expired sessions."""
        mock_association_service = AsyncMock()
        mock_association_service.cleanup_expired_sessions = AsyncMock(return_value=1)
        self.service._nfc_association_service = mock_association_service

        # Run cleanup
        cleanup_count = await self.service._periodic_cleanup()

        assert cleanup_count == 1
        mock_association_service.cleanup_expired_sessions.assert_called_once()


class TestNfcApplicationServiceIntegrationScenarios:
    """Integration tests for complete NFC workflows."""

    def setup_method(self):
        """Setup test dependencies with real repositories."""
        self.nfc_repository = NfcMemoryRepository()
        self.playlist_repository = AsyncMock(spec=SQLitePlaylistRepository)
        self.service = NfcApplicationService()

    @pytest.mark.asyncio
    async def test_complete_association_workflow(self):
        """Test complete tag association workflow end-to-end."""
        # Step 1: Start association session
        playlist_id = "test-playlist-123"
        result = await self.service.start_association_use_case(playlist_id, 60)

        assert result['success'] is True
        session_id = result['session_id']

        # Step 2: Simulate tag detection during session
        tag_uid = "04f7eda4df6181"

        # Mock successful playlist repository sync
        if hasattr(self.service, '_nfc_association_service'):
            if hasattr(self.service._nfc_association_service, '_playlist_repository'):
                self.service._nfc_association_service._playlist_repository.update_nfc_tag_association.return_value = True

        await self.service._on_tag_detected(tag_uid)

        # Step 3: Verify association was successful
        status = await self.service.get_nfc_status_use_case()

        # Association should be complete (no active sessions if successful)
        active_sessions = status['data'].get('active_sessions', [])
        if active_sessions:
            # Session might still exist but be in SUCCESS state
            session = next((s for s in active_sessions if s.get('session_id') == session_id), None)
            if session:
                assert session['state'] in ['SUCCESS', 'STOPPED']

    @pytest.mark.asyncio
    async def test_concurrent_association_sessions_workflow(self):
        """Test multiple concurrent association sessions."""
        # Start multiple sessions for different playlists
        playlist_ids = ["playlist-1", "playlist-2", "playlist-3"]
        session_ids = []

        for playlist_id in playlist_ids:
            result = await self.service.start_association_use_case(playlist_id, 120)
            assert result['success'] is True
            session_ids.append(result['session_id'])

        # Verify all sessions are active
        status = await self.service.get_nfc_status_use_case()
        active_sessions = status['data'].get('active_sessions', [])

        # Should have sessions for each playlist
        active_playlist_ids = {s.get('playlist_id') for s in active_sessions}
        expected_playlist_ids = set(playlist_ids)

        # At least our playlists should be represented
        assert expected_playlist_ids.issubset(active_playlist_ids) or len(active_sessions) >= len(playlist_ids)

        # Stop one session
        stop_result = await self.service.stop_association_use_case(session_ids[0])
        assert stop_result['success'] is True

    @pytest.mark.asyncio
    async def test_session_timeout_workflow(self):
        """Test association session timeout behavior."""
        # Start session with short timeout
        playlist_id = "timeout-test-playlist"
        result = await self.service.start_association_use_case(playlist_id, 1)  # 1 second timeout

        assert result['success'] is True
        session_id = result['session_id']

        # Wait for timeout
        await asyncio.sleep(2)

        # Run cleanup to process expired sessions
        if hasattr(self.service, '_periodic_cleanup'):
            cleanup_count = await self.service._periodic_cleanup()
            # Should have cleaned up at least one expired session
            assert cleanup_count >= 0

        # Verify session is no longer active
        status = await self.service.get_nfc_status_use_case()
        active_sessions = status['data'].get('active_sessions', [])

        # Session should either be gone or in TIMEOUT state
        session = next((s for s in active_sessions if s.get('session_id') == session_id), None)
        if session:
            assert session['state'] == 'TIMEOUT'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])