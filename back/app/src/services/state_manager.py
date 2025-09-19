# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Streamlined Server-Authoritative State Manager

Refactored StateManager using focused, single-responsibility classes.
Coordinates between EventOutbox, ClientSubscriptionManager, SequenceGenerator, and OperationTracker.
"""

import asyncio
import json
import time
import uuid
from typing import Any, Dict, Optional, Set
from enum import Enum

from app.src.monitoring import get_logger
from app.src.services.error.unified_error_decorator import handle_service_errors
from app.src.monitoring.logging.log_level import LogLevel
from app.src.common.socket_events import SocketEventType, get_event_room, SocketEventBuilder
from app.src.config.socket_config import socket_config
from app.src.services.event_outbox import EventOutbox
from app.src.services.client_subscription_manager import ClientSubscriptionManager
from app.src.services.sequence_generator import SequenceGenerator
from app.src.services.operation_tracker import OperationTracker

logger = get_logger(__name__)


class StateEventType(Enum):
    """Types of state events that can be broadcast per API Contract v2.0."""

    PLAYLISTS_SNAPSHOT = "state:playlists"
    PLAYLISTS_INDEX_UPDATE = "state:playlists_index_update"
    PLAYLIST_SNAPSHOT = "state:playlist"
    TRACK_SNAPSHOT = "state:track"
    PLAYER_STATE = "state:player"
    TRACK_PROGRESS = "state:track_progress"
    TRACK_POSITION = "state:track_position"

    PLAYLIST_DELETED = "state:playlist_deleted"
    PLAYLIST_CREATED = "state:playlist_created"
    PLAYLIST_UPDATED = "state:playlist_updated"
    TRACK_DELETED = "state:track_deleted"
    TRACK_ADDED = "state:track_added"

    VOLUME_CHANGED = "state:volume_changed"
    NFC_STATE = "state:nfc_state"


@handle_service_errors("state_manager")
def _convert_state_event_type_to_socket_event_type(
    state_event_type: StateEventType,
) -> SocketEventType:
    """Convert StateEventType to SocketEventType for compatibility."""
    conversion_map = {
        "state:playlists": SocketEventType.STATE_PLAYLISTS,
        "state:playlists_index_update": SocketEventType.STATE_PLAYLISTS_INDEX_UPDATE,
        "state:playlist": SocketEventType.STATE_PLAYLIST,
        "state:player": SocketEventType.STATE_PLAYER,
        "state:track_progress": SocketEventType.STATE_TRACK_PROGRESS,
        "state:track_position": SocketEventType.STATE_TRACK_POSITION,
        "state:track": SocketEventType.STATE_TRACK,
        "state:playlist_created": SocketEventType.STATE_PLAYLIST_CREATED,
        "state:playlist_updated": SocketEventType.STATE_PLAYLIST_UPDATED,
        "state:playlist_deleted": SocketEventType.STATE_PLAYLIST_DELETED,
        "state:track_added": SocketEventType.STATE_TRACK_ADDED,
        "state:track_deleted": SocketEventType.STATE_TRACK_DELETED,
    }

    socket_event_type = conversion_map.get(state_event_type.value)
    if socket_event_type is None:
        return SocketEventType(state_event_type.value)
    return socket_event_type


class StateManager:
    """
    Streamlined server-authoritative state manager.

    Coordinates focused components for clean separation of concerns:
    - EventOutbox: Reliable event delivery
    - ClientSubscriptionManager: Room subscriptions
    - SequenceGenerator: Event ordering
    - OperationTracker: Deduplication
    """

    def __init__(self, socketio_server=None):
        self.socketio = socketio_server
        # Pure domain architecture initialized

        # Initialize focused components
        self.outbox = EventOutbox(socketio_server)
        self.subscriptions = ClientSubscriptionManager(socketio_server)
        self.sequences = SequenceGenerator()
        self.operations = OperationTracker()

        # Position update throttling
        self._last_position_emit_time = 0

        # Cleanup task management
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5 minutes

        logger.log(LogLevel.INFO, "StateManager initialized with focused components")

    async def subscribe_client(self, client_id: str, room: str) -> None:
        """Subscribe a client to a specific room for state updates."""
        await self.subscriptions.subscribe_client(client_id, room)

        # Send current state snapshot to newly subscribed client
        await self._send_state_snapshot(client_id, room)

    async def unsubscribe_client(self, client_id: str, room: Optional[str] = None) -> None:
        """Unsubscribe a client from a room or all rooms."""
        await self.subscriptions.unsubscribe_client(client_id, room)

    async def is_operation_processed(self, client_op_id: str) -> bool:
        """Check if a client operation has already been processed."""
        return await self.operations.is_operation_processed(client_op_id)

    async def mark_operation_processed(self, client_op_id: str, result: Any = None) -> None:
        """Mark a client operation as processed with optional result caching."""
        await self.operations.mark_operation_processed(client_op_id, result)

    async def get_operation_result(self, client_op_id: str) -> Optional[Any]:
        """Get cached result for a processed operation."""
        return await self.operations.get_operation_result(client_op_id)

    @handle_service_errors("state_manager")
    async def broadcast_state_change(
        self,
        event_type: StateEventType,
        data: Dict[str, Any],
        playlist_id: Optional[str] = None,
        room: Optional[str] = None,
        immediate: bool = False,
    ) -> dict:
        """
        Broadcast a state change to all subscribed clients.

        Args:
            event_type: Type of state event
            data: Event data to broadcast
            playlist_id: Optional playlist ID for playlist-specific events
            room: Optional specific room to broadcast to
            immediate: If True, process outbox immediately for real-time delivery

        Returns:
            The created event envelope
        """
        # Get sequence numbers
        server_seq = await self.sequences.get_next_global_seq()
        if playlist_id:
            data["playlist_seq"] = await self.sequences.get_next_playlist_seq(playlist_id)

        # Convert to SocketEventType
        socket_event_type = _convert_state_event_type_to_socket_event_type(event_type)

        # Create standardized event envelope
        envelope = {
            "event_type": event_type.value,
            "server_seq": server_seq,
            "data": data,
            "timestamp": int(time.time() * 1000),
            "event_id": str(uuid.uuid4())[:8],
        }

        if playlist_id:
            envelope["playlist_id"] = playlist_id
            envelope["playlist_seq"] = data.get("playlist_seq")

        # Add to outbox for reliable delivery
        await self.outbox.add_event(
            event_id=envelope["event_id"],
            event_type=envelope["event_type"],
            payload=envelope,
            server_seq=server_seq,
            playlist_id=playlist_id,
        )

        # Broadcast immediately if Socket.IO is available
        if self.socketio:
            await self._broadcast_event(envelope, room, socket_event_type, playlist_id)
        # Process outbox immediately if requested
        if immediate:
            await self.outbox.process_outbox()

        # Log state changes except frequent position updates
        if event_type != StateEventType.TRACK_POSITION:
            logger.log(
                LogLevel.INFO, f"State change broadcasted: {event_type.value} (seq: {server_seq})"
            )
        elif not hasattr(self, "_position_state_logged"):
            logger.log(
                LogLevel.INFO, f"📡 FIRST position state change broadcasted (seq: {server_seq})"
            )
            self._position_state_logged = True

        return envelope

    async def broadcast_position_update(
        self, position_ms: int, track_id: str, is_playing: bool, duration_ms: Optional[int] = None
    ) -> Optional[dict]:
        """
        Broadcast a lightweight position update with throttling.

        Args:
            position_ms: Current playback position in milliseconds
            track_id: ID of the currently playing track
            is_playing: Whether playback is active
            duration_ms: Optional track duration

        Returns:
            Event envelope if broadcasted, None if throttled
        """
        # Throttle position updates
        current_time = time.time()
        if (
            current_time - self._last_position_emit_time
            < socket_config.POSITION_THROTTLE_MIN_MS / 1000
        ):
            return None

        self._last_position_emit_time = current_time

        # Log every 10 seconds (10 events at 1000ms interval)
        if not hasattr(self, "_position_log_counter"):
            self._position_log_counter = 0
        self._position_log_counter += 1

        if self._position_log_counter % 10 == 0:
            logger.log(
                LogLevel.DEBUG,
                f"Broadcasting position update #{self._position_log_counter}: {position_ms}ms, playing={is_playing}",
            )

        # Create minimal payload
        data = {"position_ms": position_ms, "track_id": track_id, "is_playing": is_playing}

        if duration_ms is not None:
            data["duration_ms"] = duration_ms

        # Broadcast with immediate processing for real-time updates
        return await self.broadcast_state_change(
            StateEventType.TRACK_POSITION, data, immediate=True
        )

    async def emit_playlists_index_update(self, updates: list) -> dict:
        """
        Emit playlists index update events.

        Args:
            updates: List of update operations with format:
                     [{"type": "upsert", "item": {...}}, {"type": "delete", "id": "..."}]

        Returns:
            The created event envelope
        """
        data = {"updates": updates}

        return await self.broadcast_state_change(
            StateEventType.PLAYLISTS_INDEX_UPDATE, data, immediate=True
        )

    @handle_service_errors("state_manager")
    @handle_service_errors("state_manager")
    async def _broadcast_event(
        self,
        envelope: dict,
        room: Optional[str],
        socket_event_type: SocketEventType,
        playlist_id: Optional[str],
    ) -> None:
        """Broadcast a state event to clients using standardized envelope format."""
        if not self.socketio:
            return

        json.dumps(envelope)

        if room:
            # Broadcast to specific room
            await self.socketio.emit(envelope["event_type"], envelope, room=room)
        else:
            # Use standardized room routing
            target_room = get_event_room(socket_event_type, playlist_id)
            await self.socketio.emit(envelope["event_type"], envelope, room=target_room)
            # Log first position event and all other events
            if socket_event_type == SocketEventType.STATE_TRACK_POSITION:
                if not hasattr(self, "_first_position_logged"):
                    logger.log(
                        LogLevel.INFO,
                        f"🎯 FIRST state:track_position broadcasted to '{target_room}' (seq: {envelope['server_seq']})",
                    )
                    self._first_position_logged = True
            elif socket_event_type != SocketEventType.STATE_TRACK_PROGRESS:
                logger.log(
                    LogLevel.INFO,
                    f"Broadcasted {envelope['event_type']} to room '{target_room}' (seq: {envelope['server_seq']})",
                )

    @handle_service_errors("state_manager")
    async def _send_state_snapshot(self, client_id: str, room: str) -> None:
        """Send current state snapshot to a newly subscribed client."""
        if not self.socketio:
            return

        if room == "playlists":
            # Send playlists snapshot
            await self._send_playlists_snapshot(client_id)
        elif room.startswith("playlist:"):
            # Send specific playlist snapshot
            playlist_id = room.split(":", 1)[1]
            await self._send_playlist_snapshot(client_id, playlist_id)

    @handle_service_errors("state_manager")
    async def _send_playlists_snapshot(self, client_id: str) -> None:
        """Send playlists snapshot to client."""
        # Pure domain architecture - use application service
        from app.src.application.services.playlist_application_service import (
            PlaylistApplicationService,
        )

        # Get playlist repository and initialize application service

        from app.src.dependencies import get_playlist_repository_adapter
        playlist_repository = get_playlist_repository_adapter()
        playlist_app_service = PlaylistApplicationService(playlist_repository)
        # Get all playlists via application service
        playlists_result = await playlist_app_service.get_all_playlists_use_case()
        if playlists_result["status"] == "success":
            playlists = playlists_result.get("playlists", [])
        else:
            # Pure domain architecture - use unified controller as fallback
            from app.src.domain.controllers.unified_controller import unified_controller

            playlists = (
                await unified_controller.get_all_playlists()
                if unified_controller.is_initialized
                else []
            )
        playlists_data = [self._serialize_playlist(p) for p in playlists]
        await self.socketio.emit(
            StateEventType.PLAYLISTS_SNAPSHOT.value,
            {
                "event_type": StateEventType.PLAYLISTS_SNAPSHOT.value,
                "server_seq": self.sequences.get_current_global_seq(),
                "data": {"playlists": playlists_data},
                "timestamp": int(time.time() * 1000),
            },
            room=client_id,
        )

    @handle_service_errors("state_manager")
    async def _send_playlist_snapshot(self, client_id: str, playlist_id: str) -> None:
        """Send specific playlist snapshot to client."""
        # Pure domain architecture - use application service
        from app.src.application.services.playlist_application_service import (
            PlaylistApplicationService,
        )

        # Get playlist repository and initialize application service

        from app.src.dependencies import get_playlist_repository_adapter
        playlist_repository = get_playlist_repository_adapter()
        playlist_app_service = PlaylistApplicationService(playlist_repository)
        # Get specific playlist via application service
        playlist_result = await playlist_app_service.get_playlist_use_case(playlist_id)
        if playlist_result["status"] == "success":
            playlist = playlist_result.get("playlist")
        else:
            # Pure domain architecture - use unified controller as fallback
            from app.src.domain.controllers.unified_controller import unified_controller

            # Note: unified_controller doesn't have get_playlist method, use app service directly
            playlist = None  # Graceful degradation
        if playlist:
            playlist_data = self._serialize_playlist(playlist)
            await self.socketio.emit(
                StateEventType.PLAYLIST_SNAPSHOT.value,
                {
                    "event_type": StateEventType.PLAYLIST_SNAPSHOT.value,
                    "server_seq": self.sequences.get_current_global_seq(),
                    "playlist_id": playlist_id,
                    "playlist_seq": self.sequences.get_current_playlist_seq(playlist_id),
                    "data": playlist_data,
                    "timestamp": int(time.time() * 1000),
                },
                room=client_id,
            )

    def _serialize_playlist(self, playlist) -> Dict[str, Any]:
        """Serialize a playlist object or dict for transmission."""
        if isinstance(playlist, dict):
            return {
                "id": playlist.get("id"),
                "title": playlist.get("title") or playlist.get("name", ""),
                "description": playlist.get("description", ""),
                "nfc_tag_id": playlist.get("nfc_tag_id"),
                "tracks": [self._serialize_track(track) for track in playlist.get("tracks", [])],
                "track_count": playlist.get("track_count", len(playlist.get("tracks", []))),
                "created_at": playlist.get("created_at"),
                "updated_at": playlist.get("updated_at"),
                "server_seq": self.sequences.get_current_global_seq(),
                "playlist_seq": self.sequences.get_current_playlist_seq(playlist.get("id")),
            }
        else:
            return {
                "id": playlist.id,
                "title": playlist.title,
                "description": getattr(playlist, "description", ""),
                "nfc_tag_id": getattr(playlist, "nfc_tag_id", None),
                "tracks": [
                    self._serialize_track(track) for track in getattr(playlist, "tracks", [])
                ],
                "track_count": getattr(
                    playlist, "track_count", len(getattr(playlist, "tracks", []))
                ),
                "created_at": getattr(playlist, "created_at", None),
                "updated_at": getattr(playlist, "updated_at", None),
                "server_seq": self.sequences.get_current_global_seq(),
                "playlist_seq": self.sequences.get_current_playlist_seq(playlist.id),
            }

    def _serialize_track(self, track) -> Dict[str, Any]:
        """Serialize a track object or dict for transmission."""
        if isinstance(track, dict):
            return track
        else:
            return {
                "id": track.id,
                "title": track.title,
                "filename": track.filename,
                "duration_ms": int((track.duration or 0) * 1000),
                "artist": getattr(track, "artist", None),
                "album": getattr(track, "album", None),
                "track_number": getattr(track, "number", None),
                "play_count": getattr(track, "play_count", 0),
                "created_at": getattr(track, "created_at", None),
                "server_seq": self.sequences.get_current_global_seq(),
            }

    async def process_outbox(self) -> None:
        """Process the event outbox for reliable delivery."""
        await self.outbox.process_outbox()

    @handle_service_errors("state_manager")
    async def send_acknowledgment(
        self,
        client_op_id: str,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        client_id: Optional[str] = None,
    ) -> None:
        """Send acknowledgment for a client operation."""
        if not self.socketio:
            return

        payload = SocketEventBuilder.create_operation_ack_event(
            client_op_id=client_op_id,
            success=success,
            server_seq=self.sequences.get_current_global_seq(),
            data=data,
            message=None if success else "Operation failed",
        )

        event = "ack:op" if success else "err:op"
        if client_id:
            await self.socketio.emit(event, payload, room=client_id)
        else:
            await self.socketio.emit(event, payload, room="playlists")

    # Getters for compatibility
    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """Get all rooms a client is subscribed to."""
        return self.subscriptions.get_client_subscriptions(client_id)

    def get_global_sequence(self) -> int:
        """Get current global sequence number."""
        return self.sequences.get_current_global_seq()

    def get_playlist_sequence(self, playlist_id: str) -> int:
        """Get current sequence number for a playlist."""
        return self.sequences.get_current_playlist_seq(playlist_id)

    async def start_cleanup_task(self) -> None:
        """Start a background task to periodically clean up expired operations and outbox events."""
        if self._cleanup_task:
            logger.log(LogLevel.WARNING, "Cleanup task already running")
            return

        logger.log(
            LogLevel.INFO, f"Starting periodic cleanup task (interval: {self._cleanup_interval}s)"
        )
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop the periodic cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.log(LogLevel.INFO, "Cleanup task stopped")

    @handle_service_errors("state_manager")
    async def _cleanup_loop(self) -> None:
        """Internal cleanup loop that runs periodically."""
        logger.log(LogLevel.INFO, "StateManager cleanup loop started")

        while True:
            try:
                # Clean up expired operations
                cleaned_ops = await self.operations.cleanup_expired_operations()
                # Process outbox to handle any failed events
                await self.outbox.process_outbox()
                # Log metrics periodically (every hour)
                if time.time() % 3600 < self._cleanup_interval:
                    metrics = await self.get_health_metrics()
                    logger.log(LogLevel.INFO, f"StateManager metrics: {metrics}")
                if cleaned_ops > 0:
                    logger.log(
                        LogLevel.DEBUG, f"Cleanup completed: {cleaned_ops} operations cleaned"
                    )

                # CRITICAL: Sleep to prevent blocking the event loop
                await asyncio.sleep(self._cleanup_interval)

            except asyncio.CancelledError:
                logger.log(LogLevel.INFO, "StateManager cleanup loop cancelled")
                break
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error in StateManager cleanup loop: {e}")
                # Continue after error, but still sleep
                await asyncio.sleep(self._cleanup_interval)

    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics from all components."""
        return {
            "sequences": self.sequences.get_stats(),
            "subscriptions": self.subscriptions.get_stats(),
            "operations": self.operations.get_stats(),
            "outbox": self.outbox.get_stats(),
            "last_position_update": self._last_position_emit_time,
            "cleanup_task_running": self._cleanup_task is not None
            and not self._cleanup_task.done(),
        }
