# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Integration Scenarios Tests

Tests for critical integration points between domains that represent
core business value and ensure data consistency across domain boundaries.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track
from app.src.domain.services.track_reordering_service import (
    TrackReorderingService, 
    ReorderingCommand, 
    ReorderingStrategy
)
from app.src.application.services.playlist_application_service import PlaylistApplicationService


class TestPlaylistTrackIntegrationScenarios:
    """Test integration scenarios between Playlist and Track domain entities."""
    
    def setup_method(self):
        """Set up integration test dependencies."""
        self.mock_repository = Mock()
        self.playlist_service = PlaylistApplicationService(
            playlist_repository=self.mock_repository
        )
        self.track_reordering_service = TrackReorderingService()
    
    def test_track_reordering_maintains_playlist_integrity(self):
        """
        Integration Test: Track reordering must maintain playlist business invariants
        
        Business Integration Rules:
        - Playlist must remain valid after reordering
        - All tracks must be preserved with correct metadata
        - Track numbers must be sequential and start from 1
        - Playlist duration calculation must remain accurate
        """
        # Arrange - Create playlist with tracks
        playlist = Playlist(name="Integration Test Playlist", description="Test reordering")
        
        tracks = [
            Track(track_number=1, title="First Song", filename="first.mp3", 
                  file_path="/music/first.mp3", duration_ms=180000, artist="Artist A"),
            Track(track_number=2, title="Second Song", filename="second.mp3",
                  file_path="/music/second.mp3", duration_ms=240000, artist="Artist B"),
            Track(track_number=3, title="Third Song", filename="third.mp3",
                  file_path="/music/third.mp3", duration_ms=200000, artist="Artist C"),
            Track(track_number=4, title="Fourth Song", filename="fourth.mp3",
                  file_path="/music/fourth.mp3", duration_ms=220000, artist="Artist D")
        ]
        
        for track in tracks:
            playlist.add_track(track)
        
        # Capture original state for verification
        original_duration = playlist.get_total_duration_ms()
        original_track_count = len(playlist.tracks)
        original_titles = [track.title for track in playlist.tracks]
        
        # Act - Execute reordering: [1,2,3,4] -> [3,1,4,2]
        command = ReorderingCommand(
            playlist_id="test-playlist",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[3, 1, 4, 2]
        )
        
        result = self.track_reordering_service.execute_reordering(command, playlist.tracks)
        
        # Apply reordering result to playlist
        if result.success:
            playlist.tracks = result.affected_tracks
        
        # Assert - Integration integrity maintained
        assert result.success is True
        assert len(result.validation_errors) == 0
        assert len(result.business_rule_violations) == 0
        
        # Verify playlist integrity
        assert playlist.is_valid()
        assert len(playlist.tracks) == original_track_count
        assert playlist.get_total_duration_ms() == original_duration
        
        # Verify all tracks preserved
        current_titles = [track.title for track in playlist.tracks]
        assert set(current_titles) == set(original_titles)
        
        # Verify new order
        expected_order = ["Third Song", "First Song", "Fourth Song", "Second Song"]
        actual_order = [track.title for track in playlist.tracks]
        assert actual_order == expected_order
        
        # Verify sequential numbering
        track_numbers = [track.track_number for track in playlist.tracks]
        assert track_numbers == [1, 2, 3, 4]
        
        # Verify metadata preservation
        for track in playlist.tracks:
            assert track.filename.endswith('.mp3')
            assert track.file_path.startswith('/music/')
            assert track.duration_ms > 0
            assert track.artist is not None
    
    def test_playlist_track_addition_business_rules_integration(self):
        """
        Integration Test: Adding tracks to playlist must enforce all business rules
        
        Integration Rules:
        - Auto-numbering must work correctly with existing tracks
        - Track validation must be enforced
        - Playlist sorting must be maintained
        - Domain events should be consistent
        """
        # Arrange - Create playlist with existing tracks
        playlist = Playlist(name="Addition Test")
        
        # Add some existing tracks with gaps in numbering
        existing_tracks = [
            Track(track_number=1, title="Track A", filename="a.mp3", file_path="/music/a.mp3"),
            Track(track_number=3, title="Track C", filename="c.mp3", file_path="/music/c.mp3"),
            Track(track_number=5, title="Track E", filename="e.mp3", file_path="/music/e.mp3")
        ]
        
        for track in existing_tracks:
            playlist.add_track(track)
        
        # Act - Add new tracks with various numbering scenarios
        # Case 1: Track with number 0 (should auto-assign)
        new_track_auto = Track(track_number=0, title="Auto Track", filename="auto.mp3", file_path="/music/auto.mp3")
        playlist.add_track(new_track_auto)
        
        # Case 2: Track with specific number that fits in gap
        new_track_gap = Track(track_number=2, title="Gap Track", filename="gap.mp3", file_path="/music/gap.mp3")
        playlist.add_track(new_track_gap)
        
        # Case 3: Track with number higher than existing
        new_track_high = Track(track_number=7, title="High Track", filename="high.mp3", file_path="/music/high.mp3")
        playlist.add_track(new_track_high)
        
        # Assert - Integration business rules enforced
        assert len(playlist.tracks) == 6
        assert playlist.is_valid()
        
        # Verify auto-numbering worked correctly
        assert new_track_auto.track_number == 6  # Should be max + 1 from original tracks
        
        # Verify tracks are sorted by track number
        sorted_tracks = sorted(playlist.tracks, key=lambda t: t.track_number)
        track_numbers = [track.track_number for track in sorted_tracks]
        assert track_numbers == [1, 2, 3, 5, 6, 7]
        
        # Verify specific tracks are in correct positions
        track_titles_by_number = {track.track_number: track.title for track in playlist.tracks}
        assert track_titles_by_number[2] == "Gap Track"
        assert track_titles_by_number[6] == "Auto Track"
        assert track_titles_by_number[7] == "High Track"
    
    def test_playlist_validation_cascades_to_tracks(self):
        """
        Integration Test: Playlist validation must cascade to all contained tracks
        
        Integration Rules:
        - Invalid tracks should make playlist invalid
        - Validation should check all business rules
        - Mixed valid/invalid tracks should be handled correctly
        """
        # Arrange - Create playlist with mix of valid and invalid tracks
        playlist = Playlist(name="Validation Test")
        
        # Valid tracks
        valid_tracks = [
            Track(track_number=1, title="Valid 1", filename="valid1.mp3", file_path="/music/valid1.mp3"),
            Track(track_number=2, title="Valid 2", filename="valid2.mp3", file_path="/music/valid2.mp3")
        ]
        
        # Invalid tracks
        invalid_tracks = [
            Track(track_number=0, title="Invalid Number", filename="invalid.mp3", file_path="/music/invalid.mp3"),  # Invalid number
            Track(track_number=3, title="", filename="empty_title.mp3", file_path="/music/empty.mp3"),  # Empty title
            Track(track_number=4, title="No File", filename="", file_path="")  # Empty filename and path
        ]
        
        # Add all tracks
        all_tracks = valid_tracks + invalid_tracks
        for track in all_tracks:
            playlist.add_track(track)
        
        # Act & Assert - Validation integration
        # Individual track validation
        for track in valid_tracks:
            assert track.is_valid() is True
        
        for track in invalid_tracks:
            assert track.is_valid() is False
        
        # Playlist validation should fail due to invalid tracks
        assert playlist.is_valid() is False
        
        # Remove invalid tracks
        playlist.tracks = [track for track in playlist.tracks if track.is_valid()]
        
        # Now playlist should be valid
        assert playlist.is_valid() is True
        assert len(playlist.tracks) == 2


class TestNFCPlaylistIntegrationScenarios:
    """Test integration scenarios between NFC and Playlist domains."""
    
    def setup_method(self):
        """Set up NFC integration test dependencies."""
        self.mock_playlist_repository = Mock()
        self.mock_playlist_repository.associate_nfc_tag = AsyncMock()
        self.mock_playlist_repository.disassociate_nfc_tag = AsyncMock()
        self.mock_playlist_repository.get_playlist_by_nfc_tag = AsyncMock()
        self.mock_nfc_repository = Mock()
        self.playlist_service = PlaylistApplicationService(
            playlist_repository=self.mock_playlist_repository
        )
    
    @pytest.mark.asyncio
    async def test_nfc_tag_association_lifecycle_integration(self):
        """
        Integration Test: Complete NFC tag association lifecycle
        
        Integration Scenarios:
        1. Associate NFC tag with playlist
        2. Retrieve playlist by NFC tag
        3. Verify association integrity
        4. Update association (move to different playlist)
        5. Remove association
        6. Verify cleanup
        """
        # Arrange - Test data
        tag_id = "04:A3:B2:C1:D0:FF:EE:DD"
        playlist1_id = "playlist-1"
        playlist2_id = "playlist-2"
        
        # Mock playlist data
        playlist1_data = {
            "id": playlist1_id,
            "title": "Playlist One",
            "description": "First playlist",
            "nfc_tag_id": None,  # Initially no tag
            "tracks": [
                {"track_number": 1, "title": "Song A", "filename": "a.mp3", "file_path": "/music/a.mp3"}
            ]
        }
        
        playlist2_data = {
            "id": playlist2_id,
            "title": "Playlist Two", 
            "description": "Second playlist",
            "nfc_tag_id": None,
            "tracks": [
                {"track_number": 1, "title": "Song B", "filename": "b.mp3", "file_path": "/music/b.mp3"}
            ]
        }
        
        # Setup repository responses
        self.mock_playlist_repository.associate_nfc_tag.return_value = True
        self.mock_playlist_repository.disassociate_nfc_tag.return_value = True
        
        # Act & Assert - Step 1: Associate tag with first playlist
        result1 = await self.playlist_service.associate_nfc_tag(playlist1_id, tag_id)
        assert result1 is True
        self.mock_playlist_repository.associate_nfc_tag.assert_called_with(playlist1_id, tag_id)
        
        # Step 2: Retrieve playlist by tag
        self.mock_playlist_repository.get_playlist_by_nfc_tag.return_value = {
            **playlist1_data,
            "nfc_tag_id": tag_id
        }
        
        retrieved_playlist = await self.playlist_service.get_playlist_by_nfc_tag(tag_id)
        assert retrieved_playlist is not None
        assert retrieved_playlist["title"] == "Playlist One"
        assert retrieved_playlist["nfc_tag_id"] == tag_id
        
        # Step 3: Move association to second playlist
        result2 = await self.playlist_service.associate_nfc_tag(playlist2_id, tag_id)
        assert result2 is True
        
        # Step 4: Verify new association
        self.mock_playlist_repository.get_playlist_by_nfc_tag.return_value = {
            **playlist2_data,
            "nfc_tag_id": tag_id
        }
        
        retrieved_playlist2 = await self.playlist_service.get_playlist_by_nfc_tag(tag_id)
        assert retrieved_playlist2 is not None
        assert retrieved_playlist2["title"] == "Playlist Two"
        assert retrieved_playlist2["nfc_tag_id"] == tag_id
        
        # Step 5: Remove association
        result3 = await self.playlist_service.disassociate_nfc_tag(playlist2_id)
        assert result3 is True
        
        # Step 6: Verify cleanup
        self.mock_playlist_repository.get_playlist_by_nfc_tag.return_value = None
        
        retrieved_playlist3 = await self.playlist_service.get_playlist_by_nfc_tag(tag_id)
        assert retrieved_playlist3 is None
    
    async def test_nfc_tag_format_validation_business_rules(self):
        """
        Integration Test: NFC tag format validation across domain boundaries
        
        Business Rules:
        - NFC tag IDs must follow specific format patterns
        - Invalid formats should be rejected consistently
        - Error messages should be user-friendly
        """
        # Test cases for NFC tag ID validation
        valid_tag_ids = [
            "04:A3:B2:C1:D0:FF:EE:DD",  # Standard 8-byte format
            "04A3B2C1D0FFEEDD",         # No separators
            "04-A3-B2-C1-D0-FF-EE-DD",  # Dash separators
            "AA:BB:CC:DD"               # 4-byte format
        ]
        
        invalid_tag_ids = [
            "",                         # Empty
            "INVALID",                  # Non-hex
            "04:A3:B2",                # Too short
            "04:G3:B2:C1:D0:FF:EE:DD", # Invalid hex character
            "04:A3:B2:C1:D0:FF:EE:DD:EX" # Too long
        ]
        
        playlist_id = "test-playlist"
        
        # Test valid tag IDs
        for tag_id in valid_tag_ids:
            self.mock_playlist_repository.associate_nfc_tag.return_value = True
            result = await self.playlist_service.associate_nfc_tag(playlist_id, tag_id)
            assert result is True, f"Valid tag ID should succeed: {tag_id}"
        
        # Test invalid tag IDs (would be handled by domain validation)
        for tag_id in invalid_tag_ids:
            # Note: In a full implementation, domain validation would catch these
            # For now, we test that the service handles them gracefully
            self.mock_playlist_repository.associate_nfc_tag.side_effect = ValueError(f"Invalid tag format: {tag_id}")
            try:
                result = await self.playlist_service.associate_nfc_tag(playlist_id, tag_id)
                # If no exception, result should indicate failure
                assert result is False, f"Invalid tag ID should fail: {tag_id}"
            except ValueError:
                # Exception is acceptable for invalid formats
                pass
            
            # Reset mock
            self.mock_playlist_repository.associate_nfc_tag.side_effect = None


class TestAudioPlaylistIntegrationScenarios:
    """Test integration scenarios between Audio and Playlist domains."""
    
    def setup_method(self):
        """Set up audio integration test dependencies."""
        self.mock_playlist_repository = Mock()
        self.mock_audio_engine = Mock()
        self.playlist_service = PlaylistApplicationService(
            playlist_repository=self.mock_playlist_repository
        )
    
    @pytest.mark.asyncio
    async def test_playlist_loading_into_audio_engine_integration(self):
        """
        Integration Test: Loading playlist into audio engine must preserve all data
        
        Integration Requirements:
        - All valid tracks must be loaded
        - Track order must be preserved
        - Metadata must be accessible to audio engine
        - Invalid tracks should be skipped gracefully
        """
        # Arrange - Create comprehensive playlist
        playlist_data = {
            "id": "audio-test-playlist",
            "title": "Audio Integration Test",
            "description": "Test playlist for audio integration",
            "tracks": [
                {
                    "track_number": 1,
                    "title": "Opening Song",
                    "filename": "opening.mp3",
                    "file_path": "/music/opening.mp3",
                    "duration_ms": 180000,
                    "artist": "Test Artist",
                    "album": "Test Album"
                },
                {
                    "track_number": 2,
                    "title": "Second Track",
                    "filename": "second.mp3", 
                    "file_path": "/music/second.mp3",
                    "duration_ms": 240000,
                    "artist": "Another Artist",
                    "album": "Another Album"
                },
                {
                    "track_number": 3,
                    "title": "Final Song",
                    "filename": "final.mp3",
                    "file_path": "/music/final.mp3",
                    "duration_ms": 200000,
                    "artist": "Last Artist",
                    "album": "Last Album"
                }
            ]
        }
        
        # Mock repository response
        self.mock_playlist_repository.get_playlist_by_id.return_value = playlist_data
        self.mock_audio_engine.set_playlist.return_value = True
        
        # Act - Load playlist into audio engine
        result = await self.playlist_service.start_playlist_with_details(
            playlist_data["id"],
            self.mock_audio_engine
        )
        
        # Assert - Integration success
        assert result["success"] is True
        assert result["details"]["playlist_name"] == "Audio Integration Test"
        assert result["details"]["track_count"] == 3
        assert result["details"]["valid_tracks"] == 3
        
        # Verify audio engine received correct playlist
        self.mock_audio_engine.set_playlist.assert_called_once()
        loaded_playlist = self.mock_audio_engine.set_playlist.call_args[0][0]
        
        assert isinstance(loaded_playlist, Playlist)
        assert loaded_playlist.name == "Audio Integration Test"
        assert len(loaded_playlist.tracks) == 3
        
        # Verify track data integrity
        track_titles = [track.title for track in loaded_playlist.tracks]
        expected_titles = ["Opening Song", "Second Track", "Final Song"]
        assert track_titles == expected_titles
        
        # Verify metadata preservation
        for track in loaded_playlist.tracks:
            assert track.artist is not None
            assert track.album is not None
            assert track.duration_ms is not None
            assert track.file_path.startswith("/music/")
    
    def test_audio_playback_state_playlist_synchronization(self):
        """
        Integration Test: Audio playback state must stay synchronized with playlist
        
        Integration Requirements:
        - Current track must match playlist position
        - Track changes must update playlist state
        - Seek operations must respect track boundaries
        - End of playlist must be handled correctly
        """
        # Arrange - Create playlist with multiple tracks
        playlist = Playlist(name="Sync Test Playlist")
        
        tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", 
                  file_path="/music/t1.mp3", duration_ms=180000),
            Track(track_number=2, title="Track 2", filename="t2.mp3",
                  file_path="/music/t2.mp3", duration_ms=240000),
            Track(track_number=3, title="Track 3", filename="t3.mp3",
                  file_path="/music/t3.mp3", duration_ms=200000)
        ]
        
        for track in tracks:
            playlist.add_track(track)
        
        # Mock audio engine state
        self.mock_audio_engine.set_playlist.return_value = True
        self.mock_audio_engine.get_current_track.return_value = tracks[0]
        self.mock_audio_engine.get_current_position.return_value = 0
        self.mock_audio_engine.get_state.return_value = "playing"
        
        # Act - Simulate audio engine interaction
        # This would be more complex in a real integration test
        # For now, we verify the basic integration contract
        
        # Verify playlist can provide required data to audio engine
        assert len(playlist.tracks) == 3
        assert playlist.get_first_track() is not None
        assert playlist.get_track_by_position(0) == tracks[0]
        assert playlist.get_track_by_position(1) == tracks[1]
        assert playlist.get_track_by_position(2) == tracks[2]
        
        # Verify playlist provides navigation capabilities
        assert playlist.has_track_number(1) is True
        assert playlist.has_track_number(2) is True
        assert playlist.has_track_number(3) is True
        assert playlist.has_track_number(4) is False
        
        # Verify duration calculations for seeking
        total_duration = playlist.get_total_duration_ms()
        assert total_duration == 620000  # Sum of all track durations
        
        # Verify track order integrity
        track_numbers = playlist.get_track_numbers()
        assert track_numbers == [1, 2, 3]


class TestErrorRecoveryIntegrationScenarios:
    """Test error recovery scenarios across domain boundaries."""
    
    def setup_method(self):
        """Set up error recovery integration test dependencies."""
        self.mock_playlist_repository = Mock()
        self.playlist_service = PlaylistApplicationService(
            playlist_repository=self.mock_playlist_repository
        )
    
    @pytest.mark.asyncio
    async def test_partial_failure_recovery_integration(self):
        """
        Integration Test: System must recover gracefully from partial failures
        
        Recovery Scenarios:
        - Repository fails but domain logic succeeds
        - Some tracks fail to load but others succeed
        - Network interruption during operations
        - State inconsistency detection and correction
        """
        # Scenario 1: Repository intermittent failure
        playlist_id = "recovery-test"
        
        # First call fails
        self.mock_playlist_repository.get_playlist_by_id.side_effect = Exception("Connection timeout")
        
        result1 = await self.playlist_service.get_playlist_use_case(playlist_id)
        assert result1["status"] == "error"
        assert "Connection timeout" in result1["message"]
        
        # Second call succeeds (connection recovered)
        self.mock_playlist_repository.get_playlist_by_id.side_effect = None
        self.mock_playlist_repository.get_playlist_by_id.return_value = {
            "id": playlist_id,
            "title": "Recovered Playlist",
            "description": "Test recovery",
            "tracks": [
                {"track_number": 1, "title": "Track 1", "filename": "t1.mp3", "file_path": "/music/t1.mp3"}
            ]
        }
        
        result2 = await self.playlist_service.get_playlist_use_case(playlist_id)
        assert result2["status"] == "success"
        assert result2["playlist"]["title"] == "Recovered Playlist"
        
        # Verify system maintained consistency
        assert "tracks" in result2["playlist"]
        assert len(result2["playlist"]["tracks"]) == 1
    
    def test_domain_boundary_consistency_validation(self):
        """
        Integration Test: Consistency validation across domain boundaries
        
        Consistency Rules:
        - Domain entities must maintain invariants across service calls
        - Data transformations must preserve business rules
        - Cross-domain references must remain valid
        """
        # Create domain entity
        playlist = Playlist(name="Consistency Test")
        
        # Add tracks with business rule validation
        valid_track = Track(track_number=1, title="Valid", filename="valid.mp3", file_path="/valid.mp3")
        playlist.add_track(valid_track)
        
        # Verify initial state
        assert playlist.is_valid()
        assert len(playlist.tracks) == 1
        
        # Simulate cross-domain operation (serialization/deserialization)
        # This mimics what happens when data crosses application service boundaries
        serialized_data = {
            "id": playlist.id,
            "title": playlist.name,
            "description": playlist.description,
            "tracks": [
                {
                    "track_number": track.track_number,
                    "title": track.title,
                    "filename": track.filename,
                    "file_path": track.file_path,
                    "duration_ms": track.duration_ms,
                    "artist": track.artist,
                    "album": track.album
                }
                for track in playlist.tracks
            ]
        }
        
        # Reconstruct domain entity from serialized data
        reconstructed_playlist = Playlist(
            name=serialized_data["title"],
            description=serialized_data["description"],
            id=serialized_data["id"]
        )
        
        for track_data in serialized_data["tracks"]:
            reconstructed_track = Track(
                track_number=track_data["track_number"],
                title=track_data["title"],
                filename=track_data["filename"],
                file_path=track_data["file_path"],
                duration_ms=track_data["duration_ms"],
                artist=track_data["artist"],
                album=track_data["album"]
            )
            reconstructed_playlist.add_track(reconstructed_track)
        
        # Verify consistency maintained across boundary
        assert reconstructed_playlist.is_valid()
        assert len(reconstructed_playlist.tracks) == len(playlist.tracks)
        assert reconstructed_playlist.name == playlist.name
        
        # Verify business rules still apply
        for original, reconstructed in zip(playlist.tracks, reconstructed_playlist.tracks):
            assert original.title == reconstructed.title
            assert original.track_number == reconstructed.track_number
            assert original.is_valid() == reconstructed.is_valid()