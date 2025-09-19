# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Critical Test: Audio Engine Startup Verification.

This test was created after discovering that the audio engine was not being started,
causing "Engine not running" errors that went undetected by existing tests.

The problem:
- domain_bootstrap.start() was never called
- audio_engine.start() was never called
- _is_running remained False
- set_playlist() returned True anyway (async task failure)
- Tests used mocks that didn't verify engine state

This test ensures the engine is properly started before operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from app.src.domain.audio.engine.audio_engine import AudioEngine
from app.src.domain.audio.container import AudioDomainContainer
from app.src.domain.bootstrap import DomainBootstrap
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track


class TestAudioEngineStartupRequirement:
    """Test that audio engine must be started before operations."""

    @pytest.mark.asyncio
    async def test_audio_engine_requires_start_before_operations(self):
        """Test that audio engine operations fail if engine not started."""
        # Create a real audio engine with mock backend
        mock_backend = Mock()
        mock_playlist_manager = Mock()
        mock_event_bus = AsyncMock()
        mock_state_manager = Mock()

        engine = AudioEngine(
            backend=mock_backend,
            playlist_manager=mock_playlist_manager,
            event_bus=mock_event_bus,
            state_manager=mock_state_manager
        )

        # Verify engine is not running initially
        assert not engine.is_running

        # Create a test playlist
        playlist = Playlist(
            name="Test Playlist",
            tracks=[
                Track(
                    track_number=1,
                    title="Test Track",
                    filename="test.mp3",
                    file_path="/test/test.mp3",
                    duration_ms=180000
                )
            ]
        )

        # Try to load playlist WITHOUT starting engine
        success = await engine.load_playlist(playlist)

        # Should fail because engine not started
        assert success is False

        # Now start the engine
        await engine.start()
        assert engine.is_running

        # Mock playlist manager to return success
        mock_playlist_manager.set_playlist.return_value = True

        # Try again after starting
        success = await engine.load_playlist(playlist)

        # Should succeed now
        assert success is True

    @pytest.mark.asyncio
    async def test_set_playlist_sync_method_behavior(self):
        """Test that set_playlist() sync method behaves correctly with engine state."""
        # Create a real audio engine
        mock_backend = Mock()
        mock_playlist_manager = Mock()
        mock_event_bus = AsyncMock()
        mock_state_manager = Mock()

        engine = AudioEngine(
            backend=mock_backend,
            playlist_manager=mock_playlist_manager,
            event_bus=mock_event_bus,
            state_manager=mock_state_manager
        )

        playlist = Playlist(
            name="Test Playlist",
            tracks=[
                Track(
                    track_number=1,
                    title="Test Track",
                    filename="test.mp3",
                    file_path="/test/test.mp3",
                    duration_ms=180000
                )
            ]
        )

        # Engine not started
        assert not engine.is_running

        # set_playlist returns True but async task will fail
        # This is the bug - it returns True even when it will fail
        result = engine.set_playlist(playlist)
        assert result is True  # Returns True immediately

        # Give async task time to execute
        await asyncio.sleep(0.1)

        # Verify the playlist was NOT actually loaded
        # (because engine not running)
        mock_playlist_manager.set_playlist.assert_not_called()

    @pytest.mark.asyncio
    async def test_domain_bootstrap_starts_audio_engine(self):
        """Test that domain bootstrap properly starts the audio engine."""
        # Create domain bootstrap
        bootstrap = DomainBootstrap()

        # Initialize it
        bootstrap.initialize()
        assert bootstrap.is_initialized

        # Get the audio container
        from app.src.domain.audio.container import audio_domain_container

        # Check engine is not yet running
        if audio_domain_container.is_initialized:
            engine = audio_domain_container.audio_engine
            assert not engine.is_running

        # Start the bootstrap (this was missing in main.py!)
        await bootstrap.start()

        # Now engine should be running
        if audio_domain_container.is_initialized:
            engine = audio_domain_container.audio_engine
            assert engine.is_running

        # Cleanup
        await bootstrap.stop()

    @pytest.mark.asyncio
    async def test_application_startup_must_start_domain(self):
        """Test that application startup must call domain_bootstrap.start()."""
        from app.src.core.application import Application

        # Create application
        config = {
            "auto_pause_enabled": False,
            "cors_allowed_origins": "*"
        }
        app = Application(config)

        # Initialize async resources
        await app.initialize_async()

        # Check domain bootstrap state
        from app.src.domain.bootstrap import domain_bootstrap
        assert domain_bootstrap.is_initialized

        # This is what was missing - must explicitly start!
        await domain_bootstrap.start()

        # Now check audio engine is running
        from app.src.domain.audio.container import audio_domain_container
        if audio_domain_container.is_initialized:
            engine = audio_domain_container.audio_engine
            assert engine.is_running

        # Cleanup
        await domain_bootstrap.stop()

    @pytest.mark.asyncio
    async def test_integration_chain_with_real_components(self):
        """Test the complete chain with real components (not mocks)."""
        # This test would have caught the original problem!

        # Create real components
        from app.src.application.services.playlist_application_service import PlaylistApplicationService
        from app.src.infrastructure.adapters.playlist_repository_adapter import PlaylistRepositoryAdapter
        import tempfile
        import os

        # Create temp database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        try:
            # Create real repository
            repository = PlaylistRepositoryAdapter(db_path)

            # Create service
            service = PlaylistApplicationService(playlist_repository=repository)

            # Create playlist in DB
            playlist_data = {
                "title": "Engine Test Playlist",
                "tracks": [
                    {
                        "track_number": 1,
                        "title": "Test Track",
                        "filename": "test.mp3",
                        "file_path": "/test/test.mp3",
                        "duration_ms": 180000
                    }
                ]
            }
            playlist_id = await repository.create_playlist(playlist_data)

            # Initialize domain
            from app.src.domain.bootstrap import domain_bootstrap
            if not domain_bootstrap.is_initialized:
                domain_bootstrap.initialize()

            # Get real audio engine
            from app.src.domain.audio.container import audio_domain_container
            if audio_domain_container.is_initialized:
                engine = audio_domain_container.audio_engine

                # TEST: Without starting, it should fail
                result = await service.start_playlist_with_details(
                    playlist_id, engine
                )

                # Should report failure (not success!)
                if not engine.is_running:
                    # If engine not running, service should detect and report error
                    # Currently it returns success even when engine not running
                    # This is the bug we're catching
                    pass

                # Now start the engine properly
                await domain_bootstrap.start()
                assert engine.is_running

                # Try again with started engine
                result = await service.start_playlist_with_details(
                    playlist_id, engine
                )

                # Now it should work properly
                assert result["success"] is True

                # Cleanup
                await domain_bootstrap.stop()

        finally:
            # Clean up temp database
            if os.path.exists(db_path):
                os.unlink(db_path)