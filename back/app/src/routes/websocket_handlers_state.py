# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Server-Authoritative WebSocket Handlers

This module implements WebSocket event handlers for the server-authoritative
state management system. Clients can subscribe to state updates and send
commands, but never maintain authoritative state.
"""

import time

import socketio

from app.src.monitoring import get_logger
from app.src.services.error.unified_error_decorator import handle_http_errors
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.state_manager import StateManager

logger = get_logger(__name__)


class WebSocketStateHandlers:
    """WebSocket handlers for server-authoritative state management."""

    def __init__(self, sio: socketio.AsyncServer, app, state_manager: StateManager):
        self.sio = sio
        self.app = app
        self.state_manager = state_manager

        # Set the Socket.IO server in state manager
        self.state_manager.socketio = sio

        logger.log(
            LogLevel.INFO,
            "WebSocketStateHandlers initialized with server-authoritative architecture",
        )

    def register(self):
        """Register all server-authoritative WebSocket event handlers."""

        @self.sio.event
        @handle_http_errors()
        async def connect(sid, environ):
            """Handle client connection and initial state sync."""
            logger.log(LogLevel.INFO, f"Client connected: {sid}")

            # Send connection acknowledgment with proper error handling
            await self.sio.emit(
                "connection_status",
                {
                    "status": "connected",
                    "sid": sid,
                    "server_seq": self.state_manager.get_global_sequence(),
                },
                room=sid,
            )

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection and cleanup subscriptions."""
            logger.log(LogLevel.INFO, f"Client disconnected: {sid}")

            # Unsubscribe client from all rooms
            await self.state_manager.unsubscribe_client(sid)

        @self.sio.on("join:playlists")
        @handle_http_errors()
        async def handle_join_playlists(sid, data):
            """Subscribe client to global playlists state updates."""
            logger.log(LogLevel.INFO, f"Client {sid} joining playlists room")
            await self.state_manager.subscribe_client(sid, "playlists")
            # Snapshot is sent by StateManager.subscribe_client via _send_state_snapshot
            # Send acknowledgment
            await self.sio.emit(
                "ack:join",
                {
                    "room": "playlists",
                    "success": True,
                    "server_seq": self.state_manager.get_global_sequence(),
                },
                room=sid,
            )
            logger.log(
                LogLevel.INFO,
                f"Client {sid} subscribed to playlists; snapshot will be sent by StateManager",
            )

        @self.sio.on("join:playlist")
        @handle_http_errors()
        async def handle_join_playlist(sid, data):
            """Subscribe client to specific playlist state updates."""
            playlist_id = data.get("playlist_id")
            if not playlist_id:
                raise ValueError("playlist_id is required")
            room = f"playlist:{playlist_id}"
            logger.log(LogLevel.INFO, f"Client {sid} joining playlist room: {room}")
            await self.state_manager.subscribe_client(sid, room)
            # Send acknowledgment
            await self.sio.emit(
                "ack:join",
                {
                    "room": room,
                    "playlist_id": playlist_id,
                    "success": True,
                    "playlist_seq": self.state_manager.get_playlist_sequence(playlist_id),
                },
                room=sid,
            )

        @self.sio.on("leave:playlists")
        @handle_http_errors()
        async def handle_leave_playlists(sid, data):
            """Unsubscribe client from global playlists updates."""
            logger.log(LogLevel.INFO, f"Client {sid} leaving playlists room")
            await self.state_manager.unsubscribe_client(sid, "playlists")
            await self.sio.emit("ack:leave", {"room": "playlists", "success": True}, room=sid)

        @self.sio.on("leave:playlist")
        @handle_http_errors()
        async def handle_leave_playlist(sid, data):
            """Unsubscribe client from specific playlist updates."""
            playlist_id = data.get("playlist_id")
            if not playlist_id:
                raise ValueError("playlist_id is required")
            room = f"playlist:{playlist_id}"
            logger.log(LogLevel.INFO, f"Client {sid} leaving playlist room: {room}")
            await self.state_manager.unsubscribe_client(sid, room)
            await self.sio.emit(
                "ack:leave", {"room": room, "playlist_id": playlist_id, "success": True}, room=sid
            )

        @self.sio.on("join:nfc")
        @handle_http_errors()
        async def handle_join_nfc(sid, data):
            """Subscribe client to NFC association session room and send snapshot."""
            assoc_id = data.get("assoc_id")
            if not assoc_id:
                raise ValueError("assoc_id is required")
            room = f"nfc:{assoc_id}"
            logger.log(LogLevel.INFO, f"Client {sid} joining NFC room: {room}")
            await self.state_manager.subscribe_client(sid, room)
            # Send current snapshot
            container = getattr(self.app, "container", None)
            nfc_service = getattr(container, "nfc", None) if container else None
            if nfc_service and hasattr(nfc_service, "get_session_snapshot"):
                snapshot = await nfc_service.get_session_snapshot(assoc_id)
                if snapshot:
                    await self.sio.emit("nfc_status", snapshot, room=sid)
            # Ack join
            await self.sio.emit("ack:join", {"room": room, "success": True}, room=sid)

        @self.sio.on("sync:request")
        @handle_http_errors()
        async def handle_sync_request(sid, data):
            """Handle client request for state synchronization."""
            # Get client's last known sequence numbers
            last_global_seq = data.get("last_global_seq", 0)
            last_playlist_seqs = data.get("last_playlist_seqs", {})
            logger.log(LogLevel.INFO, f"Sync request from {sid}: global_seq={last_global_seq}")
            # Send current global state if client is behind
            current_global_seq = self.state_manager.get_global_sequence()
            if last_global_seq < current_global_seq:
                # Client needs full resync - send snapshots for subscribed rooms
                subscriptions = self.state_manager.get_client_subscriptions(sid)
                for room in subscriptions:
                    await self.state_manager._send_state_snapshot(sid, room)
            # Send sync acknowledgment
            await self.sio.emit(
                "sync:complete",
                {
                    "current_global_seq": current_global_seq,
                    "synced_rooms": list(self.state_manager.get_client_subscriptions(sid)),
                },
                room=sid,
            )

        # WebSocket commands removed per API Contract v2.0
        # All commands now use HTTP endpoints only
        # State updates are broadcast via canonical events
        # NFC Association WebSocket Handlers
        @self.sio.on("start_nfc_link")
        @handle_http_errors()
        async def handle_start_nfc_link(sid, data):
            """Handle NFC association start via WebSocket."""
            playlist_id = data.get("playlist_id")
            client_op_id = data.get("client_op_id")
            if not playlist_id:
                raise ValueError("playlist_id is required")
            logger.log(
                LogLevel.INFO,
                f"Starting NFC association for playlist {playlist_id} from client {sid}",
            )
            # Get NFC service from container
            container = getattr(self.app, "container", None)
            nfc_service = getattr(container, "nfc", None) if container else None
            if not nfc_service:
                raise Exception("NFC service not available")
            # Start association using the service
            result = await nfc_service.start_association_use_case(playlist_id)
            # Emit state update to client
            await self.sio.emit(
                "nfc_association_state",
                {
                    "state": "activated",
                    "playlist_id": playlist_id,
                    "expires_at": result.get("expires_at"),
                    "server_seq": self.state_manager.get_global_sequence(),
                },
                room=sid,
            )
            # Send acknowledgment if client_op_id provided
            if client_op_id:
                await self.state_manager.send_acknowledgment(
                    client_op_id,
                    True,
                    {"assoc_id": result.get("assoc_id"), "playlist_id": playlist_id},
                )
            logger.log(
                LogLevel.INFO, f"NFC association started successfully for playlist {playlist_id}"
            )

        @self.sio.on("stop_nfc_link")
        @handle_http_errors()
        async def handle_stop_nfc_link(sid, data):
            """Handle NFC association cancellation via WebSocket."""
            playlist_id = data.get("playlist_id")
            client_op_id = data.get("client_op_id")
            if not playlist_id:
                raise ValueError("playlist_id is required")
            logger.log(
                LogLevel.INFO,
                f"Stopping NFC association for playlist {playlist_id} from client {sid}",
            )
            # Get NFC service from container
            container = getattr(self.app, "container", None)
            nfc_service = getattr(container, "nfc", None) if container else None
            if not nfc_service:
                raise Exception("NFC service not available")
            # Cancel association - need to find the association ID
            # For now, we'll use a simplified approach
            result = await nfc_service.cancel_association_by_playlist(playlist_id)
            # Emit cancelled state
            await self.sio.emit(
                "nfc_association_state",
                {
                    "state": "cancelled",
                    "playlist_id": playlist_id,
                    "message": "Association cancelled by user",
                    "server_seq": self.state_manager.get_global_sequence(),
                },
                room=sid,
            )
            # Send acknowledgment
            if client_op_id:
                await self.state_manager.send_acknowledgment(
                    client_op_id, True, {"playlist_id": playlist_id, "status": "cancelled"}
                )
            logger.log(LogLevel.INFO, f"NFC association cancelled for playlist {playlist_id}")

        @self.sio.on("override_nfc_tag")
        @handle_http_errors()
        async def handle_override_nfc_tag(sid, data):
            """Handle NFC tag override via WebSocket."""
            playlist_id = data.get("playlist_id")
            client_op_id = data.get("client_op_id")
            if not playlist_id:
                raise ValueError("playlist_id is required")
            logger.log(
                LogLevel.INFO, f"Overriding NFC tag for playlist {playlist_id} from client {sid}"
            )
            # Get NFC service from container
            container = getattr(self.app, "container", None)
            nfc_service = getattr(container, "nfc", None) if container else None
            if not nfc_service:
                raise Exception("NFC service not available")
            # Start association in override mode
            result = await nfc_service.start_association_use_case(playlist_id)
            # If there's already a detected tag in duplicate state, process it immediately
            if hasattr(nfc_service, "_active_assoc_id") and nfc_service._active_assoc_id:
                session = nfc_service._assoc_sessions.get(nfc_service._active_assoc_id)
                if session and hasattr(session, "tag_id") and session.tag_id:
                    logger.log(
                        LogLevel.INFO,
                        f"Processing previously detected tag {session.tag_id} in override mode",
                    )
                    # Use the NFC service detection handler to process the tag
                    await nfc_service.handle_tag_detected(session.tag_id)
            # Emit waiting state for override
            await self.sio.emit(
                "nfc_association_state",
                {
                    "state": "waiting",
                    "playlist_id": playlist_id,
                    "expires_at": result.get("expires_at"),
                    "message": "Place NFC tag to override existing association",
                    "server_seq": self.state_manager.get_global_sequence(),
                },
                room=sid,
            )
            # Send acknowledgment
            if client_op_id:
                await self.state_manager.send_acknowledgment(
                    client_op_id,
                    True,
                    {
                        "assoc_id": result.get("assoc_id"),
                        "playlist_id": playlist_id,
                        "override": True,
                    },
                )
            logger.log(LogLevel.INFO, f"NFC tag override started for playlist {playlist_id}")

        # Connection health monitoring
        @self.sio.on("client_ping")
        @handle_http_errors()
        async def handle_client_ping(sid, data):
            """Handle client ping for connection health monitoring."""
            await self.sio.emit(
                "client_pong",
                {
                    "timestamp": data.get("timestamp", time.time()),
                    "server_time": time.time(),
                    "server_seq": self.state_manager.get_global_sequence(),
                },
                room=sid,
            )

        @self.sio.on("health_check")
        @handle_http_errors()
        async def handle_health_check(sid, data):
            """Handle client health check request."""
            health_metrics = await self.state_manager.get_health_metrics()
            health_metrics.update(
                {
                    "connected_clients": len(self.sio.manager.rooms.get("/", {})),
                    "server_time": time.time(),
                }
            )
            await self.sio.emit("health_status", health_metrics, room=sid)

        # Post-connection state synchronization
        @self.sio.on("client:request_current_state")
        @handle_http_errors()
        async def handle_request_current_state(sid, data):
            """Handle client request for current state synchronization."""
            logger.log(LogLevel.INFO, f"🔄 Client {sid} requesting current state sync")
            # Get current player state and broadcast to specific client
            from ..services.player_state_service import player_state_service

            # Get playlist routes state from app attribute instead of global import
            playlist_routes_state = getattr(self.app, "playlist_routes_state", None)
            if playlist_routes_state:
                audio_controller = playlist_routes_state.audio_controller
                if audio_controller:
                    # Build current player state
                    player_state = await player_state_service.build_current_player_state(
                        audio_controller, self.state_manager
                    )

                    # Handle both PlayerStateModel and dict returns
                    if hasattr(player_state, 'server_seq'):
                        # PlayerStateModel case
                        server_seq = player_state.server_seq
                        data = player_state.model_dump()
                        playlist_title = getattr(player_state, 'active_playlist_title', None)
                    else:
                        # dict case (fallback scenario)
                        server_seq = player_state.get('server_seq', 0)
                        data = player_state
                        playlist_title = player_state.get('active_playlist_title', 'None')

                    # Send current player state to requesting client
                    await self.sio.emit(
                        "state:player",
                        {
                            "event_type": "state:player",
                            "server_seq": server_seq,
                            "data": data,
                            "timestamp": time.time(),
                            "event_id": f"sync_{int(time.time() * 1000)}",
                        },
                        room=sid,
                    )
                    logger.log(
                        LogLevel.INFO,
                        f"✅ Sent current player state to client {sid}: {playlist_title}",
                    )
                else:
                    logger.log(
                        LogLevel.WARNING, f"⚠️ No audio controller available for state sync to {sid}"
                    )
            else:
                logger.log(
                    LogLevel.WARNING, f"⚠️ No playlist routes state available for sync to {sid}"
                )

        logger.log(LogLevel.INFO, "Server-authoritative WebSocket handlers registered successfully")
