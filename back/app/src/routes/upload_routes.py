# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Upload Management Routes for TheOpenMusicBox.

This module provides endpoints for managing upload sessions,
including listing sessions, cleanup, and monitoring.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from ..common.response_models import create_success_response, create_error_response, ErrorType
from ..infrastructure.error_handling.unified_error_handler import UnifiedErrorHandler as ErrorHandler
from app.src.monitoring import get_logger
from app.src.services.error.unified_error_decorator import handle_errors
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)


class UploadRoutes:
    """Upload management routes for session monitoring and cleanup."""

    def __init__(self, app, socketio):
        """Initialize upload management routes."""
        self.app = app
        self.socketio = socketio
        self.router = APIRouter()
        self.error_handler = ErrorHandler()
        self._register_routes()

    def _register_routes(self):
        """Register all upload management routes."""

        @self.router.get("/sessions")
        @handle_errors()
        async def list_upload_sessions(
            request: Request,
            status: Optional[str] = Query(None, description="Filter by upload status"),
            limit: int = Query(50, ge=1, le=100, description="Maximum sessions to return"),
        ):
            """List all upload sessions with optional filtering."""
            # Get upload controller from app state
            playlist_routes_state = getattr(request.app, "playlist_routes_state", None)
            if not playlist_routes_state or not hasattr(playlist_routes_state, "upload_controller"):
                return JSONResponse(
                    content=create_error_response(
                        message="Upload service not available",
                        error_type=ErrorType.SERVICE_UNAVAILABLE,
                    ),
                    status_code=503,
                )
            upload_controller = playlist_routes_state.upload_controller
            # Get all active sessions from the chunked upload service
            # Access the internal session storage
            sessions_data = []
            if hasattr(upload_controller, "chunked") and hasattr(
                upload_controller.chunked, "_sessions"
            ):
                for session_id, session_info in upload_controller.chunked._sessions.items():
                    session_data = {
                        "session_id": session_id,
                        "filename": session_info.get("filename", "unknown"),
                        "file_size": session_info.get("file_size", 0),
                        "chunks_uploaded": session_info.get("chunks_received", 0),
                        "chunks_total": session_info.get("total_chunks", 0),
                        "progress_percent": round(
                            (
                                session_info.get("chunks_received", 0)
                                / max(1, session_info.get("total_chunks", 1))
                            )
                            * 100,
                            2,
                        ),
                        "playlist_id": session_info.get("playlist_id"),
                        "created_at": session_info.get("created_at"),
                        "status": self._determine_session_status(session_info),
                    }
                    # Apply status filter if provided
                    if status is None or session_data["status"] == status:
                        sessions_data.append(session_data)
                        # Apply limit
                        if len(sessions_data) >= limit:
                            break

            logger.log(LogLevel.INFO, f"Listed {len(sessions_data)} upload sessions")
            return JSONResponse(
                content=create_success_response(
                    message=f"Found {len(sessions_data)} upload sessions",
                    data={"sessions": sessions_data},
                ),
                status_code=200,
            )

        @self.router.delete("/sessions/{session_id}")
        @handle_errors()
        async def delete_upload_session(session_id: str, request: Request):
            """Delete a specific upload session."""
            # Get upload controller from app state
            playlist_routes_state = getattr(request.app, "playlist_routes_state", None)
            if not playlist_routes_state or not hasattr(playlist_routes_state, "upload_controller"):
                return JSONResponse(
                    content=create_error_response(
                        message="Upload service not available",
                        error_type=ErrorType.SERVICE_UNAVAILABLE,
                    ),
                    status_code=503,
                )
            upload_controller = playlist_routes_state.upload_controller
            # Try to remove the session
            if hasattr(upload_controller, "chunked"):
                # Check if session exists
                if hasattr(upload_controller.chunked, "_sessions"):
                    if session_id not in upload_controller.chunked._sessions:
                        return JSONResponse(
                            content=create_error_response(
                                message=f"Upload session not found: {session_id}",
                                error_type=ErrorType.NOT_FOUND,
                            ),
                            status_code=404,
                        )
                    # Remove session
                    del upload_controller.chunked._sessions[session_id]
                    logger.log(LogLevel.INFO, f"Deleted upload session: {session_id}")
                # Also cleanup any temporary files
                if hasattr(upload_controller.chunked, "_cleanup_session_files"):
                    await upload_controller.chunked._cleanup_session_files(session_id)
                return JSONResponse(
                    content=create_success_response(
                        message=f"Upload session deleted: {session_id}"
                    ),
                    status_code=200,
                )

        @self.router.post("/cleanup")
        @handle_errors()
        async def cleanup_stale_sessions(
            request: Request,
            max_age_hours: int = Query(
                24, ge=1, le=168, description="Maximum age in hours for cleanup"
            ),
        ):
            """Cleanup stale upload sessions older than specified age."""
            # Get upload controller from app state
            playlist_routes_state = getattr(request.app, "playlist_routes_state", None)
            if not playlist_routes_state or not hasattr(playlist_routes_state, "upload_controller"):
                return JSONResponse(
                    content=create_error_response(
                        message="Upload service not available",
                        error_type=ErrorType.SERVICE_UNAVAILABLE,
                    ),
                    status_code=503,
                )
            upload_controller = playlist_routes_state.upload_controller
            import time
            from datetime import datetime, timedelta

            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_sessions = []

            if hasattr(upload_controller, "chunked") and hasattr(
                upload_controller.chunked, "_sessions"
            ):
                sessions_to_remove = []
                for session_id, session_info in upload_controller.chunked._sessions.items():
                    created_at = session_info.get("created_at")
                    if created_at:
                        # Try to parse the creation time
                        try:
                            if isinstance(created_at, str):
                                session_time = datetime.fromisoformat(
                                    created_at.replace("Z", "+00:00")
                                )
                            else:
                                session_time = created_at

                            if session_time < cutoff_time:
                                sessions_to_remove.append(session_id)
                                cleaned_sessions.append(
                                    {
                                        "session_id": session_id,
                                        "filename": session_info.get("filename", "unknown"),
                                        "age_hours": (datetime.now() - session_time).total_seconds()
                                        / 3600,
                                    }
                                )
                        except Exception as e:
                            logger.log(
                                LogLevel.WARNING,
                                f"Could not parse creation time for session {session_id}: {e}",
                            )

                # Remove identified stale sessions
                for session_id in sessions_to_remove:
                    del upload_controller.chunked._sessions[session_id]
                    # Also cleanup any temporary files
                    if hasattr(upload_controller.chunked, "_cleanup_session_files"):
                        await upload_controller.chunked._cleanup_session_files(session_id)

            logger.log(LogLevel.INFO, f"Cleaned up {len(cleaned_sessions)} stale upload sessions")
            return JSONResponse(
                content=create_success_response(
                    message=f"Cleaned up {len(cleaned_sessions)} stale sessions",
                    data={"cleaned_sessions": cleaned_sessions},
                ),
                status_code=200,
            )

    def _determine_session_status(self, session_info: Dict[str, Any]) -> str:
        """Determine the status of an upload session."""
        chunks_received = session_info.get("chunks_received", 0)
        total_chunks = session_info.get("total_chunks", 0)

        if chunks_received == 0:
            return "pending"
        elif chunks_received < total_chunks:
            return "uploading"
        elif chunks_received == total_chunks:
            return "completed"
        else:
            return "error"

    def register_with_app(self, prefix: str = "/api/uploads"):
        """Register the router with the FastAPI app."""
        self.app.include_router(self.router, prefix=prefix, tags=["uploads"])
        logger.log(LogLevel.INFO, f"Upload management routes registered with prefix: {prefix}")
