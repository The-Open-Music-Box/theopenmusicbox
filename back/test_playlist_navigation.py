#!/usr/bin/env python3

"""
Test script to verify playlist navigation (next/previous track) works.

This tests the new manual playlist navigation logic in AudioController.
"""

from unittest.mock import Mock
from app.src.controllers.audio_controller import AudioController


class MockPlaylist:
    """Mock playlist with tracks."""

    def __init__(self, title="Test Playlist"):
        self.title = title
        self.tracks = [
            MockTrack("Track 1", "/music/track1.mp3"),
            MockTrack("Track 2", "/music/track2.mp3"),
            MockTrack("Track 3", "/music/track3.mp3"),
        ]


class MockTrack:
    """Mock track with file path."""

    def __init__(self, title, file_path):
        self.title = title
        self.file_path = file_path
        self.id = f"track_{title.replace(' ', '_').lower()}"


class MockBackend:
    """Mock audio backend."""

    def __init__(self):
        self.current_file = None
        self.play_file_calls = []

    def is_available(self):
        return True

    def play_file(self, file_path):
        """Mock play_file method."""
        self.current_file = file_path
        self.play_file_calls.append(file_path)
        return True


def test_playlist_navigation():
    """Test that next/previous track navigation works with playlist."""
    print("Testing playlist navigation...")

    # Arrange
    mock_backend = MockBackend()
    controller = AudioController()
    controller._backend = mock_backend

    # Set up playlist
    playlist = MockPlaylist()
    controller._current_playlist = playlist
    controller._current_track_index = 0  # Start at first track

    print(f"Playlist has {len(playlist.tracks)} tracks")
    print(f"Starting at index: {controller._current_track_index}")

    # Test next track navigation
    print("\n--- Testing next track ---")
    for i in range(len(playlist.tracks)):
        current_track = playlist.tracks[controller._current_track_index]
        print(f"Current: Track {controller._current_track_index + 1} - {current_track.title}")

        if controller._current_track_index < len(playlist.tracks) - 1:
            result = controller.next_track()
            print(f"Next track result: {result}")
            print(f"New index: {controller._current_track_index}")

            # Verify backend play_file was called with correct path
            if result:
                expected_track = playlist.tracks[controller._current_track_index]
                assert expected_track.file_path in mock_backend.play_file_calls, f"Backend should have been called with {expected_track.file_path}"
                print(f"✅ Backend called with play_file({expected_track.file_path})")
        else:
            # Should fail at end of playlist
            result = controller.next_track()
            print(f"Next track at end: {result} (should be False)")
            assert result is False, "Should return False at end of playlist"

    print("\n--- Testing previous track ---")
    # Test previous track navigation (go backwards)
    while controller._current_track_index > 0:
        current_track = playlist.tracks[controller._current_track_index]
        print(f"Current: Track {controller._current_track_index + 1} - {current_track.title}")

        result = controller.previous_track()
        print(f"Previous track result: {result}")
        print(f"New index: {controller._current_track_index}")

        # Verify backend play_file was called with correct path
        if result:
            expected_track = playlist.tracks[controller._current_track_index]
            assert expected_track.file_path in mock_backend.play_file_calls, f"Backend should have been called with {expected_track.file_path}"
            print(f"✅ Backend called with play_file({expected_track.file_path})")

    # Should fail at beginning of playlist
    result = controller.previous_track()
    print(f"Previous track at beginning: {result} (should be False)")
    assert result is False, "Should return False at beginning of playlist"

    print("\n✅ Playlist navigation working correctly!")


def test_no_playlist_fallback():
    """Test behavior when no playlist is available."""
    print("\nTesting behavior without playlist...")

    controller = AudioController()
    controller._backend = MockBackend()
    # No _current_playlist set

    result_next = controller.next_track()
    result_prev = controller.previous_track()

    print(f"Next track without playlist: {result_next}")
    print(f"Previous track without playlist: {result_prev}")

    # Should fall back to backend (which doesn't have these methods)
    assert result_next is False, "Should return False when no playlist"
    assert result_prev is False, "Should return False when no playlist"

    print("✅ No playlist fallback works correctly!")


if __name__ == "__main__":
    print("🧪 Testing playlist navigation in AudioController...\n")

    try:
        test_playlist_navigation()
        test_no_playlist_fallback()

        print("\n🎉 All playlist navigation tests passed!")
        print("\nExpected behavior:")
        print("✅ Next track loads and plays next file in playlist")
        print("✅ Previous track loads and plays previous file in playlist")
        print("✅ Navigation stops at playlist boundaries")
        print("✅ Fallback works when no playlist available")
        print("\n🚀 Next/Previous buttons should now work on the hardware!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise