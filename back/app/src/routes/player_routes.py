# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Standardized Player Routes for TheOpenMusicBox.

This module provides consistent, standardized player control endpoints
using unified response formats, error handling, and state management.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import Field
from typing import Optional
import time
from collections import defaultdict

from ..common.response_models import ClientOperationRequest
from app.src.services.response.unified_response_service import UnifiedResponseService
from app.src.services.error.unified_error_decorator import handle_http_errors
from app.src.domain.error_handling.unified_error_handler import (
    unified_error_handler as ErrorHandler,
    rate_limit_error,
    service_unavailable_error,
    bad_request_error,
)
from ..common.socket_events import SocketEventType
from ..services.player_state_service import player_state_service
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 30  # max requests per window
rate_limit_store = defaultdict(lambda: {"count": 0, "window_start": 0})


class SeekRequest(ClientOperationRequest):
    """Request model for seek operations."""

    position_ms: int = Field(
        ..., ge=0, le=86400000, description="Position in milliseconds (max 24 hours)"
    )


class VolumeRequest(ClientOperationRequest):
    """Request model for volume operations."""

    volume: int = Field(..., ge=0, le=100, description="Volume level (0-100)")


class PlayerControlRequest(ClientOperationRequest):
    """Base request model for player control operations."""

    pass


def get_audio_controller(request: Request):
    """Resolve AudioController using domain-driven architecture only."""
    # Primary: Use the instance managed by PlaylistRoutesState (shared state)
    prs = getattr(request.app, "playlist_routes_state", None)
    if prs and getattr(prs, "audio_controller", None):
        return prs.audio_controller
    # Domain-driven approach: Create AudioController with domain architecture
    from app.src.controllers.audio_controller import AudioController
    from app.src.domain.bootstrap import domain_bootstrap
    from app.src.domain.audio.container import audio_domain_container

    # Initialize domain if not already done
    if not domain_bootstrap.is_initialized:
        domain_bootstrap.initialize()
    # Try to get audio engine from domain container
    if audio_domain_container.is_initialized:
        audio_engine = audio_domain_container.audio_engine
        logger.log(
            LogLevel.INFO,
            f"Using domain audio engine for AudioController: {type(audio_engine).__name__}",
        )
        return AudioController(audio_engine)


def get_state_manager(request: Request):
    """Resolve the StateManager for broadcasting player state events."""
    sm = getattr(request.app, "state_manager", None)
    if sm:
        return sm

    container = getattr(request.app, "container", None)
    state_manager = getattr(container, "state_manager", None) if container else None
    if not state_manager:
        logger.log(LogLevel.WARNING, "State manager not available in container")
    return state_manager


def check_rate_limit(client_id: str) -> bool:
    """Check if client is within rate limits."""
    current_time = int(time.time())
    client_data = rate_limit_store[client_id]

    # Reset window if expired
    if current_time - client_data["window_start"] >= RATE_LIMIT_WINDOW:
        client_data["count"] = 0
        client_data["window_start"] = current_time

    # Check rate limit
    if client_data["count"] >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Increment counter
    client_data["count"] += 1
    return True


def get_client_id(request: Request) -> str:
    """Get client identifier for rate limiting."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def validate_client_op_id(client_op_id: Optional[str]) -> str:
    """Validate and sanitize client operation ID."""
    if not client_op_id:
        return f"auto_{int(time.time() * 1000)}_{hash(time.time()) & 0x7FFFFFFF}"

    # Sanitize client_op_id
    import re

    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", client_op_id)
    if len(sanitized) < 3:
        sanitized = f"client_{sanitized}_{int(time.time())}"
    return sanitized[:100]  # Limit length


class PlayerRoutes:
    """Standardized Player routes with unified response handling."""

    def __init__(self, app, socketio):
        """Initialize PlayerRoutes with FastAPI app and Socket.IO server."""
        self.app = app
        self.socketio = socketio
        self.router = APIRouter()
        self.error_handler = ErrorHandler
        self._register_routes()

    def _register_routes(self):
        """Register all player-related API routes with standardized handling."""

        @self.router.post("/stop")
        @handle_http_errors()
        async def stop_player(
            request: Request,
            body: PlayerControlRequest = PlayerControlRequest(),
            audio_controller=Depends(get_audio_controller),
            state_manager=Depends(get_state_manager),
        ):
            """Stop current playbook."""
            if not audio_controller:
                raise service_unavailable_error("Audio controller")
            client_op_id = validate_client_op_id(body.client_op_id)
            # Execute stop command
            result = await audio_controller.handle_playback_control("stop")
            if result.get("status") == "success":
                # Stop the TrackProgressService
                from app.src.routes.playlist_routes_state import playlist_routes_state

                if playlist_routes_state and hasattr(playlist_routes_state, "progress_service"):
                    await playlist_routes_state.progress_service.stop()
                    logger.log(LogLevel.INFO, "TrackProgressService stopped")
                # Build stopped player state
                player_state = await player_state_service.build_stopped_player_state(state_manager)
                # Broadcast state change
                if state_manager:
                    await state_manager.broadcast_state_change(
                        SocketEventType.STATE_PLAYER, player_state.model_dump()
                    )
                    # Send acknowledgment
                    if client_op_id:
                        await state_manager.send_acknowledgment(
                            client_op_id, True, player_state.model_dump()
                        )
                logger.log(LogLevel.INFO, "Stop: Successfully stopped playback")
                # Return wrapped response as per standardized API format
                return UnifiedResponseService.success(
                    message="Player stopped successfully",
                    data=player_state.model_dump(),
                    server_seq=player_state.server_seq,
                )
            else:
                error_message = result.get("error", "Stop operation failed")
                raise bad_request_error(error_message)

        @self.router.post("/next")
        async def next_track(
            request: Request,
            body: PlayerControlRequest = PlayerControlRequest(),
            audio_controller=Depends(get_audio_controller),
            state_manager=Depends(get_state_manager),
        ):
            """Skip to next track."""
            return await self._handle_navigation_command(
                request, body, audio_controller, state_manager, "next"
            )

        @self.router.post("/previous")
        async def previous_track(
            request: Request,
            body: PlayerControlRequest = PlayerControlRequest(),
            audio_controller=Depends(get_audio_controller),
            state_manager=Depends(get_state_manager),
        ):
            """Skip to previous track."""
            return await self._handle_navigation_command(
                request, body, audio_controller, state_manager, "previous"
            )

        @self.router.post("/toggle")
        @handle_http_errors()
        async def toggle_playback(
            request: Request,
            body: PlayerControlRequest = PlayerControlRequest(),
            audio_controller=Depends(get_audio_controller),
            state_manager=Depends(get_state_manager),
        ):
            """Toggle between play and pause."""
            # Rate limiting
            client_id = get_client_id(request)
            if not check_rate_limit(client_id):
                raise rate_limit_error("Too many player control requests")
            if not audio_controller:
                raise service_unavailable_error("Audio controller")
            client_op_id = validate_client_op_id(body.client_op_id)
            # Execute toggle command
            result = await audio_controller.handle_playback_control("toggle")
            if result.get("status") == "success":
                # Build unified player state
                player_state = await player_state_service.build_current_player_state(
                    audio_controller, state_manager
                )
                # Broadcast state change
                if state_manager:
                    await state_manager.broadcast_state_change(
                        SocketEventType.STATE_PLAYER, player_state.model_dump()
                    )
                    # Send acknowledgment
                    if client_op_id:
                        await state_manager.send_acknowledgment(
                            client_op_id, True, player_state.model_dump()
                        )
                # Trigger immediate progress update for UI responsiveness
                await self._trigger_immediate_progress(request)
                logger.log(
                    LogLevel.INFO,
                    f"Toggle: Successfully toggled - is_playing={player_state.is_playing}",
                )
                # Return wrapped response as per standardized API format
                return UnifiedResponseService.success(
                    message="Playback toggled successfully",
                    data=player_state.model_dump(),
                    server_seq=player_state.server_seq,
                )
            else:
                error_message = result.get("error", "Toggle operation failed")
                raise bad_request_error(error_message)

        @self.router.get("/status")
        @handle_http_errors()
        async def get_player_status(
            request: Request,
            audio_controller=Depends(get_audio_controller),
            state_manager=Depends(get_state_manager),
        ):
            """Get current player status in standardized PlayerState format."""
            if not audio_controller:
                raise service_unavailable_error("Audio controller")
            # Build current player state
            player_state = await player_state_service.build_current_player_state(
                audio_controller, state_manager
            )
            # Return wrapped response as per standardized API format
            return UnifiedResponseService.success(
                message="Player status retrieved successfully",
                data=player_state.model_dump(),
                server_seq=player_state.server_seq,
            )

        @self.router.post("/seek")
        @handle_http_errors()
        async def seek_player(
            request: Request,
            body: SeekRequest,
            audio_controller=Depends(get_audio_controller),
            state_manager=Depends(get_state_manager),
        ):
            """Seek to a specific playback position (in milliseconds)."""
            # Debug logging
            logger.log(
                LogLevel.DEBUG,
                f"Seek request received: position_ms={body.position_ms}, client_op_id={body.client_op_id}",
            )
            # Rate limiting
            client_id = get_client_id(request)
            if not check_rate_limit(client_id):
                raise rate_limit_error("Too many seek requests")
            if not audio_controller:
                raise service_unavailable_error("Audio controller")
            position_ms = body.position_ms
            client_op_id = validate_client_op_id(body.client_op_id)
            # Execute seek
            ok = audio_controller.seek_to(int(position_ms))
            if not ok:
                if client_op_id and state_manager:
                    await state_manager.send_acknowledgment(
                        client_op_id, False, {"message": "Seek failed"}
                    )
                raise bad_request_error("Seek operation failed")
            # Build updated player state
            player_state = await player_state_service.build_current_player_state(
                audio_controller, state_manager
            )
            # Override position with exact seek position
            player_state.position_ms = position_ms
            if state_manager:
                await state_manager.broadcast_state_change(
                    SocketEventType.STATE_PLAYER, player_state.model_dump()
                )
                if client_op_id:
                    await state_manager.send_acknowledgment(
                        client_op_id, True, player_state.model_dump()
                    )
            # Trigger immediate progress update for UI responsiveness
            await self._trigger_immediate_progress(request)
            logger.log(LogLevel.INFO, f"Seek: Successfully sought to {position_ms}ms")
            # Return wrapped response as per standardized API format
            return UnifiedResponseService.success(
                message="Seek completed successfully",
                data=player_state.model_dump(),
                server_seq=player_state.server_seq,
            )

        @self.router.post("/volume")
        @handle_http_errors()
        async def set_volume(
            request: Request,
            body: VolumeRequest,
            audio_controller=Depends(get_audio_controller),
            state_manager=Depends(get_state_manager),
        ):
            """Set player volume and broadcast updated state."""
            # Rate limiting (reuse same policy as other controls)
            client_id = get_client_id(request)
            if not check_rate_limit(client_id):
                raise rate_limit_error("Too many volume requests")
            if not audio_controller:
                raise service_unavailable_error("Audio controller")
            client_op_id = validate_client_op_id(body.client_op_id)
            ok = audio_controller.set_volume(int(body.volume))
            if not ok:
                if client_op_id and state_manager:
                    await state_manager.send_acknowledgment(
                        client_op_id, False, {"message": "Volume set failed"}
                    )
                raise bad_request_error("Volume set operation failed")
            # Build current player state with updated volume
            player_state = await player_state_service.build_current_player_state(
                audio_controller, state_manager
            )
            if state_manager:
                await state_manager.broadcast_state_change(
                    SocketEventType.STATE_PLAYER, player_state.model_dump()
                )
                if client_op_id:
                    await state_manager.send_acknowledgment(
                        client_op_id, True, player_state.model_dump()
                    )
            logger.log(LogLevel.INFO, f"Volume: Successfully set to {body.volume}")
            # Return wrapped response as per standardized API format
            return UnifiedResponseService.success(
                message="Volume set successfully",
                data=player_state.model_dump(),
                server_seq=player_state.server_seq,
            )

    @handle_http_errors()
    async def _handle_navigation_command(
        self,
        request: Request,
        body: PlayerControlRequest,
        audio_controller,
        state_manager,
        command: str,
    ):
        """Handle navigation commands (next/previous) with unified logic."""
        if not audio_controller:
            raise service_unavailable_error("Audio controller")
        client_op_id = validate_client_op_id(body.client_op_id)
        # Execute navigation command
        result = await audio_controller.handle_playback_control(command)
        if result.get("status") == "success":
            # Build unified player state
            player_state = await player_state_service.build_current_player_state(
                audio_controller, state_manager
            )
            # Broadcast state change
            if state_manager:
                await state_manager.broadcast_state_change(
                    SocketEventType.STATE_PLAYER, player_state.model_dump()
                )
                # Send acknowledgment
                if client_op_id:
                    await state_manager.send_acknowledgment(
                        client_op_id, True, player_state.model_dump()
                    )
            logger.log(
                LogLevel.INFO,
                f"{command.capitalize()}: Successfully navigated - track={player_state.active_track_id}",
            )
            # Return wrapped response as per standardized API format
            return UnifiedResponseService.success(
                message=f"Navigation to {command} track successful",
                data=player_state.model_dump(),
                server_seq=player_state.server_seq,
            )
        else:
            error_message = result.get("error", f"{command.capitalize()} operation failed")
            raise bad_request_error(error_message)

    @handle_http_errors()
    async def _trigger_immediate_progress(self, request: Request):
        """Trigger immediate progress update for UI responsiveness."""
        playlist_routes_state = getattr(request.app, "playlist_routes_state", None)
        if playlist_routes_state and hasattr(playlist_routes_state, "progress_service"):
            logger.log(
                LogLevel.DEBUG, "Triggering immediate progress emission for UI responsiveness"
            )
            await playlist_routes_state.progress_service.emit_immediate_position()

    def register_with_app(self, prefix: str = "/api/player"):
        """Register the router with the FastAPI app."""
        self.app.include_router(self.router, prefix=prefix, tags=["player"])
        logger.log(LogLevel.INFO, f"Standardized player routes registered with prefix: {prefix}")
