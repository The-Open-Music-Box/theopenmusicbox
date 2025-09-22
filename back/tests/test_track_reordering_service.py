# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for TrackReorderingService domain service.

This test suite ensures 100% coverage of the track reordering business logic,
including all business rules, edge cases, and error scenarios.
"""

import pytest
from typing import List

from app.src.domain.data.models.track import Track
from app.src.domain.data.models.playlist import Playlist
from app.src.domain.services.track_reordering_service import (
    TrackReorderingService,
    ReorderingStrategy,
    ReorderingCommand,
    ReorderingResult
)


class TestTrackReorderingServiceBusinessRules:
    """Test business rules and validation logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TrackReorderingService()
        self.sample_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
            Track(track_number=3, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", id="track3"),
        ]
    
    def test_validate_empty_playlist_error(self):
        """Test business rule: cannot reorder empty playlist."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[1, 2, 3]
        )
        
        errors = self.service.validate_reordering_command(command, [])
        
        assert len(errors) == 1
        assert "Cannot reorder tracks in empty playlist" in errors[0]
    
    def test_validate_negative_track_numbers_error(self):
        """Test business rule: track numbers must be positive."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[-1, 0, 2]
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        # Should have multiple errors: positive validation + non-existent tracks
        assert len(errors) >= 1
        error_text = " ".join(errors)
        assert "Track numbers must be positive: [-1, 0]" in error_text
    
    def test_validate_duplicate_track_numbers_error(self):
        """Test business rule: no duplicate track numbers allowed."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[1, 2, 2, 3, 3]
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        # Should have multiple errors: duplicates + count mismatch for bulk reorder
        assert len(errors) >= 1
        error_text = " ".join(errors)
        assert "Duplicate track numbers not allowed: {2, 3}" in error_text
    
    def test_validate_non_existent_track_numbers_error(self):
        """Test business rule: track numbers must exist in playlist."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[1, 5, 9]
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        assert len(errors) == 1
        assert "Track numbers do not exist in playlist: [5, 9]" in errors[0]
    
    def test_validate_bulk_reorder_count_mismatch_error(self):
        """Test business rule: bulk reorder must include all tracks."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[1, 2]  # Missing track 3
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        assert len(errors) == 1
        assert "Bulk reorder must include all tracks. Expected 3, got 2" in errors[0]
    
    def test_validate_target_positions_count_mismatch_error(self):
        """Test business rule: target positions must match track numbers count."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.MOVE_TO_POSITION,
            track_numbers=[1, 2],
            target_positions=[3]  # Count mismatch
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        assert len(errors) == 1
        assert "Target positions count must match track numbers count" in errors[0]
    
    def test_validate_invalid_target_positions_error(self):
        """Test business rule: target positions must be within valid range."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.MOVE_TO_POSITION,
            track_numbers=[1, 2],
            target_positions=[0, 5]  # Invalid positions for 3-track playlist
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        assert len(errors) == 1
        assert "Invalid target positions (must be 1-3): [0, 5]" in errors[0]
    
    def test_validate_multiple_errors_combined(self):
        """Test multiple validation errors are collected."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[-1, 2, 2, 5]  # Negative, duplicate, non-existent, wrong count
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        assert len(errors) == 4
        # Check that all error types are present
        error_text = " ".join(errors)
        assert "Track numbers must be positive" in error_text
        assert "Duplicate track numbers not allowed" in error_text
        assert "Track numbers do not exist in playlist" in error_text
        assert "Bulk reorder must include all tracks" in error_text
    
    def test_validate_valid_command_no_errors(self):
        """Test valid command passes validation."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[3, 1, 2]
        )
        
        errors = self.service.validate_reordering_command(command, self.sample_tracks)
        
        assert len(errors) == 0


class TestTrackReorderingServiceCalculations:
    """Test order calculation logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TrackReorderingService()
        self.sample_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
            Track(track_number=3, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", id="track3"),
            Track(track_number=4, title="Track 4", filename="t4.mp3", file_path="/music/t4.mp3", id="track4"),
        ]
    
    def test_calculate_bulk_reorder_new_order(self):
        """Test bulk reorder calculation."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[3, 1, 4, 2]
        )
        
        new_order = self.service.calculate_new_order(command, self.sample_tracks)
        
        assert new_order == [3, 1, 4, 2]
    
    def test_calculate_swap_tracks_order(self):
        """Test swap tracks calculation."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.SWAP_TRACKS,
            track_numbers=[2, 4]
        )
        
        new_order = self.service.calculate_new_order(command, self.sample_tracks)
        
        # Should swap positions of tracks 2 and 4
        assert new_order == [1, 4, 3, 2]
    
    def test_calculate_swap_tracks_invalid_count_error(self):
        """Test swap strategy validation: requires exactly 2 tracks."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.SWAP_TRACKS,
            track_numbers=[1, 2, 3]  # Too many tracks for swap
        )
        
        with pytest.raises(ValueError, match="Swap strategy requires exactly 2 track numbers"):
            self.service.calculate_new_order(command, self.sample_tracks)
    
    def test_calculate_move_to_position_bulk_fallback(self):
        """Test move to position strategy fallback to bulk reorder."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.MOVE_TO_POSITION,
            track_numbers=[4, 3, 2, 1]  # All tracks specified
        )
        
        new_order = self.service.calculate_new_order(command, self.sample_tracks)
        
        # Should use bulk reorder logic when all tracks specified
        assert new_order == [4, 3, 2, 1]
    
    def test_calculate_move_to_position_partial_no_change(self):
        """Test move to position with partial tracks returns current order."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.MOVE_TO_POSITION,
            track_numbers=[1, 3]  # Only some tracks specified
        )
        
        new_order = self.service.calculate_new_order(command, self.sample_tracks)
        
        # Should return original order when partial move not implemented
        assert new_order == [1, 2, 3, 4]
    
    def test_calculate_unsupported_strategy_error(self):
        """Test unsupported strategy raises error."""
        # Create a mock strategy that doesn't exist
        command = ReorderingCommand(
            playlist_id="test",
            strategy="UNSUPPORTED_STRATEGY",  # Invalid strategy
            track_numbers=[1, 2, 3, 4]
        )
        
        with pytest.raises(ValueError, match="Unsupported reordering strategy"):
            self.service.calculate_new_order(command, self.sample_tracks)


class TestTrackReorderingServiceTrackCreation:
    """Test track creation and reordering logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TrackReorderingService()
        self.sample_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", 
                  id="track1", duration_ms=180000, artist="Artist 1", album="Album 1"),
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", 
                  id="track2", duration_ms=240000, artist="Artist 2", album="Album 2"),
            Track(track_number=3, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", 
                  id="track3", duration_ms=200000, artist="Artist 3", album="Album 3"),
        ]
    
    def test_create_reordered_tracks_preserves_metadata(self):
        """Test reordered tracks preserve all original metadata."""
        new_order = [3, 1, 2]
        
        reordered_tracks = self.service.create_reordered_tracks(new_order, self.sample_tracks)
        
        assert len(reordered_tracks) == 3
        
        # First position should be original track 3 with new track_number 1
        assert reordered_tracks[0].track_number == 1
        assert reordered_tracks[0].title == "Track 3"
        assert reordered_tracks[0].filename == "t3.mp3"
        assert reordered_tracks[0].file_path == "/music/t3.mp3"
        assert reordered_tracks[0].id == "track3"
        assert reordered_tracks[0].duration_ms == 200000
        assert reordered_tracks[0].artist == "Artist 3"
        assert reordered_tracks[0].album == "Album 3"
        
        # Second position should be original track 1 with new track_number 2
        assert reordered_tracks[1].track_number == 2
        assert reordered_tracks[1].title == "Track 1"
        assert reordered_tracks[1].id == "track1"
        
        # Third position should be original track 2 with new track_number 3
        assert reordered_tracks[2].track_number == 3
        assert reordered_tracks[2].title == "Track 2"
        assert reordered_tracks[2].id == "track2"
    
    def test_create_reordered_tracks_sequential_numbering(self):
        """Test reordered tracks get sequential track numbers starting from 1."""
        new_order = [2, 3, 1]
        
        reordered_tracks = self.service.create_reordered_tracks(new_order, self.sample_tracks)
        
        track_numbers = [track.track_number for track in reordered_tracks]
        assert track_numbers == [1, 2, 3]
    
    def test_create_reordered_tracks_empty_order(self):
        """Test creating reordered tracks with empty order."""
        new_order = []
        
        reordered_tracks = self.service.create_reordered_tracks(new_order, self.sample_tracks)
        
        assert len(reordered_tracks) == 0


class TestTrackReorderingServiceExecution:
    """Test the main execution logic and business rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TrackReorderingService()
        self.sample_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
            Track(track_number=3, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", id="track3"),
        ]
    
    def test_execute_reordering_successful_bulk_reorder(self):
        """Test successful bulk reorder execution."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[3, 1, 2]
        )
        
        result = self.service.execute_reordering(command, self.sample_tracks)
        
        assert result.success is True
        assert result.original_order == [1, 2, 3]
        assert result.new_order == [3, 1, 2]
        assert len(result.affected_tracks) == 3
        assert len(result.validation_errors) == 0
        assert len(result.business_rule_violations) == 0
        
        # Check track details
        assert result.affected_tracks[0].track_number == 1
        assert result.affected_tracks[0].title == "Track 3"
        assert result.affected_tracks[1].track_number == 2
        assert result.affected_tracks[1].title == "Track 1"
        assert result.affected_tracks[2].track_number == 3
        assert result.affected_tracks[2].title == "Track 2"
    
    def test_execute_reordering_successful_swap(self):
        """Test successful swap execution."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.SWAP_TRACKS,
            track_numbers=[1, 3]
        )
        
        result = self.service.execute_reordering(command, self.sample_tracks)
        
        assert result.success is True
        assert result.original_order == [1, 2, 3]
        assert result.new_order == [3, 2, 1]  # Swapped tracks 1 and 3
        assert len(result.affected_tracks) == 3
    
    def test_execute_reordering_validation_failure(self):
        """Test execution failure due to validation errors."""
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[1, 2, 5]  # Invalid track number 5
        )
        
        result = self.service.execute_reordering(command, self.sample_tracks)
        
        assert result.success is False
        assert result.original_order == [1, 2, 3]
        assert result.new_order == [1, 2, 3]  # No change
        assert len(result.affected_tracks) == 0
        assert len(result.validation_errors) > 0
        assert len(result.business_rule_violations) == 0
    
    def test_execute_reordering_handles_exceptions(self):
        """Test execution handles unexpected exceptions gracefully."""
        # Create invalid command to trigger exception in calculate_new_order
        command = ReorderingCommand(
            playlist_id="test",
            strategy="INVALID_STRATEGY",  # This will cause an exception
            track_numbers=[1, 2, 3]
        )
        
        result = self.service.execute_reordering(command, self.sample_tracks)
        
        assert result.success is False
        assert result.original_order == [1, 2, 3]
        assert result.new_order == [1, 2, 3]  # No change
        assert len(result.affected_tracks) == 0
        assert len(result.validation_errors) > 0
        assert "Reordering execution failed" in result.validation_errors[0]


class TestTrackReorderingServiceBusinessRuleChecks:
    """Test post-reordering business rule validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TrackReorderingService()
        self.original_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
            Track(track_number=3, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", id="track3"),
        ]
    
    def test_check_business_rules_valid_reordering(self):
        """Test business rules pass for valid reordering."""
        reordered_tracks = [
            Track(track_number=1, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", id="track3"),
            Track(track_number=2, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=3, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
        ]
        
        violations = self.service._check_business_rules(reordered_tracks, self.original_tracks)
        
        assert len(violations) == 0
    
    def test_check_business_rules_track_count_violation(self):
        """Test business rule violation: track count changed."""
        reordered_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
            # Missing track 3
        ]
        
        violations = self.service._check_business_rules(reordered_tracks, self.original_tracks)
        
        # Should have multiple violations: count change + missing tracks
        assert len(violations) >= 1
        violation_text = " ".join(violations)
        assert "Track count changed: 3 -> 2" in violation_text
    
    def test_check_business_rules_missing_tracks_violation(self):
        """Test business rule violation: tracks missing after reordering."""
        reordered_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
            Track(track_number=3, title="New Track", filename="new.mp3", file_path="/music/new.mp3", id="new_track"),
        ]
        
        violations = self.service._check_business_rules(reordered_tracks, self.original_tracks)
        
        assert len(violations) >= 1
        violation_text = " ".join(violations)
        assert "Missing tracks: {'track3'}" in violation_text
        assert "Unexpected tracks added: {'new_track'}" in violation_text
    
    def test_check_business_rules_non_sequential_numbers_violation(self):
        """Test business rule violation: track numbers not sequential."""
        reordered_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=3, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),  # Gap in numbering
            Track(track_number=5, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", id="track3"),
        ]
        
        violations = self.service._check_business_rules(reordered_tracks, self.original_tracks)
        
        assert len(violations) >= 1
        violation_text = " ".join(violations)
        assert "Track numbers not sequential. Expected: [1, 2, 3], Got: [1, 3, 5]" in violation_text
    
    def test_check_business_rules_duplicate_numbers_violation(self):
        """Test business rule violation: duplicate track numbers."""
        reordered_tracks = [
            Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3", id="track1"),
            Track(track_number=1, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),  # Duplicate number
            Track(track_number=2, title="Track 3", filename="t3.mp3", file_path="/music/t3.mp3", id="track3"),
        ]
        
        violations = self.service._check_business_rules(reordered_tracks, self.original_tracks)
        
        assert len(violations) >= 1
        violation_text = " ".join(violations)
        assert "Duplicate track numbers found" in violation_text


class TestTrackReorderingServicePlaylistValidation:
    """Test playlist-level validation for reordering capability."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TrackReorderingService()
    
    def test_can_reorder_valid_playlist(self):
        """Test valid playlist can be reordered."""
        playlist = Playlist(name="Test Playlist")
        playlist.add_track(Track(track_number=1, title="Track 1", filename="t1.mp3", file_path="/music/t1.mp3"))
        playlist.add_track(Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3"))
        
        can_reorder, reason = self.service.can_reorder(playlist)
        
        assert can_reorder is True
        assert reason == ""
    
    def test_can_reorder_none_playlist(self):
        """Test None playlist cannot be reordered."""
        can_reorder, reason = self.service.can_reorder(None)
        
        assert can_reorder is False
        assert reason == "Playlist does not exist"
    
    def test_can_reorder_empty_playlist(self):
        """Test empty playlist cannot be reordered."""
        playlist = Playlist(name="Empty Playlist")
        
        can_reorder, reason = self.service.can_reorder(playlist)
        
        assert can_reorder is False
        assert reason == "Playlist is empty"
    
    def test_can_reorder_single_track_playlist(self):
        """Test single track playlist cannot be reordered."""
        playlist = Playlist(name="Single Track Playlist")
        playlist.add_track(Track(track_number=1, title="Only Track", filename="only.mp3", file_path="/music/only.mp3"))
        
        can_reorder, reason = self.service.can_reorder(playlist)
        
        assert can_reorder is False
        assert reason == "Single track playlist cannot be reordered"


class TestTrackReorderingServiceEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TrackReorderingService()
    
    def test_reorder_tracks_with_gaps_in_numbering(self):
        """Test reordering tracks with non-sequential original numbering."""
        tracks = [
            Track(track_number=2, title="Track 2", filename="t2.mp3", file_path="/music/t2.mp3", id="track2"),
            Track(track_number=5, title="Track 5", filename="t5.mp3", file_path="/music/t5.mp3", id="track5"),
            Track(track_number=8, title="Track 8", filename="t8.mp3", file_path="/music/t8.mp3", id="track8"),
        ]
        
        command = ReorderingCommand(
            playlist_id="test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=[8, 2, 5]  # Reorder the existing numbers
        )
        
        result = self.service.execute_reordering(command, tracks)
        
        assert result.success is True
        assert result.new_order == [8, 2, 5]
        assert len(result.affected_tracks) == 3
        
        # Check that new tracks have sequential numbering
        assert result.affected_tracks[0].track_number == 1  # Original track 8, now position 1
        assert result.affected_tracks[1].track_number == 2  # Original track 2, now position 2
        assert result.affected_tracks[2].track_number == 3  # Original track 5, now position 3
    
    def test_reorder_large_playlist(self):
        """Test reordering large playlist for performance."""
        # Create 100 tracks
        large_tracks = [
            Track(track_number=i, title=f"Track {i}", filename=f"t{i}.mp3", 
                  file_path=f"/music/t{i}.mp3", id=f"track{i}")
            for i in range(1, 101)
        ]
        
        # Reverse the order
        new_order = list(range(100, 0, -1))
        
        command = ReorderingCommand(
            playlist_id="large_test",
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=new_order
        )
        
        result = self.service.execute_reordering(command, large_tracks)
        
        assert result.success is True
        assert len(result.affected_tracks) == 100
        assert result.affected_tracks[0].title == "Track 100"  # First position should be original track 100
        assert result.affected_tracks[99].title == "Track 1"   # Last position should be original track 1
    
    def test_swap_first_and_last_tracks(self):
        """Test swapping first and last tracks in playlist."""
        tracks = [
            Track(track_number=1, title="First", filename="first.mp3", file_path="/music/first.mp3", id="first"),
            Track(track_number=2, title="Middle", filename="middle.mp3", file_path="/music/middle.mp3", id="middle"),
            Track(track_number=3, title="Last", filename="last.mp3", file_path="/music/last.mp3", id="last"),
        ]
        
        command = ReorderingCommand(
            playlist_id="swap_test",
            strategy=ReorderingStrategy.SWAP_TRACKS,
            track_numbers=[1, 3]
        )
        
        result = self.service.execute_reordering(command, tracks)
        
        assert result.success is True
        assert result.new_order == [3, 2, 1]  # First and last swapped
        assert result.affected_tracks[0].title == "Last"    # Position 1 now has "Last"
        assert result.affected_tracks[1].title == "Middle"  # Position 2 unchanged
        assert result.affected_tracks[2].title == "First"   # Position 3 now has "First"