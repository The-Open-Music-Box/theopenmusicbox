"""Test utilities for TheOpenMusicBox.

This module provides utility functions and classes to assist with
testing various components of the application.
"""

import asyncio
import uuid
from unittest.mock import MagicMock


class AsyncTestHelper:
    """Helper class for testing async code."""

    @staticmethod
    async def wait_for_condition(condition_func, timeout=1.0, interval=0.05):
        """Wait for a condition to become true.

        Args:
            condition_func: A function that returns True when the condition is met
            timeout: Maximum time to wait in seconds
            interval: Check interval in seconds

        Raises:
            TimeoutError: If the condition is not met within the timeout period
        """
        start_time = asyncio.get_event_loop().time()
        while not condition_func():
            await asyncio.sleep(interval)
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Condition not met within {timeout} seconds")


class MockHelpers:
    """Helper methods for creating common mocks."""

    @staticmethod
    def create_playlist(playlist_id=None, title="Test Playlist", track_count=2):
        """Create a mock playlist with the specified number of tracks.

        Args:
            playlist_id: Optional playlist ID (generated if not provided)
            title: Playlist title
            track_count: Number of tracks to include

        Returns:
            Dict representing a playlist with tracks
        """
        if playlist_id is None:
            playlist_id = str(uuid.uuid4())

        tracks = []
        for i in range(1, track_count + 1):
            tracks.append(
                {
                    "number": i,
                    "title": f"Track {i}",
                    "filename": f"track_{i}.mp3",
                    "duration": "3:00",
                    "artist": "Test Artist",
                    "album": "Test Album",
                    "play_counter": 0,
                }
            )

        return {
            "id": playlist_id,
            "title": title,
            "type": "playlist",
            "path": f"{title.lower().replace(' ', '_')}",
            "created_at": "2025-01-01T00:00:00Z",
            "tracks": tracks,
        }

    @staticmethod
    def create_mock_audio_player():
        """Create a mock audio player with common methods.

        Returns:
            MagicMock configured as an audio player
        """
        mock = MagicMock()
        mock.is_playing = True
        mock.is_paused = False
        mock.is_finished.return_value = False
        mock.current_track = MagicMock()
        mock.current_track.number = 1
        mock.current_track.title = "Test Track"
        return mock

    @staticmethod
    def create_mock_nfc_service():
        """Create a mock NFC service.

        Returns:
            MagicMock configured as an NFC service
        """
        mock = MagicMock()
        mock.is_listening.return_value = False
        mock.get_status.return_value = {"listening": False, "playlist_id": None}
        return mock


class EventCollector:
    """Collect events for testing asynchronous event-based code.

    This class helps test code that emits events asynchronously by
    collecting the events and providing methods to wait for them.
    """

    def __init__(self):
        """Initialize the event collector."""
        self.events = []
        self.event_received = asyncio.Event()

    def callback(self, event):
        """Callback to be used as an event handler.

        Args:
            event: The event data
        """
        self.events.append(event)
        self.event_received.set()

    async def wait_for_event(self, timeout=1.0):
        """Wait for an event to be received.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            The most recently received event

        Raises:
            asyncio.TimeoutError: If no event is received within the timeout
        """
        await asyncio.wait_for(self.event_received.wait(), timeout)
        self.event_received.clear()
        return self.events[-1]

    def clear(self):
        """Clear all collected events."""
        self.events.clear()
        self.event_received.clear()
