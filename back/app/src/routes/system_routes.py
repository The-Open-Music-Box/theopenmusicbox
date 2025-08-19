# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

# back/app/src/routes/system_routes.py
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request

from app.src.dependencies import get_audio, get_audio_controller
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class SystemRoutes:
    """Registers and manages system-level API routes for TheOpenMusicBox backend.

    This class sets up FastAPI endpoints for system functions such as health checks and volume control.
    It ensures all routes are registered with the FastAPI app and provides dependency injection for audio services.
    """
    def __init__(self, app: FastAPI):
        self.app = app
        # Using /api as prefix, so endpoints will be /api/volume
        self.router = APIRouter(prefix="/api", tags=["system"])
        self._register_routes()

    def register(self):
        """Register the system API routes with the FastAPI application."""
        # Enregistrer les routes système importantes directement sur l'app FastAPI
        # pour éviter les problèmes potentiels avec le routeur

        # Route GET /api/volume
        @self.app.get("/api/volume")
        async def get_volume_direct(audio=Depends(get_audio)):
            from fastapi.responses import JSONResponse

            logger.log(LogLevel.INFO, "DIRECT API /api/volume: Route called")

            try:
                if not audio:
                    error_data = {"error": "Audio system not available"}
                    return JSONResponse(content=error_data, status_code=503)

                current_volume = getattr(audio, "_volume", "unknown")
                logger.log(
                    LogLevel.INFO,
                    f"API: Responding with current volume: {current_volume}",
                )

                data = {"volume": current_volume}
                response = JSONResponse(content=data, status_code=200)

                # Ajouter des en-têtes anti-cache
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                return response
            except Exception as e:
                logger.log(LogLevel.ERROR, f"DIRECT API /api/volume: Error: {str(e)}")
                error_data = {"error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        # Route GET /api/playback/status
        @self.app.get("/api/playback/status")
        async def get_playback_status_direct(audio_controller=Depends(get_audio_controller)):
            from fastapi.responses import JSONResponse

            logger.log(LogLevel.INFO, "DIRECT API /api/playback/status: Route called")

            try:
                if not audio_controller:
                    error_data = {"error": "Audio controller not available"}
                    return JSONResponse(content=error_data, status_code=503)

                playback_state = audio_controller.get_playback_state()
                logger.log(
                    LogLevel.INFO,
                    f"API: Responding with playback state: {playback_state}",
                )

                response = JSONResponse(content=playback_state, status_code=200)

                # Add anti-cache headers
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                return response
            except Exception as e:
                logger.log(LogLevel.ERROR, f"DIRECT API /api/playback/status: Error: {str(e)}")
                error_data = {"error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        # Route GET /api/health
        @self.app.get("/api/health")
        async def health_check_direct(request: Request):
            from fastapi.responses import JSONResponse

            logger.log(LogLevel.INFO, "DIRECT API /api/health: Route called")

            try:
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
                    response.headers["Cache-Control"] = (
                        "no-cache, no-store, must-revalidate"
                    )
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
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                return response
            except Exception as e:
                logger.log(LogLevel.ERROR, f"DIRECT API /api/health: Error: {str(e)}")
                error_data = {"error": str(e), "status": "error"}
                return JSONResponse(content=error_data, status_code=500)

        # Route GET /api/system/info
        @self.app.get("/api/system/info")
        async def get_system_info_direct(request: Request):
            from fastapi.responses import JSONResponse
            import platform
            import psutil
            import os

            logger.log(LogLevel.INFO, "DIRECT API /api/system/info: Route called")

            try:
                # Get container from app state
                container = getattr(request.app, "container", None)
                
                # System information
                system_info = {
                    "system": {
                        "platform": platform.system(),
                        "platform_release": platform.release(),
                        "platform_version": platform.version(),
                        "architecture": platform.machine(),
                        "hostname": platform.node(),
                        "python_version": platform.python_version()
                    },
                    "hardware": {
                        "cpu_count": psutil.cpu_count(),
                        "memory_total": psutil.virtual_memory().total,
                        "memory_available": psutil.virtual_memory().available,
                        "disk_usage": {
                            "total": psutil.disk_usage('/').total,
                            "used": psutil.disk_usage('/').used,
                            "free": psutil.disk_usage('/').free
                        }
                    },
                    "application": {
                        "name": "TheOpenMusicBox",
                        "version": "1.0.0",
                        "container_available": container is not None,
                        "pid": os.getpid()
                    }
                }

                response = JSONResponse(content=system_info, status_code=200)
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                return response
            except Exception as e:
                logger.log(LogLevel.ERROR, f"DIRECT API /api/system/info: Error: {str(e)}")
                error_data = {"error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        # Route GET /api/system/logs
        @self.app.get("/api/system/logs")
        async def get_system_logs_direct():
            from fastapi.responses import JSONResponse
            import os
            import glob

            logger.log(LogLevel.INFO, "DIRECT API /api/system/logs: Route called")

            try:
                logs_data = {
                    "logs": [],
                    "log_files_available": []
                }

                # Try to find log files in common locations
                possible_log_paths = [
                    "/var/log/tomb-rpi/*.log",
                    "/tmp/tomb-rpi*.log",
                    "logs/*.log",
                    "*.log"
                ]

                for pattern in possible_log_paths:
                    log_files = glob.glob(pattern)
                    for log_file in log_files:
                        logs_data["log_files_available"].append(log_file)
                        try:
                            # Read last 100 lines of each log file
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                last_lines = lines[-100:] if len(lines) > 100 else lines
                                logs_data["logs"].extend([
                                    {"file": log_file, "line": line.strip()} 
                                    for line in last_lines if line.strip()
                                ])
                        except (IOError, OSError):
                            continue

                # If no log files found, provide current session info
                if not logs_data["logs"]:
                    logs_data["logs"] = [
                        {"file": "current_session", "line": "No log files found in standard locations"}
                    ]

                response = JSONResponse(content=logs_data, status_code=200)
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                return response
            except Exception as e:
                logger.log(LogLevel.ERROR, f"DIRECT API /api/system/logs: Error: {str(e)}")
                error_data = {"error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        # Route POST /api/system/restart
        @self.app.post("/api/system/restart")
        async def restart_system_direct():
            from fastapi.responses import JSONResponse
            import asyncio
            import os
            import signal

            logger.log(LogLevel.INFO, "DIRECT API /api/system/restart: Route called")

            try:
                # Schedule restart after response is sent
                async def delayed_restart():
                    await asyncio.sleep(2)  # Give time for response to be sent
                    logger.log(LogLevel.INFO, "Restarting application...")
                    os.kill(os.getpid(), signal.SIGTERM)

                # Start the delayed restart task
                asyncio.create_task(delayed_restart())

                response_data = {
                    "status": "restart_scheduled",
                    "message": "Application restart scheduled in 2 seconds"
                }

                response = JSONResponse(content=response_data, status_code=200)
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                return response
            except Exception as e:
                logger.log(LogLevel.ERROR, f"DIRECT API /api/system/restart: Error: {str(e)}")
                error_data = {"error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        # Inclure le routeur pour les autres routes (comme POST /api/volume)
        self.app.include_router(self.router)

    def _register_routes(self):
        """Register all system-related API routes with the FastAPI router."""
        @self.router.post("/volume", response_model=Dict[str, Any])
        async def set_system_volume(
            volume: int = Body(..., embed=True, ge=0, le=100), audio=Depends(get_audio)
        ):
            """Set the system audio volume (0-100)."""
            if not audio:
                raise HTTPException(
                    status_code=503, detail="Audio system not available"
                )

            logger.log(
                LogLevel.INFO, f"API: Received request to set volume to {volume}"
            )
            success = audio.set_volume(volume)  # audio.set_volume expects 0-100
            if not success:
                logger.log(
                    LogLevel.ERROR,
                    f"API: Failed to set volume to {volume} via audio module",
                )
                raise HTTPException(status_code=500, detail="Failed to set volume")

            current_volume = getattr(
                audio, "_volume", "unknown"
            )  # Get the updated volume
            logger.log(
                LogLevel.INFO, f"API: Volume successfully set to {current_volume}"
            )
            return {"status": "success", "volume": current_volume}

        @self.router.get("/volume", response_model=Dict[str, Any])
        async def get_system_volume(audio=Depends(get_audio)):
            """Get the current system audio volume."""
            if not audio:
                raise HTTPException(
                    status_code=503, detail="Audio system not available"
                )

            # audio._volume should be 0-100
            current_volume = getattr(audio, "_volume", "unknown")
            logger.log(
                LogLevel.INFO, f"API: Responding with current volume: {current_volume}"
            )
            return {"volume": current_volume}

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
