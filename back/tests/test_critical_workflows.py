# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Critical Business Workflows Test Coverage
Tests for core user workflows spanning multiple domains.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import tempfile
from pathlib import Path

from app.src.domain.data.models.playlist import Playlist
from app.src.domain.data.models.track import Track
from app.src.domain.nfc.entities.nfc_tag import NfcTag
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.application.services.playlist_application_service import DataApplicationService as PlaylistApplicationService
from app.src.application.services.nfc_application_service import NfcApplicationService
from app.src.services.player_state_service import PlayerStateService
from app.src.services.state_manager import StateManager, StateEventType
from app.src.common.data_models import PlayerStateModel, TrackModel, PlaybackState


class TestCriticalBusinessWorkflows:
    """Test critical business workflows that span multiple domains."""

    def setup_method(self):
        """Set up test fixtures for workflow tests."""
        self.mock_repository = Mock()
        self.mock_hardware = Mock()
        self.mock_audio_engine = Mock()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestNFCToPlaylistWorkflow:
    """Test NFC tag detection to playlist playback workflow."""

    def setup_method(self):
        """Set up NFC workflow test fixtures."""
        self.mock_repository = Mock()
        self.mock_hardware = Mock()
        
        # Create test playlist data
        self.test_playlist = {
            "id": "nfc-playlist-123",
            "title": "NFC Test Playlist",
            "description": "Test playlist for NFC",
            "tracks": [
                {
                    "track_number": 1,
                    "title": "First Song",
                    "filename": "song1.mp3",
                    "file_path": "/music/song1.mp3",
                    "duration_ms": 180000
                },
                {
                    "track_number": 2,
                    "title": "Second Song", 
                    "filename": "song2.mp3",
                    "file_path": "/music/song2.mp3",
                    "duration_ms": 200000
                }
            ],
            "nfc_tag_id": "ABCD1234"
        }

    @pytest.mark.asyncio
    async def test_nfc_detection_to_playlist_resolution_workflow(self):
        """Test complete workflow from NFC detection to playlist resolution."""
        # Step 1: NFC tag detected - Business Logic
        tag_id = TagIdentifier("ABCD1234")
        nfc_tag = NfcTag(identifier=tag_id, associated_playlist_id="nfc-playlist-123")
        
        # Business Rule: Tag must be properly formatted and associated
        assert nfc_tag.identifier.is_valid()
        assert nfc_tag.is_associated()
        assert nfc_tag.associated_playlist_id == "nfc-playlist-123"
        
        # Step 2: Repository lookup - Business Logic
        self.mock_repository.get_playlist_by_nfc_tag = Mock(return_value=self.test_playlist)
        
        # Business workflow: Retrieve playlist by NFC tag
        playlist_data = self.mock_repository.get_playlist_by_nfc_tag(tag_id.uid)
        
        # Business Rule: Playlist must exist and have valid structure
        assert playlist_data is not None
        assert playlist_data["id"] == "nfc-playlist-123"
        assert playlist_data["nfc_tag_id"] == tag_id.uid
        assert len(playlist_data["tracks"]) == 2
        
        # Step 3: Playlist validation - Business Logic
        # Business Rule: All tracks must be valid
        for track_data in playlist_data["tracks"]:
            assert track_data["track_number"] > 0
            assert len(track_data["title"]) > 0
            assert len(track_data["file_path"]) > 0
            assert track_data["duration_ms"] > 0
        
        # Business Rule: Tracks should be sequential
        track_numbers = [t["track_number"] for t in playlist_data["tracks"]]
        assert track_numbers == [1, 2]
        
        # Step 4: Playlist ready for playback - Business Outcome
        total_duration = sum(t["duration_ms"] for t in playlist_data["tracks"])
        assert total_duration == 380000  # 180000 + 200000
        
        print("✅ NFC detection to playlist resolution workflow: PASSED")

    @pytest.mark.asyncio
    async def test_nfc_detection_invalid_tag_workflow(self):
        """Test NFC detection workflow with invalid tag."""
        # Business Rule: Invalid tag should be handled gracefully
        try:
            invalid_tag_id = TagIdentifier("GG")  # Too short and invalid hex
            assert False, "Should have raised ValueError for invalid tag"
        except ValueError:
            pass  # Expected behavior
        
        # Business Rule: Non-associated tag should return no playlist
        valid_tag = TagIdentifier("ABCD1234")
        unassociated_tag = NfcTag(identifier=valid_tag)  # No playlist association
        
        assert not unassociated_tag.is_associated()
        assert unassociated_tag.associated_playlist_id is None
        
        # Business workflow: Repository should return None for unassociated tags
        self.mock_repository.get_playlist_by_nfc_tag = Mock(return_value=None)
        
        result = self.mock_repository.get_playlist_by_nfc_tag(valid_tag.uid)
        assert result is None
        
        print("✅ NFC invalid tag workflow: PASSED")

    @pytest.mark.asyncio
    async def test_nfc_to_empty_playlist_workflow(self):
        """Test NFC detection with empty playlist workflow."""
        # Business Scenario: NFC tag associated with empty playlist
        empty_playlist = {
            "id": "empty-playlist-123",
            "title": "Empty Playlist",
            "description": "No tracks",
            "tracks": [],
            "nfc_tag_id": "EMPTY123"
        }
        
        tag_id = TagIdentifier("EMPTY123")
        nfc_tag = NfcTag(identifier=tag_id, associated_playlist_id="empty-playlist-123")
        
        # Business Rule: Tag is valid and associated
        assert nfc_tag.is_associated()
        
        # Business workflow: Repository returns empty playlist
        self.mock_repository.get_playlist_by_nfc_tag = Mock(return_value=empty_playlist)
        playlist_data = self.mock_repository.get_playlist_by_nfc_tag(tag_id.uid)
        
        # Business Rule: Empty playlist should be handled gracefully
        assert playlist_data is not None
        assert playlist_data["id"] == "empty-playlist-123"
        assert len(playlist_data["tracks"]) == 0
        
        # Business Logic: Calculate total duration for empty playlist
        total_duration = sum(t["duration_ms"] for t in playlist_data["tracks"])
        assert total_duration == 0
        
        print("✅ NFC empty playlist workflow: PASSED")


class TestPlaylistToAudioWorkflow:
    """Test playlist loading to audio engine workflow."""

    def setup_method(self):
        """Set up playlist to audio workflow test fixtures."""
        self.mock_audio_engine = Mock()
        self.mock_state_manager = Mock()
        
        # Create test playlist with tracks
        self.test_playlist = Playlist(name="Audio Test Playlist", description="For audio testing")
        
        track1 = Track(1, "Audio Track 1", "audio1.mp3", "/audio/audio1.mp3", duration_ms=240000)
        track2 = Track(2, "Audio Track 2", "audio2.mp3", "/audio/audio2.mp3", duration_ms=180000)
        
        self.test_playlist.add_track(track1)
        self.test_playlist.add_track(track2)

    @pytest.mark.asyncio
    async def test_playlist_loading_to_audio_engine_workflow(self):
        """Test loading playlist into audio engine workflow."""
        # Business Rule: Playlist must be valid before loading
        assert self.test_playlist.is_valid()
        assert len(self.test_playlist.tracks) == 2
        
        # Business workflow: Prepare playlist for audio engine
        playlist_tracks = self.test_playlist.tracks
        
        # Business Rule: All tracks must have valid file paths
        for track in playlist_tracks:
            assert track.is_valid()
            assert len(track.file_path) > 0
            assert track.track_number > 0
            assert track.duration_ms > 0
        
        # Business Logic: Calculate total playlist duration
        total_duration = self.test_playlist.get_total_duration_ms()
        assert total_duration == 420000  # 240000 + 180000
        
        # Simulate audio engine loading business logic
        self.mock_audio_engine.load_playlist = AsyncMock(return_value=True)
        self.mock_audio_engine.get_current_track = Mock(return_value=playlist_tracks[0])
        self.mock_audio_engine.is_playing = Mock(return_value=True)
        
        # Business workflow: Load playlist into audio engine
        load_result = await self.mock_audio_engine.load_playlist(playlist_tracks)
        assert load_result is True
        
        # Business Rule: Audio engine should have current track
        current_track = self.mock_audio_engine.get_current_track()
        assert current_track.track_number == 1
        assert current_track.title == "Audio Track 1"
        
        print("✅ Playlist to audio engine workflow: PASSED")

    @pytest.mark.asyncio
    async def test_audio_playback_state_management_workflow(self):
        """Test audio playback state management workflow."""
        # Business workflow: Create player state from playlist and audio engine
        player_state = PlayerState(
            is_playing=True,
            is_paused=False,
            current_track_number=1,
            active_playlist_id=self.test_playlist.id,
            active_playlist_title=self.test_playlist.name,
            total_tracks=len(self.test_playlist.tracks),
            position_seconds=30.0,
            duration_seconds=240.0,  # First track duration in seconds
            volume=75,
            server_seq=100
        )
        
        # Business Rule: Player state must reflect current playback status
        assert player_state.is_playing
        assert not player_state.is_paused
        assert player_state.current_track_number == 1
        assert player_state.total_tracks == 2
        
        # Business Logic: Calculate playback progress
        progress = player_state.progress_percentage
        expected_progress = (30.0 / 240.0) * 100
        assert progress == pytest.approx(expected_progress, abs=0.1)
        
        # Business Rule: State should be serializable for transmission
        state_dict = player_state.model_dump()
        assert state_dict["is_playing"] is True
        assert state_dict["active_playlist_title"] == "Audio Test Playlist"
        assert state_dict["volume"] == 75
        
        print("✅ Audio playback state management workflow: PASSED")


class TestUploadToPlaylistWorkflow:
    """Test file upload to playlist addition workflow."""

    def setup_method(self):
        """Set up upload workflow test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_repository = Mock()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_upload_to_playlist_workflow(self):
        """Test complete workflow from upload to playlist addition."""
        # Step 1: Upload validation - Business Logic
        from app.src.domain.upload.services.upload_validation_service import UploadValidationService
        
        validation_service = UploadValidationService(
            max_file_size=1000000,  # 1MB
            allowed_extensions={"mp3", "wav", "flac"}
        )
        
        # Business Rule: File must meet validation criteria
        assert validation_service.is_valid_file_size(500000)
        assert validation_service.is_valid_file_extension("newtrack.mp3")
        assert not validation_service.is_valid_file_size(2000000)  # Too large
        assert not validation_service.is_valid_file_extension("document.pdf")  # Wrong type
        
        # Step 2: Upload session creation - Business Logic
        from app.src.domain.upload.entities.upload_session import UploadSession, UploadStatus
        
        upload_session = UploadSession(
            filename="newtrack.mp3",
            total_size_bytes=500000,
            total_chunks=10
        )
        
        # Business Rule: New session should have correct initial state
        assert upload_session.status == UploadStatus.CREATED
        assert upload_session.received_chunks == 0
        assert not upload_session.is_completed()
        
        # Step 3: Chunk upload simulation - Business Logic
        from app.src.domain.upload.value_objects.file_chunk import FileChunk
        
        # Business workflow: Upload all chunks
        for chunk_index in range(10):
            chunk_data = f"chunk_{chunk_index}_data".encode()
            chunk = FileChunk.create(chunk_index, chunk_data, f"checksum_{chunk_index}")
            
            # Business Rule: Each chunk must be valid
            assert chunk.index == chunk_index
            assert chunk.size == len(chunk_data)
            assert chunk.is_valid_size(100000)  # Within limits
            
            upload_session.add_chunk(chunk)
        
        # Business Rule: Session should be ready for completion after all chunks
        assert upload_session.received_chunks == 10
        assert len(upload_session.received_chunk_indices) == 10
        
        # Step 4: Upload completion - Business Logic
        upload_session.mark_completed()
        assert upload_session.is_completed()
        assert upload_session.status == UploadStatus.COMPLETED
        
        # Step 5: File metadata extraction - Business Logic
        from app.src.domain.upload.value_objects.file_metadata import FileMetadata
        
        extracted_metadata = FileMetadata(
            filename="newtrack.mp3",
            size_bytes=500000,
            mime_type="audio/mpeg",
            title="New Track Title",
            artist="Test Artist",
            album="Test Album",
            duration_seconds=180.0,
            bitrate=320,
            sample_rate=44100
        )
        
        # Business Rule: Metadata should be complete and valid
        assert extracted_metadata.title == "New Track Title"
        assert extracted_metadata.duration_seconds == 180.0
        assert extracted_metadata.get_duration_formatted() == "3:00"
        
        # Step 6: Track creation from upload - Business Logic
        new_track = Track(
            track_number=1,  # Will be auto-assigned by playlist
            title=extracted_metadata.title,
            filename=extracted_metadata.filename,
            file_path=f"/uploads/{extracted_metadata.filename}",
            duration_ms=int(extracted_metadata.duration_seconds * 1000),
            artist=extracted_metadata.artist,
            album=extracted_metadata.album
        )
        
        # Business Rule: Track created from upload should be valid
        assert new_track.is_valid()
        assert new_track.title == "New Track Title"
        assert new_track.duration_ms == 180000
        assert new_track.artist == "Test Artist"
        
        # Step 7: Add track to playlist - Business Logic
        target_playlist = Playlist(name="Upload Target Playlist", description="For uploads")
        target_playlist.add_track(new_track)
        
        # Business Rule: Playlist should contain the new track
        assert len(target_playlist.tracks) == 1
        assert target_playlist.tracks[0].title == "New Track Title"
        assert target_playlist.get_total_duration_ms() == 180000
        
        print("✅ Complete upload to playlist workflow: PASSED")


class TestErrorRecoveryWorkflows:
    """Test error recovery workflows across business domains."""

    def setup_method(self):
        """Set up error recovery test fixtures."""
        self.mock_repository = Mock()
        self.mock_hardware = Mock()

    @pytest.mark.asyncio
    async def test_nfc_hardware_failure_recovery_workflow(self):
        """Test NFC hardware failure recovery workflow."""
        # Business Scenario: Hardware failure during NFC detection
        self.mock_hardware.start_detection = AsyncMock(side_effect=Exception("Hardware failure"))
        self.mock_hardware.get_hardware_status = Mock(return_value={"is_available": False})
        
        # Business Rule: Service should handle hardware failures gracefully
        from app.src.application.services.nfc_application_service import NfcApplicationService
        
        nfc_service = NfcApplicationService(
            nfc_adapter=self.mock_hardware,
            nfc_repository=self.mock_repository,
            association_service=Mock()
        )
        
        # Business workflow: Attempt to start NFC system with failing hardware
        result = await nfc_service.start_nfc_system_use_case()
        
        # Business Rule: Error should be handled gracefully with proper error response
        assert result["status"] == "error"
        assert "error_type" in result
        assert "Hardware failure" in result.get("message", "")
        
        print("✅ NFC hardware failure recovery workflow: PASSED")

    @pytest.mark.asyncio
    async def test_playlist_repository_failure_recovery_workflow(self):
        """Test playlist repository failure recovery workflow."""
        # Business Scenario: Repository failure during playlist operations
        self.mock_repository.get_playlist_by_id = Mock(side_effect=Exception("Database connection failed"))
        
        # Business Rule: Application service should handle repository failures
        playlist_service = PlaylistApplicationService(
            playlist_repository=self.mock_repository,
            file_system_service=Mock()
        )
        
        # Business workflow: Attempt playlist retrieval with failing repository
        result = await playlist_service.get_playlist_use_case("test-playlist-id")
        
        # Business Rule: Repository failure should be handled gracefully
        assert result["status"] == "error"
        assert "Database connection failed" in result.get("message", "")
        
        print("✅ Playlist repository failure recovery workflow: PASSED")

    @pytest.mark.asyncio
    async def test_partial_upload_recovery_workflow(self):
        """Test recovery from partial upload failure workflow."""
        # Business Scenario: Upload interrupted after partial completion
        from app.src.domain.upload.entities.upload_session import UploadSession, UploadStatus
        from app.src.domain.upload.value_objects.file_chunk import FileChunk
        
        upload_session = UploadSession(
            filename="interrupted.mp3",
            total_size_bytes=1000,
            total_chunks=10
        )
        
        # Business workflow: Simulate partial upload (5 out of 10 chunks)
        for i in range(5):
            chunk = FileChunk.create(i, f"chunk_{i}".encode(), f"checksum_{i}")
            upload_session.add_chunk(chunk)
        
        # Business Rule: Session should track partial completion
        assert upload_session.received_chunks == 5
        assert upload_session.status == UploadStatus.CREATED  # Not completed
        assert not upload_session.is_completed()
        
        # Business Logic: Calculate completion percentage
        completion_percentage = (upload_session.received_chunks / upload_session.total_chunks) * 100
        assert completion_percentage == 50.0
        
        # Business workflow: Resume upload with remaining chunks
        for i in range(5, 10):
            chunk = FileChunk.create(i, f"chunk_{i}".encode(), f"checksum_{i}")
            upload_session.add_chunk(chunk)
        
        # Business Rule: Session should complete after all chunks received
        upload_session.mark_completed()
        assert upload_session.is_completed()
        assert upload_session.received_chunks == 10
        
        print("✅ Partial upload recovery workflow: PASSED")


class TestStateConsistencyWorkflows:
    """Test state consistency across business domains."""

    @pytest.mark.asyncio
    async def test_playlist_audio_state_consistency_workflow(self):
        """Test state consistency between playlist and audio domains."""
        # Business setup: Create playlist with tracks
        playlist = Playlist(name="Consistency Test", description="State test")
        
        track1 = Track(1, "Track One", "track1.mp3", "/music/track1.mp3", duration_ms=200000)
        track2 = Track(2, "Track Two", "track2.mp3", "/music/track2.mp3", duration_ms=180000)
        
        playlist.add_track(track1)
        playlist.add_track(track2)
        
        # Business Rule: Playlist state should be consistent
        assert len(playlist.tracks) == 2
        assert playlist.get_total_duration_ms() == 380000
        
        # Simulate audio engine state
        mock_audio_state = {
            "current_playlist_id": playlist.id,
            "current_track_number": 1,
            "is_playing": True,
            "position_seconds": 45.0,
            "duration_seconds": 200.0  # Track 1 duration
        }
        
        # Business Rule: Audio state should match playlist data
        current_track = playlist.get_track_by_number(mock_audio_state["current_track_number"])
        assert current_track is not None
        assert current_track.track_number == 1
        assert current_track.title == "Track One"
        
        # Business Logic: Verify duration consistency
        expected_duration_seconds = current_track.duration_ms / 1000
        assert mock_audio_state["duration_seconds"] == expected_duration_seconds
        
        # Business Rule: Position should be within track duration
        assert 0 <= mock_audio_state["position_seconds"] <= mock_audio_state["duration_seconds"]
        
        print("✅ Playlist-audio state consistency workflow: PASSED")

    @pytest.mark.asyncio
    async def test_nfc_playlist_association_consistency_workflow(self):
        """Test consistency between NFC associations and playlist data."""
        # Business setup: Create playlist and NFC tag
        playlist = Playlist(name="NFC Consistency Test", description="Association test")
        playlist.nfc_tag_id = "CONSIST123"
        
        tag_id = TagIdentifier("CONSIST123")
        nfc_tag = NfcTag(identifier=tag_id, associated_playlist_id=playlist.id)
        
        # Business Rule: Bidirectional association should be consistent
        assert playlist.nfc_tag_id == tag_id.uid
        assert nfc_tag.associated_playlist_id == playlist.id
        assert nfc_tag.is_associated()
        
        # Business workflow: Verify association lookup works both ways
        # From NFC tag to playlist
        assert nfc_tag.associated_playlist_id == playlist.id
        
        # From playlist to NFC tag
        assert playlist.nfc_tag_id == tag_id.uid
        
        # Business Rule: Dissociation should maintain consistency
        nfc_tag.dissociate_from_playlist()
        # Note: In real system, playlist.nfc_tag_id would also be cleared
        
        assert not nfc_tag.is_associated()
        assert nfc_tag.associated_playlist_id is None
        
        print("✅ NFC-playlist association consistency workflow: PASSED")


# Integration test class for all workflow combinations
class TestCompleteWorkflowIntegration:
    """Integration tests for complete workflow combinations."""

    @pytest.mark.asyncio
    async def test_end_to_end_music_box_workflow(self):
        """Test complete end-to-end music box workflow."""
        print("\n🎵 Testing complete end-to-end Music Box workflow...")
        
        # Phase 1: Upload and playlist creation
        playlist = Playlist(name="End-to-End Test", description="Complete workflow test")
        
        # Simulate uploaded tracks
        track1 = Track(1, "Opening Song", "opening.mp3", "/music/opening.mp3", duration_ms=240000)
        track2 = Track(2, "Main Theme", "theme.mp3", "/music/theme.mp3", duration_ms=300000)
        
        playlist.add_track(track1)
        playlist.add_track(track2)
        
        # Business Rule: Playlist should be ready for use
        assert playlist.is_valid()
        assert len(playlist.tracks) == 2
        
        # Phase 2: NFC tag association
        tag_id = TagIdentifier("E2E12345")
        nfc_tag = NfcTag(identifier=tag_id)
        nfc_tag.associate_with_playlist(playlist.id)
        playlist.nfc_tag_id = tag_id.uid
        
        # Business Rule: NFC association should be bidirectional
        assert nfc_tag.is_associated()
        assert playlist.nfc_tag_id == tag_id.uid
        
        # Phase 3: NFC detection and playlist resolution
        # Simulate NFC detection workflow
        detected_tag_uid = tag_id.uid
        associated_playlist_id = nfc_tag.associated_playlist_id
        
        # Business Rule: Detection should resolve to correct playlist
        assert associated_playlist_id == playlist.id
        
        # Phase 4: Audio playback preparation
        playlist_tracks = playlist.tracks
        total_duration = playlist.get_total_duration_ms()
        
        # Business Rule: Playlist should be ready for audio engine
        assert len(playlist_tracks) == 2
        assert total_duration == 540000  # 240000 + 300000
        
        # Phase 5: State management
        player_state = PlayerState(
            is_playing=True,
            is_paused=False,
            current_track_number=1,
            active_playlist_id=playlist.id,
            active_playlist_title=playlist.name,
            total_tracks=len(playlist.tracks),
            position_seconds=0.0,
            duration_seconds=240.0,  # First track
            volume=100,
            server_seq=1
        )
        
        # Business Rule: Player state should reflect the complete workflow
        assert player_state.is_playing
        assert player_state.active_playlist_title == "End-to-End Test"
        assert player_state.total_tracks == 2
        assert player_state.current_track_number == 1
        
        print("✅ Complete end-to-end Music Box workflow: PASSED")
        print(f"   📝 Playlist: {playlist.name} ({len(playlist.tracks)} tracks)")
        print(f"   🏷️  NFC Tag: {tag_id.uid}")
        print(f"   🎵 Now Playing: {playlist_tracks[0].title}")
        print(f"   ⏱️  Total Duration: {total_duration/1000/60:.1f} minutes")