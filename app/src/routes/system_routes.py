# back/app/src/routes/system_routes.py
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request

from app.src.dependencies import get_audio  # Assuming get_audio dependency injector
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class SystemRoutes:
    def __init__(self, app: FastAPI):
        self.app = app
        # Using /api as prefix, so endpoints will be /api/volume
        self.router = APIRouter(prefix="/api", tags=["system"])
        self._register_routes()

    def register(self):
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

        # Inclure le routeur pour les autres routes (comme POST /api/volume)
        self.app.include_router(self.router)

    def _register_routes(self):
        @self.router.post("/volume", response_model=Dict[str, Any])
        async def set_system_volume(
            volume: int = Body(..., embed=True, ge=0, le=100), audio=Depends(get_audio)
        ):
            """Set the system audio volume (0-100)"""
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
            """Consolidated health check endpoint for the entire
            application."""
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
