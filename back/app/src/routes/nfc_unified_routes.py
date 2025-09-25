# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Unified NFC API Routes for TheOpenMusicBox.

This module consolidates all NFC-related endpoints into a single, coherent API
that follows the documented API specification and uses standardized response formats.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from ..common.response_models import create_success_response, ClientOperationRequest
from ..common.data_models import NFCAssociationModel
from app.src.infrastructure.error_handling.unified_error_handler import (
    unified_error_handler,
    service_unavailable_error,
    bad_request_error,
)
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_http_errors

logger = get_logger(__name__)


# Request Models
class NFCAssociateRequest(ClientOperationRequest):
    """Request model for NFC tag association."""

    playlist_id: str = Field(..., description="Playlist ID to associate with tag")
    tag_id: str = Field(..., description="NFC tag identifier")


class NFCScanRequest(ClientOperationRequest):
    """Request model for NFC scan operations."""

    timeout_ms: Optional[int] = Field(
        60000, ge=1000, le=300000, description="Scan timeout in milliseconds"
    )
    playlist_id: Optional[str] = Field(
        None, description="Playlist ID for association mode scanning"
    )


class NFCWriteRequest(ClientOperationRequest):
    """Request model for NFC tag writing."""

    tag_id: str = Field(..., description="NFC tag identifier")
    data: dict = Field(..., description="Data to write to tag")


# Response Models
class NFCStatusResponse(BaseModel):
    """NFC reader status response."""

    reader_available: bool = Field(..., description="Whether NFC reader is available")
    scanning: bool = Field(..., description="Whether currently scanning")
    association_active: bool = Field(False, description="Whether association session is active")
    current_session_id: Optional[str] = Field(None, description="Current association session ID")


class NFCScanResponse(BaseModel):
    """NFC scan operation response."""

    scan_id: str = Field(..., description="Scan session identifier")
    timeout_ms: int = Field(..., description="Scan timeout in milliseconds")


def get_nfc_service(request: Request):
    """Get NFC service from domain application."""
    application = getattr(request.app, "application", None)
    if not application:
        raise service_unavailable_error("Domain application not available")
    nfc_service = getattr(application, "_nfc_app_service", None)
    if not nfc_service:
        raise service_unavailable_error("NFC service not available")
    return nfc_service


def get_state_manager(request: Request):
    """Get state manager from application."""
    return getattr(request.app, "state_manager", None)


class UnifiedNFCRoutes:
    """Unified NFC API routes with standardized response handling."""

    def __init__(self, app, socketio):
        """Initialize UnifiedNFCRoutes with FastAPI app and Socket.IO server."""
        self.app = app
        self.socketio = socketio
        self.router = APIRouter()
        self.error_handler = unified_error_handler

        # Configure Socket.IO for NFC service if available
        self._configure_nfc_socketio()

        self._register_routes()

    def _configure_nfc_socketio(self):
        """Configure Socket.IO for the NFC service."""
        application = getattr(self.app, "application", None)
        if application:
            # Try new NFC application service first
            nfc_service = getattr(application, "_nfc_app_service", None)
            if not nfc_service or not hasattr(nfc_service, "set_socketio"):
                # Fallback to legacy NFC service
                nfc_service = getattr(application, "_nfc_app_service", None)
            if nfc_service and hasattr(nfc_service, "set_socketio"):
                nfc_service.set_socketio(self.socketio)
                logger.log(LogLevel.INFO, "✅ Socket.IO configured for NFC service")
            else:
                logger.log(
                    LogLevel.INFO,
                    "ℹ️ NFC service doesn't support Socket.IO (using direct callbacks)",
                )
        else:
            logger.log(
                LogLevel.WARNING, "⚠️ Domain application not available for Socket.IO configuration"
            )

    def _register_routes(self):
        """Register all NFC-related API routes with standardized handling."""

        @self.router.post("/associate")
        @handle_http_errors()
        async def associate_tag_with_playlist(
            request: Request,
            body: NFCAssociateRequest,
            nfc_service=Depends(get_nfc_service),
            state_manager=Depends(get_state_manager),
        ):
            """Associate NFC tag with playlist."""
            playlist_id = body.playlist_id
            tag_id = body.tag_id
            client_op_id = body.client_op_id
            # Start association session
            result = await nfc_service.start_association_use_case(playlist_id)
            if not result.get("assoc_id"):
                error_msg = "Failed to start association session"
                if state_manager and client_op_id:
                    await state_manager.send_acknowledgment(
                        client_op_id, False, {"message": error_msg}
                    )
                raise bad_request_error(error_msg)
            # Perform the association
            association_result = await nfc_service.associate_tag(tag_id, playlist_id)
            if association_result.get("status") == "success":
                association_data = NFCAssociationModel(
                    tag_id=tag_id,
                    playlist_id=playlist_id,
                    playlist_title=association_result.get("playlist_title", ""),
                    created_at=association_result.get("created_at", ""),
                )
                if state_manager and client_op_id:
                    await state_manager.send_acknowledgment(
                        client_op_id, True, association_data.model_dump(mode="json")
                    )
                logger.log(
                    LogLevel.INFO, f"NFC tag {tag_id} associated with playlist {playlist_id}"
                )
                return JSONResponse(
                    content=create_success_response(
                        message="NFC tag associated successfully",
                        data={"association": association_data.model_dump(mode="json")},
                    ),
                    status_code=200,
                )
            elif association_result.get("status") == "conflict":
                # Tag already associated with another playlist
                conflict_data = association_result.get("conflict_info", {})
                if state_manager and client_op_id:
                    await state_manager.send_acknowledgment(client_op_id, False, conflict_data)
                raise bad_request_error("Tag already associated with another playlist")
            else:
                error_msg = association_result.get("message", "Association failed")
                if state_manager and client_op_id:
                    await state_manager.send_acknowledgment(
                        client_op_id, False, {"message": error_msg}
                    )
                raise bad_request_error(error_msg)

        @self.router.delete("/associate/{tag_id}")
        @handle_http_errors()
        async def remove_tag_association(
            tag_id: str,
            request: Request,
            body: ClientOperationRequest = ClientOperationRequest(),
            nfc_service=Depends(get_nfc_service),
            state_manager=Depends(get_state_manager),
        ):
            """Remove NFC tag association."""
            client_op_id = body.client_op_id
            # Remove the association
            result = await nfc_service.remove_association(tag_id)
            if result.get("status") == "success":
                if state_manager and client_op_id:
                    await state_manager.send_acknowledgment(client_op_id, True, {"tag_id": tag_id})
                logger.log(LogLevel.INFO, f"NFC tag association removed for tag {tag_id}")
                return JSONResponse(
                    content=create_success_response(
                        message="NFC tag association removed successfully"
                    ),
                    status_code=200,
                )
            elif result.get("status") == "not_found":
                if state_manager and client_op_id:
                    await state_manager.send_acknowledgment(client_op_id, False, {"tag_id": tag_id})
                raise bad_request_error("NFC tag association not found")
            else:
                error_msg = result.get("message", "Failed to remove association")
                if state_manager and client_op_id:
                    await state_manager.send_acknowledgment(
                        client_op_id, False, {"message": error_msg}
                    )
                raise bad_request_error(error_msg)

        @self.router.get("/status")
        @handle_http_errors()
        async def get_nfc_status(request: Request, nfc_service=Depends(get_nfc_service)):
            """Get current NFC reader status."""
            status = await nfc_service.get_nfc_status_use_case()
            # Add association session information (simplified for now)
            active_sessions = []
            # Note: Direct access to private attributes removed for architecture safety
            status_response = NFCStatusResponse(
                reader_available=status.get("hardware_available", False),
                scanning=status.get("listening", False),
                association_active=status.get("association_active", False),
                current_session_id=status.get("current_session_id", None),
            )
            # Add session details to response
            response_data = status_response.model_dump()
            response_data["active_sessions"] = active_sessions
            return JSONResponse(
                content=create_success_response(
                    message="NFC status retrieved successfully", data=response_data
                ),
                status_code=200,
            )

        @self.router.post("/scan")
        @handle_http_errors()
        async def start_nfc_scan(
            request: Request,
            body: NFCScanRequest,
            nfc_service=Depends(get_nfc_service),
            state_manager=Depends(get_state_manager),
        ):
            """Start NFC scan session."""
            timeout_ms = body.timeout_ms or 60000
            client_op_id = body.client_op_id
            playlist_id = body.playlist_id
            # If playlist_id is provided, start association session instead of generic scan
            if playlist_id:
                logger.log(
                    LogLevel.INFO, f"Starting NFC association session for playlist {playlist_id}"
                )
                result = await nfc_service.start_association_use_case(
                    playlist_id, timeout_seconds=timeout_ms // 1000
                )
                if result.get("status") == "success" and "session" in result:
                    session_id = result["session"]["session_id"]  # Get session ID from session dict
                    scan_response = NFCScanResponse(
                        scan_id=session_id, timeout_ms=timeout_ms  # Use session ID as scan ID
                    )
                    if state_manager and client_op_id:
                        await state_manager.send_acknowledgment(
                            client_op_id, True, scan_response.model_dump()
                        )
                    logger.log(
                        LogLevel.INFO,
                        f"NFC association session started with ID {session_id} for playlist {playlist_id}",
                    )
                    return JSONResponse(
                        content=create_success_response(
                            message="NFC association session started",
                            data=scan_response.model_dump(),
                        ),
                        status_code=200,
                    )
                else:
                    error_msg = result.get("message", "Failed to start association session")
                    if state_manager and client_op_id:
                        await state_manager.send_acknowledgment(
                            client_op_id, False, {"message": error_msg}
                        )
                    raise bad_request_error(error_msg)
            else:
                # Generic scan session (no association)
                result = await nfc_service.start_scan_session(timeout_ms)
                if result.get("status") == "success":
                    scan_response = NFCScanResponse(
                        scan_id=result["scan_id"], timeout_ms=timeout_ms
                    )
                    if state_manager and client_op_id:
                        await state_manager.send_acknowledgment(
                            client_op_id, True, scan_response.model_dump()
                        )
                    logger.log(
                        LogLevel.INFO, f"NFC scan session started with ID {result['scan_id']}"
                    )
                    return JSONResponse(
                        content=create_success_response(
                            message="NFC scan session started", data=scan_response.model_dump()
                        ),
                        status_code=200,
                    )
                else:
                    error_msg = result.get("message", "Failed to start scan session")
                    if state_manager and client_op_id:
                        await state_manager.send_acknowledgment(
                            client_op_id, False, {"message": error_msg}
                        )
                    raise bad_request_error(error_msg)

    def register_with_app(self, prefix: str = "/api/nfc"):
        """Register the router with the FastAPI app."""
        self.app.include_router(self.router, prefix=prefix, tags=["nfc"])
        logger.log(LogLevel.INFO, f"Unified NFC routes registered with prefix: {prefix}")
