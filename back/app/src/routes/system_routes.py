# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""System-level API routes for TheOpenMusicBox backend.

Provides REST API endpoints for system health checks, status monitoring,
system information, log access, and restart functionality. Handles both
direct FastAPI registration and router-based route registration.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, FastAPI, Request

from app.src.routes.player_routes import get_audio_controller
from app.src.monitoring import get_logger
from app.src.services.error.unified_error_decorator import handle_errors
from app.src.monitoring.logging.log_level import LogLevel
from app.src.utils.response_utils import ResponseUtils

logger = get_logger(__name__)


class SystemRoutes:
    """Registers and manages system-level API routes for TheOpenMusicBox backend.

    This class sets up FastAPI endpoints for system functions such as health checks and system info.
    It ensures all routes are registered with the FastAPI app and provides dependency injection for audio services.
    """

    def __init__(self, app: FastAPI):
        self.app = app
        # Using /api as prefix for system endpoints
        self.router = APIRouter(prefix="/api", tags=["system"])
        self._register_routes()

    def register(self):
        """Register the system API routes with the FastAPI application."""
        # Enregistrer les routes système importantes directement sur l'app FastAPI
        # pour éviter les problèmes potentiels avec le routeur

        # Volume endpoints have been moved to PlayerRoutes at /api/player/volume
        # for better separation of concerns

        # Route GET /api/playback/status
        @self.app.get("/api/playback/status")
        @handle_errors("system_routes")
        async def get_playback_status_direct(audio_controller=Depends(get_audio_controller)):
            from fastapi.responses import JSONResponse

            logger.log(LogLevel.INFO, "DIRECT API /api/playback/status: Route called")

            if not audio_controller:
                return ResponseUtils.create_error_response("Audio controller not available", 503)
            playback_state = await audio_controller.get_playback_status()
            logger.log(
                LogLevel.INFO,
                f"API: Responding with playback state: {playback_state}",
            )
            response = JSONResponse(content=playback_state, status_code=200)
            # Add anti-cache headers
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        # Route GET /api/health
        @self.app.get("/api/health")
        @handle_errors("system_routes")
        async def health_check_direct(request: Request):
            from fastapi.responses import JSONResponse

            logger.log(LogLevel.INFO, "DIRECT API /api/health: Route called")

            # Get container from app state
            container = getattr(request.app, "container", None)
            if not container:
                data = {
                    "status": "warning",
                    "message": "Container not available",
                    "subsystems": {
                        "api": True,
                        "audio": False,
                        "nfc": False,
                        "gpio": False,
                        "led_hat": False,
                        "websocket": False,
                    },
                }
                response = JSONResponse(content=data, status_code=200)
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                return response
            # Get audio status
            audio = getattr(container, "audio", None)
            # Get NFC status
            nfc = getattr(container, "nfc", None)
            nfc_status = {
                "available": nfc is not None,
                "code": "NFC_OK" if nfc is not None else "NFC_NOT_AVAILABLE",
            }
            # Consolidated health information
            data = {
                "status": "ok",
                "nfc": nfc_status,
                "subsystems": {
                    "api": True,
                    "audio": bool(audio),
                    "nfc": bool(nfc),
                    "gpio": bool(getattr(container, "gpio", None)),
                    "led_hat": bool(getattr(container, "led_hat", None)),
                    "websocket": hasattr(request.app, "socketio"),
                },
                "volume": getattr(audio, "_volume", None) if audio else None,
            }
            response = JSONResponse(content=data, status_code=200)
            # Ajouter des en-têtes anti-cache
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        # Route GET /api/system/info
        @self.app.get("/api/system/info")
        @handle_errors("system_routes")
        async def get_system_info_direct(request: Request):
            from fastapi.responses import JSONResponse
            import platform
            import os
            import shutil

            logger.log(LogLevel.INFO, "DIRECT API /api/system/info: Route called")

            # psutil is optional; provide graceful fallback if unavailable
            try:
                import psutil as _psutil  # type: ignore
            except ImportError:
                _psutil = None

            # Build system info response
            system_info = {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "processor": platform.processor(),
            }

            # Add memory info if psutil available
            if _psutil:
                try:
                    memory = _psutil.virtual_memory()
                    system_info.update(
                        {
                            "memory_total": memory.total,
                            "memory_available": memory.available,
                            "memory_percent": memory.percent,
                        }
                    )
                except Exception:
                    pass

            return JSONResponse(content={"status": "success", "system_info": system_info})

        # Route GET /api/system/logs
        @self.app.get("/api/system/logs")
        @handle_errors("system_routes")
        async def get_system_logs_direct():
            from fastapi.responses import JSONResponse
            import os
            import glob

            logger.log(LogLevel.INFO, "DIRECT API /api/system/logs: Route called")

            logs_data = {"logs": [], "log_files_available": []}
            # Try to find log files in common locations
            possible_log_paths = [
                "/var/log/tomb-rpi/*.log",
                "/tmp/tomb-rpi*.log",
                "logs/*.log",
                "*.log",
            ]
            for pattern in possible_log_paths:
                log_files = glob.glob(pattern)
                for log_file in log_files:
                    logs_data["log_files_available"].append(log_file)
                    # Read last 100 lines of each log file
                    try:
                        with open(log_file, "r") as f:
                            lines = f.readlines()
                            last_lines = lines[-100:] if len(lines) > 100 else lines
                            logs_data["logs"].extend(
                                [
                                    {"file": log_file, "line": line.strip()}
                                    for line in last_lines
                                    if line.strip()
                                ]
                            )
                    except (IOError, OSError):
                        pass  # Skip files that can't be read

            return JSONResponse(content={"status": "success", "data": logs_data})

        # Route POST /api/system/restart
        @self.app.post("/api/system/restart")
        @handle_errors("system_routes")
        async def restart_system_direct():
            from fastapi.responses import JSONResponse
            import asyncio
            import os
            import signal

            logger.log(LogLevel.INFO, "DIRECT API /api/system/restart: Route called")

            # Schedule restart after response is sent
            async def delayed_restart():
                await asyncio.sleep(2)  # Give time for response to be sent
                logger.log(LogLevel.INFO, "Restarting application...")
                os.kill(os.getpid(), signal.SIGTERM)

            # Start the delayed restart task
            asyncio.create_task(delayed_restart())
            response_data = {
                "status": "restart_scheduled",
                "message": "Application restart scheduled in 2 seconds",
            }
            # Use standardized response format
            from app.src.common.response_models import create_success_response

            standardized_response = create_success_response(
                message="System restart scheduled successfully", data=response_data
            )
            response = JSONResponse(content=standardized_response, status_code=200)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        # Include the router for other system routes
        self.app.include_router(self.router)

    def _register_routes(self):
        """Register all system-related API routes with the FastAPI router."""
        # Volume endpoints removed - handled by PlayerRoutes at /api/player/volume

        @self.router.get("/health", response_model=Dict[str, Any])
        async def api_health_check(request: Request):
            """
            Perform a consolidated health check for the entire application.

            Returns:
                dict: Health status and subsystem availability.
            """
            logger.log(LogLevel.INFO, "API: Health check requested")

            # Get container from app state
            container = getattr(request.app, "container", None)
            if not container:
                return {
                    "status": "warning",
                    "message": "Container not available",
                    "subsystems": {
                        "api": True,
                        "audio": False,
                        "nfc": False,
                        "gpio": False,
                        "led_hat": False,
                        "websocket": False,
                    },
                }

            # Get audio status
            audio = getattr(container, "audio", None)

            # Get NFC status
            nfc = getattr(container, "nfc", None)
            nfc_status = {
                "available": nfc is not None,
                "code": "NFC_OK" if nfc is not None else "NFC_NOT_AVAILABLE",
            }

            # Consolidated health information from all previous endpoints
            return {
                "status": "ok",
                "nfc": nfc_status,
                "subsystems": {
                    "api": True,
                    "audio": bool(audio),
                    "nfc": bool(nfc),
                    "gpio": bool(getattr(container, "gpio", None)),
                    "led_hat": bool(getattr(container, "led_hat", None)),
                    "websocket": hasattr(request.app, "socketio"),
                },
                "volume": getattr(audio, "_volume", None) if audio else None,
            }
