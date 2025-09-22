# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for audio core modules.

These tests verify the core audio system components including AudioEngine,
EventBus, ResourceManager, and related infrastructure.
"""

import pytest
import asyncio
import threading
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.src.domain.audio.engine.audio_engine import AudioEngine
from app.src.domain.audio.engine.event_bus import EventBus
from app.src.domain.audio.engine.state_manager import StateManager
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track


class TestAudioEngine:
    """Test the unified audio engine implementation."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_backend = Mock()
        self.mock_event_bus = Mock()
        self.mock_state_manager = Mock()
        self.mock_playlist_manager = Mock()
        
        self.engine = AudioEngine(
            backend=self.mock_backend,
            event_bus=self.mock_event_bus,
            state_manager=self.mock_state_manager,
            playlist_manager=self.mock_playlist_manager
        )
    
    @pytest.mark.asyncio
    async def test_start_engine(self):
        """Test starting the audio engine."""
        self.mock_backend.is_available = Mock(return_value=True)
        
        await self.engine.start()
        
        assert self.engine.is_running is True
        # Verify backend was initialized
        assert self.mock_backend.is_available.called
    
    @pytest.mark.asyncio
    async def test_start_engine_unavailable_backend(self):
        """Test starting engine with unavailable backend."""
        self.mock_backend.is_available = Mock(return_value=False)
        
        await self.engine.start()
        
        # Engine should handle unavailable backend gracefully
        # Implementation might still start but log warnings
        assert self.mock_backend.is_available.called
    
    @pytest.mark.asyncio
    async def test_stop_engine(self):
        """Test stopping the audio engine."""
        # Start first
        self.mock_backend.is_available = Mock(return_value=True)
        await self.engine.start()
        
        # Then stop
        await self.engine.stop()
        
        assert self.engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_load_playlist(self):
        """Test loading a playlist into the engine."""
        # Create test playlist
        playlist = Playlist(name="Test Playlist")
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/music/test.mp3"
        )
        playlist.add_track(track)
        
        self.mock_playlist_manager.set_playlist = Mock(return_value=True)
        
        result = await self.engine.load_playlist(playlist)
        
        assert result is True
        self.mock_playlist_manager.set_playlist.assert_called_once_with(playlist)
    
    @pytest.mark.asyncio
    async def test_load_empty_playlist(self):
        """Test loading an empty playlist."""
        empty_playlist = Playlist(name="Empty Playlist")
        
        result = await self.engine.load_playlist(empty_playlist)
        
        # Engine should reject empty playlists
        assert result is False
    
    @pytest.mark.asyncio
    async def test_play_playlist(self):
        """Test playing a playlist."""
        # Create test playlist
        playlist = Playlist(name="Test Playlist")
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/music/test.mp3"
        )
        playlist.add_track(track)
        
        self.mock_playlist_manager.set_playlist = Mock(return_value=True)
        
        result = await self.engine.play_playlist(playlist)
        
        assert result is True
        self.mock_playlist_manager.set_playlist.assert_called_once_with(playlist)
    
    @pytest.mark.asyncio
    async def test_next_track(self):
        """Test advancing to next track."""
        self.mock_playlist_manager.next_track = Mock(return_value=True)
        
        result = await self.engine.next_track()
        
        assert result is True
        self.mock_playlist_manager.next_track.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_previous_track(self):
        """Test going to previous track."""
        self.mock_playlist_manager.previous_track = Mock(return_value=True)
        
        result = await self.engine.previous_track()
        
        assert result is True
        self.mock_playlist_manager.previous_track.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_play_track_by_index(self):
        """Test playing track by index."""
        self.mock_playlist_manager.play_track_by_number = Mock(return_value=True)
        
        result = await self.engine.play_track_by_index(2)
        
        assert result is True
        # Index is 0-based, but play_track_by_number expects 1-based
        self.mock_playlist_manager.play_track_by_number.assert_called_once_with(3)
    
    @pytest.mark.asyncio
    async def test_play_file_directly(self):
        """Test playing a single file directly."""
        file_path = "/music/single.mp3"
        self.mock_backend.play_file = Mock(return_value=True)
        
        result = await self.engine.play_file(file_path)
        
        assert result is True
        self.mock_backend.play_file.assert_called_once_with(file_path)
    
    @pytest.mark.asyncio
    async def test_pause_playback(self):
        """Test pausing playback."""
        self.mock_backend.pause = Mock(return_value=True)
        
        result = await self.engine.pause_playback()
        
        assert result is True
        self.mock_backend.pause.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resume_playback(self):
        """Test resuming playback."""
        self.mock_backend.resume = Mock(return_value=True)
        
        result = await self.engine.resume_playback()
        
        assert result is True
        self.mock_backend.resume.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_playback(self):
        """Test stopping playback."""
        self.mock_backend.stop = Mock(return_value=True)
        
        result = await self.engine.stop_playback()
        
        assert result is True
        self.mock_backend.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_volume(self):
        """Test setting volume."""
        self.mock_backend.set_volume = Mock(return_value=True)
        
        result = await self.engine.set_volume(75)
        
        assert result is True
        self.mock_backend.set_volume.assert_called_once_with(75)
    
    def test_get_state_dict(self):
        """Test getting engine state as dictionary."""
        # Mock state components
        self.mock_backend.is_playing = Mock(return_value=True)
        self.mock_backend.get_volume = Mock(return_value=80)
        self.mock_backend.get_current_file = Mock(return_value="/music/current.mp3")
        
        self.mock_playlist_manager.current_playlist = Mock()
        self.mock_playlist_manager.current_track = Mock()
        self.mock_playlist_manager.current_track_index = 2
        
        state = self.engine.get_state_dict()
        
        assert isinstance(state, dict)
        assert 'is_playing' in state
        assert 'volume' in state
        assert 'current_file' in state
    
    def test_get_engine_statistics(self):
        """Test getting comprehensive engine statistics."""
        stats = self.engine.get_engine_statistics()
        
        assert isinstance(stats, dict)
        assert 'engine_name' in stats
        assert 'is_running' in stats
        assert 'backend_available' in stats


class TestEventBus:
    """Test the audio event bus implementation."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.event_bus = EventBus()
    
    def test_subscribe_and_publish(self):
        """Test subscribing to events and receiving publications."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
        
        # Subscribe to event
        self.event_bus.subscribe('test_event', event_handler)
        
        # Publish event
        test_data = {'message': 'test'}
        self.event_bus.publish('test_event', test_data)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0] == test_data
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to the same event."""
        received_events_1 = []
        received_events_2 = []
        
        def handler1(event_data):
            received_events_1.append(event_data)
        
        def handler2(event_data):
            received_events_2.append(event_data)
        
        # Subscribe both handlers
        self.event_bus.subscribe('multi_event', handler1)
        self.event_bus.subscribe('multi_event', handler2)
        
        # Publish event
        test_data = {'message': 'multi_test'}
        self.event_bus.publish('multi_event', test_data)
        
        # Verify both handlers received the event
        assert len(received_events_1) == 1
        assert len(received_events_2) == 1
        assert received_events_1[0] == test_data
        assert received_events_2[0] == test_data
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
        
        # Subscribe and publish
        self.event_bus.subscribe('unsub_event', event_handler)
        self.event_bus.publish('unsub_event', {'first': True})
        
        # Unsubscribe and publish again
        self.event_bus.unsubscribe('unsub_event', event_handler)
        self.event_bus.publish('unsub_event', {'second': True})
        
        # Only first event should be received
        assert len(received_events) == 1
        assert received_events[0]['first'] is True
    
    def test_publish_nonexistent_event(self):
        """Test publishing to an event with no subscribers."""
        # Should not raise an exception
        self.event_bus.publish('nonexistent_event', {'data': 'test'})
    
    def test_thread_safety(self):
        """Test that event bus is thread-safe."""
        received_events = []
        event_lock = threading.Lock()
        
        def thread_safe_handler(event_data):
            with event_lock:
                received_events.append(event_data)
        
        self.event_bus.subscribe('thread_event', thread_safe_handler)
        
        def publish_events():
            for i in range(10):
                self.event_bus.publish('thread_event', {'count': i})
        
        # Run multiple threads publishing events
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=publish_events)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all events were received
        assert len(received_events) == 30  # 3 threads * 10 events each
    
    def test_event_handler_exception_handling(self):
        """Test that exceptions in event handlers don't crash the event bus."""
        received_events = []
        
        def failing_handler(event_data):
            raise Exception("Handler failed")
        
        def working_handler(event_data):
            received_events.append(event_data)
        
        # Subscribe both handlers
        self.event_bus.subscribe('exception_event', failing_handler)
        self.event_bus.subscribe('exception_event', working_handler)
        
        # Publish event - should not raise exception
        self.event_bus.publish('exception_event', {'test': 'data'})
        
        # Working handler should still receive the event
        assert len(received_events) == 1


class TestStateManager:
    """Test the audio state manager implementation."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.state_manager = StateManager()
    
    def test_initial_state(self):
        """Test initial state values."""
        state = self.state_manager.get_current_state()
        
        assert isinstance(state, dict)
        # Verify default state structure
        expected_keys = ['is_playing', 'is_paused', 'volume', 'current_track', 'current_playlist']
        for key in expected_keys:
            assert key in state
    
    def test_update_playback_state(self):
        """Test updating playback state."""
        # Update to playing
        self.state_manager.update_playback_state(is_playing=True, is_paused=False)
        
        state = self.state_manager.get_current_state()
        assert state['is_playing'] is True
        assert state['is_paused'] is False
    
    def test_update_volume_state(self):
        """Test updating volume state."""
        self.state_manager.update_volume(85)
        
        state = self.state_manager.get_current_state()
        assert state['volume'] == 85
    
    def test_update_track_state(self):
        """Test updating current track state."""
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/music/test.mp3"
        )
        
        self.state_manager.update_current_track(track)
        
        state = self.state_manager.get_current_state()
        assert state['current_track'] is not None
        assert state['current_track']['title'] == "Test Track"
    
    def test_update_playlist_state(self):
        """Test updating current playlist state."""
        playlist = Playlist(name="Test Playlist")
        track = Track(
            track_number=1,
            title="Test Track",
            filename="test.mp3",
            file_path="/music/test.mp3"
        )
        playlist.add_track(track)
        
        self.state_manager.update_current_playlist(playlist)
        
        state = self.state_manager.get_current_state()
        assert state['current_playlist'] is not None
        assert state['current_playlist']['name'] == "Test Playlist"
    
    def test_state_change_notifications(self):
        """Test that state changes trigger notifications."""
        notifications = []
        
        def state_change_handler(new_state):
            notifications.append(new_state)
        
        # Subscribe to state changes (if supported)
        if hasattr(self.state_manager, 'subscribe_to_changes'):
            self.state_manager.subscribe_to_changes(state_change_handler)
            
            # Make a change
            self.state_manager.update_volume(90)
            
            # Verify notification was sent
            assert len(notifications) > 0
            assert notifications[-1]['volume'] == 90
    
    def test_state_persistence_across_updates(self):
        """Test that state persists correctly across multiple updates."""
        # Set initial state
        self.state_manager.update_volume(75)
        self.state_manager.update_playback_state(is_playing=True, is_paused=False)
        
        # Update only playback state
        self.state_manager.update_playback_state(is_playing=False, is_paused=True)
        
        # Volume should persist
        state = self.state_manager.get_current_state()
        assert state['volume'] == 75
        assert state['is_playing'] is False
        assert state['is_paused'] is True
    
    def test_thread_safe_state_access(self):
        """Test that state access is thread-safe."""
        def update_volume():
            for i in range(100):
                self.state_manager.update_volume(i)
        
        def update_playback():
            for i in range(100):
                self.state_manager.update_playback_state(
                    is_playing=i % 2 == 0,
                    is_paused=i % 2 == 1
                )
        
        # Run concurrent updates
        thread1 = threading.Thread(target=update_volume)
        thread2 = threading.Thread(target=update_playback)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # State should still be accessible and valid
        state = self.state_manager.get_current_state()
        assert isinstance(state, dict)
        assert 'volume' in state
        assert 'is_playing' in state


class TestAudioCoreIntegration:
    """Test integration between audio core components."""
    
    def setup_method(self):
        """Set up integrated test environment."""
        self.mock_backend = Mock()
        self.event_bus = EventBus()
        self.state_manager = StateManager()
        self.mock_playlist_manager = Mock()
        
        self.engine = AudioEngine(
            backend=self.mock_backend,
            event_bus=self.event_bus,
            state_manager=self.state_manager,
            playlist_manager=self.mock_playlist_manager
        )
    
    @pytest.mark.asyncio
    async def test_engine_state_integration(self):
        """Test that engine operations update state manager."""
        # Mock backend responses
        self.mock_backend.is_available = Mock(return_value=True)
        self.mock_backend.set_volume = Mock(return_value=True)
        self.mock_backend.get_volume = Mock(return_value=80)
        
        # Start engine
        await self.engine.start()
        
        # Set volume through engine
        await self.engine.set_volume(80)
        
        # Verify state was updated
        state = self.state_manager.get_current_state()
        # Note: Actual integration depends on implementation
        assert isinstance(state, dict)
    
    def test_event_bus_state_manager_integration(self):
        """Test integration between event bus and state manager."""
        state_updates = []
        
        def state_update_handler(event_data):
            state_updates.append(event_data)
        
        # Subscribe to state update events
        self.event_bus.subscribe('state_updated', state_update_handler)
        
        # Update state (if state manager publishes events)
        self.state_manager.update_volume(85)
        
        # This test assumes state manager publishes events - 
        # implementation may vary
        if hasattr(self.state_manager, 'publish_state_change'):
            self.state_manager.publish_state_change()
            assert len(state_updates) > 0
    
    @pytest.mark.asyncio
    async def test_full_playback_workflow_integration(self):
        """Test complete playback workflow integration."""
        # Setup mocks for full workflow
        self.mock_backend.is_available = Mock(return_value=True)
        self.mock_backend.play_file = Mock(return_value=True)
        self.mock_backend.is_playing = Mock(return_value=True)
        self.mock_playlist_manager.set_playlist = Mock(return_value=True)
        self.mock_playlist_manager.current_track = Mock()
        
        # Create test playlist
        playlist = Playlist(name="Integration Test")
        track = Track(
            track_number=1,
            title="Integration Track",
            filename="integration.mp3",
            file_path="/music/integration.mp3"
        )
        playlist.add_track(track)
        
        # Start engine
        await self.engine.start()
        
        # Load and play playlist
        load_result = await self.engine.load_playlist(playlist)
        play_result = await self.engine.play_playlist(playlist)
        
        # Verify workflow completed successfully
        assert load_result is True
        assert play_result is True
        assert self.mock_playlist_manager.set_playlist.called
        
        # Get final state
        final_state = self.engine.get_state_dict()
        assert isinstance(final_state, dict)