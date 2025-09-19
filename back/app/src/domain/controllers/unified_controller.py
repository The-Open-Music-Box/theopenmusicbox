# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unified controller that replaces all legacy playlist controllers."""

import asyncio
from typing import Dict, Any, Optional, Callable, List

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors
from app.src.domain.models.playlist import Playlist
from app.src.domain.models.track import Track

from ..audio.container import audio_domain_container
from ..audio.protocols.audio_engine_protocol import AudioEngineProtocol

logger = get_logger(__name__)


class UnifiedPlaylistController:
    """Unified controller that replaces all legacy PlaylistController implementations.

    This controller acts as the single point of entry for all playlist operations,
    providing a consistent interface while using the domain-driven architecture underneath.
    """

    def __init__(
        self,
        audio_engine: AudioEngineProtocol = None,
        playlist_service=None,
        config=None,
        state_manager=None,
        player_state_service=None,
        audio_controller=None,
    ):
        """Initialize the unified controller.

        Args:
            audio_engine: Optional audio engine (uses global container if None)
            playlist_service: Legacy playlist service for compatibility
            config: Legacy configuration
            state_manager: Legacy state manager for websocket broadcasting
            player_state_service: Legacy player state service
            audio_controller: Legacy audio controller
        """
        self._audio_engine = audio_engine
        self._playlist_service = playlist_service
        self._config = config
        self._state_manager = state_manager
        self._player_state_service = player_state_service
        self._audio_controller = audio_controller

        # Initialize playlist application service for centralized architecture
        from app.src.application.services.playlist_application_service import playlist_app_service

        self._playlist_app_service = playlist_app_service

        # Internal state
        self._is_initialized = False
        self._current_playlist: Optional[Playlist] = None
        self._current_track_index = 0
        self._callbacks: Dict[str, list] = {
            "track_started": [],
            "track_ended": [],
            "playlist_finished": [],
            "state_changed": [],
        }

        logger.log(LogLevel.INFO, "UnifiedPlaylistController initialized")

    def ensure_initialized(self) -> None:
        """Ensure the controller is initialized."""
        if self._is_initialized:
            return

        # Use domain container if no engine provided
        if self._audio_engine is None:
            if audio_domain_container.is_initialized:
                self._audio_engine = audio_domain_container.audio_engine
            else:
                logger.log(
                    LogLevel.DEBUG, "Audio engine not available yet, will initialize when needed"
                )

        self._is_initialized = True
        logger.log(LogLevel.INFO, "UnifiedPlaylistController initialized")

    async def start(self) -> None:
        """Start the controller."""
        self.ensure_initialized()
        # Domain architecture handles starting automatically
        logger.log(LogLevel.INFO, "UnifiedPlaylistController started with domain architecture")

    async def stop(self) -> None:
        """Stop the controller."""
        if self._is_initialized:
            # Domain architecture handles stopping
            if self._audio_engine and hasattr(self._audio_engine, "stop"):
                await self._audio_engine.stop()
        logger.log(LogLevel.INFO, "UnifiedPlaylistController stopped")

    # === NFC Integration Interface ===

    @handle_errors("play_playlist_from_nfc")
    async def play_playlist_from_nfc(self, nfc_tag_uid: str) -> bool:
        """Handle NFC tag detection and playlist playback."""
        self.ensure_initialized()

        # Use playlist application service to get playlist from NFC
        if self._playlist_service:
            playlist = await self._playlist_service.get_playlist_by_nfc_tag(nfc_tag_uid)
            if playlist:
                return await self.play_playlist(playlist)
        # Fallback: Use application service directly
        # CENTRALIZED FLOW: Get playlist ID from NFC tag, then use unified start logic
        playlist_id = await self._playlist_app_service.get_playlist_id_by_nfc_tag(nfc_tag_uid)
        if not playlist_id:
            logger.log(LogLevel.WARNING, f"⚠️ No playlist ID found for NFC tag: {nfc_tag_uid}")
            return False
        # Use centralized start-by-ID method (same as UI flow)
        result = await self._playlist_app_service.start_playlist_by_id(
            playlist_id, self._audio_controller
        )
        if result.get("success"):
            logger.log(
                LogLevel.INFO, f"✅ Started playlist {playlist_id} from NFC tag {nfc_tag_uid}"
            )
            return True
        else:
            logger.log(
                LogLevel.ERROR,
                f"❌ Failed to start playlist {playlist_id} from NFC tag: {result.get('error', 'Unknown error')}",
            )
            return False

    def register_playback_callback(self, callback: Callable) -> None:
        """Register callback for playback status updates (legacy interface)."""
        if "state_changed" not in self._callbacks:
            self._callbacks["state_changed"] = []
        self._callbacks["state_changed"].append(callback)

    # === Audio Playback Control Interface ===

    @handle_errors("load_playlist")
    async def load_playlist(self, playlist: Playlist) -> bool:
        """Load a playlist for playback."""
        self.ensure_initialized()

        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "set_playlist"):
            success = self._audio_engine.set_playlist(
                playlist
            )  # Remove await - this is synchronous
        else:
            success = True  # Allow operation even without audio engine
        if success:
            self._current_playlist = playlist
            self._current_track_index = 0
            await self._notify_callbacks("playlist_loaded", {"playlist": playlist})
        return success

    async def play_playlist(self, playlist: Playlist, track_index: int = 0) -> bool:
        """Load and play a playlist."""
        success = await self.load_playlist(playlist)
        if success and track_index > 0:
            success = await self.play_track_by_index(track_index)
        return success

    @handle_errors("set_playlist")
    def set_playlist(self, playlist: Playlist) -> bool:
        """Set playlist for playback (synchronous compatibility method).

        This method provides backward compatibility with application services
        that expect a synchronous set_playlist method. It delegates to the
        audio engine's playlist manager if available.
        """
        self.ensure_initialized()

        # Use audio engine's playlist manager directly (synchronous)
        if (
            self._audio_engine
            and hasattr(self._audio_engine, "_playlist_manager")
            and hasattr(self._audio_engine._playlist_manager, "set_playlist")
        ):
            success = self._audio_engine._playlist_manager.set_playlist(playlist)
            logger.log(LogLevel.INFO, f"✅ Playlist set via audio engine: {playlist.title}")
            return success
        # Fallback: Just store the playlist (compatible mode)
        self._current_playlist = playlist
        self._current_track_index = 0
        logger.log(LogLevel.INFO, f"✅ Playlist stored for compatibility: {playlist.title}")
        return True

    async def play_track_by_index(self, index: int) -> bool:
        """Play track by index."""
        self.ensure_initialized()

        if not self._current_playlist or index < 0 or index >= len(self._current_playlist.tracks):
            return False

        self._current_track_index = index
        track = self._current_playlist.tracks[index]

        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "play_track"):
            success = await self._audio_engine.play_track(str(track.path))
        else:
            success = True
        if success:
            await self._notify_callbacks("track_started", {"track": track, "index": index})

        return success

    async def next_track(self) -> bool:
        """Advance to next track."""
        self.ensure_initialized()
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "next_track"):
            success = await self._audio_engine.next_track()
        else:
            success = True
        if success and self._current_playlist:
            if self._current_track_index < len(self._current_playlist.tracks) - 1:
                self._current_track_index += 1
            else:
                await self._notify_callbacks(
                    "playlist_finished", {"playlist": self._current_playlist}
                )
        return success

    async def previous_track(self) -> bool:
        """Go to previous track."""
        self.ensure_initialized()
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "previous_track"):
            success = await self._audio_engine.previous_track()
        else:
            success = True
        if success and self._current_track_index > 0:
            self._current_track_index -= 1
        return success

    async def pause(self) -> bool:
        """Pause playback."""
        self.ensure_initialized()
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "pause"):
            success = await self._audio_engine.pause()
        else:
            success = True
        if success:
            await self._notify_callbacks("state_changed", {"state": "paused"})
        return success

    async def resume(self) -> bool:
        """Resume playback."""
        self.ensure_initialized()
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "resume"):
            success = await self._audio_engine.resume()
        else:
            success = True
        if success:
            await self._notify_callbacks("state_changed", {"state": "playing"})
        return success

    async def stop(self) -> bool:
        """Stop playback."""
        self.ensure_initialized()
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "stop"):
            success = await self._audio_engine.stop()
        else:
            success = True
        if success:
            await self._notify_callbacks("state_changed", {"state": "stopped"})
        return success

    def toggle_playback(self) -> bool:
        """Toggle between play and pause states.

        Returns:
            bool: True if toggle was successful, False otherwise
        """
        try:
            # Don't call ensure_initialized yet, let's debug step by step
            logger.log(LogLevel.DEBUG, "🎮 Toggle playback called")

            # Simple implementation for physical controls
            logger.log(LogLevel.INFO, "🎮 Physical control toggle - using simple pause/resume")

            # For now, always try to resume (since we can't reliably check state synchronously)
            result = asyncio.create_task(self.resume())
            logger.log(LogLevel.INFO, "🎮 Toggling to play")
            return True

        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Toggle playback failed: {e}")
            import traceback
            logger.log(LogLevel.ERROR, f"Stack trace: {traceback.format_exc()}")
            return False

    def next_track_sync(self) -> bool:
        """Synchronous wrapper for next_track for physical controls."""
        try:
            result = asyncio.create_task(self.next_track())
            return True  # Return sync success for compatibility
        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Next track failed: {e}")
            return False

    def previous_track_sync(self) -> bool:
        """Synchronous wrapper for previous_track for physical controls."""
        try:
            result = asyncio.create_task(self.previous_track())
            return True  # Return sync success for compatibility
        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Previous track failed: {e}")
            return False

    async def set_volume(self, volume: int) -> bool:
        """Set volume."""
        self.ensure_initialized()
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "set_volume"):
            return await self._audio_engine.set_volume(volume)
        else:
            return True

    # === State Access ===

    @handle_errors("get_state")
    def get_state(self) -> Dict[str, Any]:
        """Get current controller state."""
        if not self._is_initialized:
            return {"initialized": False, "controller_type": "UnifiedPlaylistController"}

        # Try to get base state from domain audio engine
        base_state = {}
        if self._audio_engine and hasattr(self._audio_engine, "get_state_dict"):
            base_state = self._audio_engine.get_state_dict()
        # Add playlist information
        if self._current_playlist:
            base_state.update(
                {
                    "current_playlist": {
                        "id": getattr(self._current_playlist, "id", None),
                        "title": self._current_playlist.title,
                        "track_count": len(self._current_playlist.tracks),
                    },
                    "current_track_index": self._current_track_index,
                    "can_previous": self._current_track_index > 0,
                    "can_next": self._current_track_index < len(self._current_playlist.tracks) - 1,
                }
            )

            if self._current_track_index < len(self._current_playlist.tracks):
                track = self._current_playlist.tracks[self._current_track_index]
                base_state.update(
                    {
                        "current_track": {
                            "id": track.id,
                            "title": track.title,
                            "filename": track.filename,
                            "path": str(track.path),
                            "duration_ms": track.duration_ms,
                        }
                    }
                )

        base_state.update(
            {"initialized": self._is_initialized, "controller_type": "UnifiedPlaylistController"}
        )

        return base_state

    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        if not self._is_initialized:
            return False
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "is_playing"):
            return self._audio_engine.is_playing
        else:
            return False

    @property
    def is_paused(self) -> bool:
        """Check if currently paused."""
        if not self._is_initialized:
            return False
        # Domain architecture: Use audio engine directly
        if self._audio_engine and hasattr(self._audio_engine, "is_paused"):
            return self._audio_engine.is_paused
        else:
            return False

    def get_current_track_info(self) -> Dict[str, Any]:
        """Get current track information."""
        if not self._is_initialized:
            return {}

        if not self._current_playlist or self._current_track_index >= len(
            self._current_playlist.tracks
        ):
            return {}

        track = self._current_playlist.tracks[self._current_track_index]
        # Calculate track_number (1-based) for compatibility
        track_number = self._current_track_index + 1

        return {
            "track_index": self._current_track_index,
            "track_count": len(self._current_playlist.tracks),
            "track_number": track_number,  # Add 1-based track number for consistency
            "track_id": track.id,
            "title": track.title,
            "filename": track.filename,
            "duration_ms": track.duration_ms,  # Already in milliseconds - good!
            "file_path": str(track.path),
            "can_next": self._current_track_index < len(self._current_playlist.tracks) - 1,
            "can_previous": self._current_track_index > 0,
        }

    @property
    def is_initialized(self) -> bool:
        """Check if the controller is initialized (read-only)."""
        return self._is_initialized

    @handle_errors("cleanup")
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._is_initialized:
            # Domain architecture: Cleanup audio engine
            if self._audio_engine and hasattr(self._audio_engine, "cleanup"):
                self._audio_engine.cleanup()
            logger.log(LogLevel.INFO, "UnifiedPlaylistController cleanup completed")

    # === Playlist Service Methods ===

    @handle_errors("get_all_playlists")
    async def get_all_playlists(self, page: int = 1, page_size: int = 50):
        """Retrieve all playlists using domain-driven architecture only."""
        # PURE DOMAIN ARCHITECTURE: Use application service
        from app.src.application.services.playlist_application_service import playlist_app_service

        playlists_result = await playlist_app_service.get_all_playlists_use_case(page=page, page_size=page_size)
        if playlists_result.get("status") == "success":
            playlists = playlists_result.get("playlists", [])
        else:
            playlists = []
        logger.log(LogLevel.INFO, f"Retrieved {len(playlists)} playlists via domain architecture (page {page}, size {page_size})")
        return playlists

    # === Playlist CRUD Methods for Route Compatibility ===

    @handle_errors("create_playlist")
    async def create_playlist(
        self, title: str, description: str = None, client_op_id: str = None
    ) -> Dict[str, Any]:
        """Create a new playlist with state broadcasting."""
        # PURE DOMAIN ARCHITECTURE: Use application service
        from app.src.application.services.playlist_application_service import playlist_app_service

        # Create playlist using domain application service
        result = await playlist_app_service.create_playlist_use_case(title, description)
        if result.get("status") == "success":
            playlist_id = result.get("playlist_id")

            # Get the complete playlist data to return to UI
            playlist_result = await playlist_app_service.get_playlist_use_case(playlist_id)
            playlist_data = playlist_result.get("playlist") if playlist_result.get("status") == "success" else None

            logger.log(LogLevel.INFO, f"✅ Created playlist: {title}")
            return {
                "status": "success",
                "message": "Playlist created successfully",
                "playlist_id": playlist_id,
                "playlist": playlist_data,  # Add complete playlist data
                "client_op_id": client_op_id,
            }
        else:
            return {
                "status": "error",
                "message": result.get("message", "Failed to create playlist"),
            }

    @handle_errors("delete_playlist")
    async def delete_playlist(self, playlist_id: str, client_op_id: str = None) -> Dict[str, Any]:
        """Delete a playlist with state broadcasting."""
        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        success = await repo.delete_playlist(playlist_id)  # Add await here
        if success:
            logger.log(LogLevel.INFO, f"✅ Deleted playlist: {playlist_id}")
            return {
                "status": "success",
                "message": "Playlist deleted successfully",
                "client_op_id": client_op_id,
            }
        else:
            return {"status": "error", "message": "Failed to delete playlist"}

    @handle_errors("update_playlist")
    async def update_playlist(
        self, playlist_id: str, updates: Dict[str, Any], client_op_id: str = None
    ) -> Dict[str, Any]:
        """Update a playlist with state broadcasting."""

        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        success = await repo.update_playlist(playlist_id, updates)
        if success:
            logger.log(LogLevel.INFO, f"✅ Updated playlist: {playlist_id}")
            return {
                "status": "success",
                "message": "Playlist updated successfully",
                "client_op_id": client_op_id,
            }
        else:
            return {"status": "error", "message": "Failed to update playlist"}

    @handle_errors("reorder_tracks")
    async def reorder_tracks(
        self, playlist_id: str, track_order: List[int], client_op_id: str = None
    ) -> Dict[str, Any]:
        """Reorder tracks in a playlist using domain service with state broadcasting."""
        # Use domain services following DDD architecture
        from app.src.domain.services.track_reordering_service import (
            TrackReorderingService,
            ReorderingStrategy,
            ReorderingCommand,
        )

        # Get repository for data access
        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        # Get current playlist to extract tracks
        playlist_dict = await repo.get_playlist_by_id(playlist_id)
        if not playlist_dict:
            return {"status": "error", "message": "Playlist not found"}
        # Convert tracks to domain objects
        from app.src.domain.models.track import Track

        tracks = []
        for track_dict in playlist_dict.get("tracks", []):
            track = Track(
                track_number=track_dict.get("track_number", 0),
                title=track_dict.get("title", ""),
                filename=track_dict.get("filename", ""),
                file_path=track_dict.get("file_path", ""),
                duration_ms=track_dict.get("duration_ms"),
                artist=track_dict.get("artist"),
                album=track_dict.get("album"),
                id=track_dict.get("id"),
            )
            tracks.append(track)
        # Create domain service and command
        reordering_service = TrackReorderingService()
        command = ReorderingCommand(
            playlist_id=playlist_id,
            strategy=ReorderingStrategy.BULK_REORDER,
            track_numbers=track_order,
        )
        # Execute reordering through domain service
        result = reordering_service.execute_reordering(command, tracks)
        if result.success:
            # Apply changes to repository using the reordered tracks
            # The reordered tracks already have their new track_numbers assigned by the domain service
            old_to_new_mapping = {}
            for new_track in result.affected_tracks:
                # Find the original track number for this track using its ID
                original_track = next(
                    (orig_track for orig_track in tracks if orig_track.id == new_track.id), None
                )
                if original_track:
                    # Map: old track_number -> new track_number
                    old_to_new_mapping[original_track.track_number] = new_track.track_number
            # Apply to database
            success = repo.update_track_numbers(playlist_id, old_to_new_mapping)
            if success:
                logger.log(
                    LogLevel.INFO, f"✅ Reordered tracks using domain service: {playlist_id}"
                )
                logger.log(
                    LogLevel.DEBUG,
                    f"Domain service reordered {len(result.affected_tracks)} tracks: {result.original_order} -> {result.new_order}",
                )
                return {
                    "status": "success",
                    "message": "Tracks reordered successfully",
                    "playlist_id": playlist_id,
                    "client_op_id": client_op_id,
                }
            else:
                return {
                    "status": "error",
                    "message": "Domain service succeeded but repository update failed",
                }
        else:
            # Domain service validation failed
            error_messages = result.validation_errors + result.business_rule_violations
            logger.log(LogLevel.WARNING, f"❌ Domain service reordering failed: {error_messages}")
            return {
                "status": "error",
                "message": f"Reordering validation failed: {'; '.join(error_messages)}",
            }

    @handle_errors("delete_tracks")
    async def delete_tracks(
        self, playlist_id: str, track_numbers: List[int], client_op_id: str = None
    ) -> Dict[str, Any]:
        """Delete tracks from a playlist with state broadcasting and file cleanup."""

        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        # Get current playlist
        playlist = await repo.get_playlist_by_id(playlist_id)
        if not playlist:
            return {"status": "error", "message": "Playlist not found"}

        # Identify tracks to delete (for file cleanup)
        tracks_to_delete = [
            track
            for track in playlist.get("tracks", [])
            if track.get("track_number") in track_numbers
        ]

        # Filter out tracks to delete
        remaining_tracks = [
            track
            for track in playlist.get("tracks", [])
            if track.get("track_number") not in track_numbers
        ]

        # Replace tracks with remaining ones in database
        success = await repo.replace_tracks(playlist_id, remaining_tracks)
        if success:
            # Clean up physical files for deleted tracks
            await self._cleanup_deleted_track_files(tracks_to_delete)

            logger.log(
                LogLevel.INFO,
                f"✅ Deleted {len(track_numbers)} tracks from playlist: {playlist_id}",
            )
            return {
                "status": "success",
                "message": f"Deleted {len(track_numbers)} tracks successfully",
                "client_op_id": client_op_id,
            }
        else:
            return {"status": "error", "message": "Failed to delete tracks"}

    @handle_errors("get_playlist")
    async def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get a single playlist by ID."""

        from app.src.dependencies import get_playlist_repository_adapter
        repo = get_playlist_repository_adapter()
        return await repo.get_playlist_by_id(playlist_id)

    @handle_errors("handle_upload_complete")
    async def handle_upload_complete(
        self, playlist_id: str, track_data: Dict[str, Any], client_op_id: str = None
    ) -> Dict[str, Any]:
        """Handle upload completion with proper DDD architecture integration.

        Args:
            playlist_id: The playlist ID to add the track to
            track_data: Complete track information from upload service
            client_op_id: Client operation ID for deduplication

        Returns:
            Result dictionary with success/error status
        """
        try:
            logger.log(LogLevel.INFO, f"🎵 Processing upload completion for playlist {playlist_id}")

            # Add track to playlist using domain application service
            from app.src.application.services.playlist_application_service import (
                playlist_app_service,
            )

            # Prepare track data for domain service
            track_entry = {
                "title": track_data.get("title"),
                "filename": track_data.get("filename"),
                "file_path": track_data.get("file_path"),
                "duration_ms": track_data.get("duration"),  # Already in milliseconds
                "artist": track_data.get("artist"),
                "album": track_data.get("album"),
                "file_size": track_data.get("file_size"),
                "track_number": track_data.get("track_number", 1),
            }

            # Add track via domain application service
            add_result = await playlist_app_service.add_track_to_playlist_use_case(
                playlist_id=playlist_id, track_data=track_entry
            )

            if add_result.get("status") != "success":
                logger.log(
                    LogLevel.ERROR,
                    f"❌ Failed to add track to playlist: {add_result.get('message')}",
                )
                return {
                    "status": "error",
                    "message": add_result.get("message", "Failed to add track to playlist"),
                }

            # Get updated playlist for broadcasting
            playlist_result = await playlist_app_service.get_playlist_use_case(playlist_id)
            if playlist_result.get("status") == "success":
                updated_playlist = playlist_result.get("playlist")

                # Broadcast playlist state change via StateManager (server-authoritative)
                if self._state_manager:
                    from app.src.services.state_manager import StateEventType

                    await self._state_manager.broadcast_state_change(
                        StateEventType.PLAYLISTS_SNAPSHOT,
                        {"playlists": [updated_playlist]},
                        playlist_id=playlist_id,
                    )
                    logger.log(
                        LogLevel.INFO, f"✅ Broadcasted playlist update after upload: {playlist_id}"
                    )

            logger.log(
                LogLevel.INFO,
                f"🎉 Upload integration completed successfully for playlist {playlist_id}",
            )
            return {
                "status": "success",
                "message": "Track added to playlist and state broadcasted",
                "track": add_result.get("track"),
                "client_op_id": client_op_id,
            }

        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Upload completion integration failed: {str(e)}")
            return {"status": "error", "message": f"Upload integration failed: {str(e)}"}

    async def move_track_between_playlists(self, *args, **kwargs) -> Dict[str, Any]:
        """Move track between playlists - placeholder for compatibility."""
        logger.log(
            LogLevel.INFO, "Move track between playlists handled by UnifiedPlaylistController"
        )
        return {"status": "success", "message": "Track move handled"}

    # === Internal Methods ===

    @handle_errors("_notify_callbacks")
    async def _notify_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify registered callbacks about events."""
        callbacks = self._callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error in callback for {event_type}: {e}")

        # Also notify legacy state managers if available
        if hasattr(self, "_state_manager") and self._state_manager:
            await self._state_manager.emit_playback_state_changed()

        if self._player_state_service and hasattr(self._player_state_service, "broadcast_state"):
            await self._player_state_service.broadcast_state()

    def set_nfc_service(self, nfc_service):
        """Set NFC service for domain architecture integration.

        Args:
            nfc_service: The NFC service instance to integrate with
        """
        self._nfc_service = nfc_service
        logger.log(LogLevel.INFO, "✅ UnifiedPlaylistController NFC service integration configured")

    @handle_errors("handle_tag_scanned")
    async def handle_tag_scanned(
        self, tag_id: str, tag_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Handle NFC tag scanning for playlist playback.

        Args:
            tag_id: NFC tag identifier
            tag_data: Optional tag data from the NFC hardware

        Returns:
            True if tag was handled successfully, False otherwise
        """
        logger.log(LogLevel.INFO, f"🏷️ Handling NFC tag scan: {tag_id}")

        # Check if there are active association sessions - if so, skip playback
        if self._nfc_service and hasattr(self._nfc_service, "get_nfc_status_use_case"):
            try:
                nfc_status = await self._nfc_service.get_nfc_status_use_case()
                active_sessions = nfc_status.get("active_sessions", [])

                if active_sessions:
                    # Filter for actually active sessions (not completed/stopped)
                    listening_sessions = [
                        s for s in active_sessions if s.get("state") in ["listening", "LISTENING"]
                    ]

                    if listening_sessions:
                        logger.log(
                            LogLevel.INFO,
                            f"🔄 Tag {tag_id} detected during association mode - skipping playlist playback",
                        )
                        logger.log(
                            LogLevel.DEBUG,
                            f"Active association sessions: {len(listening_sessions)}",
                        )
                        return True  # Successfully handled (association in progress)

            except Exception as e:
                logger.log(LogLevel.WARNING, f"⚠️ Error checking NFC association status: {e}")
                # Continue with normal playback if we can't check association status

        # Normal scan-to-play behavior when no active association sessions
        success = await self.play_playlist_from_nfc(tag_id)
        if success:
            logger.log(LogLevel.INFO, f"✅ Successfully started playback for tag: {tag_id}")
        else:
            logger.log(LogLevel.WARNING, f"⚠️ No playlist found for tag: {tag_id}")
        return success

    def handle_tag_absence(self) -> None:
        """Handle when an NFC tag is removed.

        This method can be used to implement auto-pause functionality
        when tags are removed from the reader.
        """
        logger.log(LogLevel.DEBUG, "📤 NFC tag removed (tag absence detected)")
        # Future: Could implement auto-pause here if desired

    async def _cleanup_deleted_track_files(self, tracks_to_delete: List[Dict[str, Any]]) -> None:
        """Clean up physical files for deleted tracks."""
        if not tracks_to_delete:
            return

        from pathlib import Path
        import os

        logger.log(LogLevel.INFO, f"🗑️ Starting cleanup of {len(tracks_to_delete)} deleted track files")

        deleted_files = []
        failed_deletions = []

        for track in tracks_to_delete:
            file_path = track.get("file_path")
            track_title = track.get("title", "Unknown")

            if not file_path:
                logger.log(LogLevel.WARNING, f"⚠️ No file_path for track: {track_title}")
                continue

            try:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    os.remove(path)
                    deleted_files.append(str(path))
                    logger.log(LogLevel.INFO, f"✅ Deleted file: {path}")
                else:
                    logger.log(LogLevel.WARNING, f"⚠️ File not found or not a file: {path}")
            except Exception as e:
                failed_deletions.append(file_path)
                logger.log(LogLevel.ERROR, f"❌ Failed to delete file {file_path}: {e}")

        # Summary
        if deleted_files:
            logger.log(LogLevel.INFO, f"🗑️ Successfully deleted {len(deleted_files)} track files")
        if failed_deletions:
            logger.log(LogLevel.WARNING, f"⚠️ Failed to delete {len(failed_deletions)} track files")


# Global instance
unified_controller = UnifiedPlaylistController()
