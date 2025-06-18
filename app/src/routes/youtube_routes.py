from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.youtube import YouTubeService

logger = ImprovedLogger(__name__)

# Define request model


class YouTubeDownloadRequest(BaseModel):
    url: str


class YouTubeRoutes:
    def __init__(self, app: FastAPI, socketio):
        self.app = app
        self.socketio = socketio
        self.router = None

    def register(self):
        """Register YouTube routes with FastAPI app."""
        try:
            logger.log(LogLevel.INFO, "YouTubeRoutes: Registering YouTube routes")
            self._init_routes()
            logger.log(
                LogLevel.INFO, "YouTubeRoutes: YouTube routes registered successfully"
            )
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"YouTubeRoutes: Failed to register routes: {e}",
                exc_info=True,
            )
            raise

    def _init_routes(self):
        """Initialize YouTube routes."""

        @self.app.post("/api/youtube/download", tags=["youtube"])
        async def download_youtube(
            request: Request, download_req: YouTubeDownloadRequest
        ):
            """Download a YouTube video."""
            logger.log(
                LogLevel.INFO, "YouTubeRoutes: Received YouTube download request"
            )

            url = download_req.url
            if not url:
                logger.log(
                    LogLevel.WARNING, "YouTubeRoutes: Invalid YouTube URL provided"
                )
                error_data = {"error": "Invalid YouTube URL", "status": "error"}
                return JSONResponse(content=error_data, status_code=400)

            try:
                # Get container from app state
                container = getattr(request.app, "container", None)
                if not container:
                    logger.log(LogLevel.ERROR, "YouTubeRoutes: Container not available")
                    error_data = {
                        "error": "Application container not available",
                        "status": "error",
                    }
                    return JSONResponse(content=error_data, status_code=500)

                service = YouTubeService(self.socketio, container.config)
                # Call the asynchronous method which handles the download in a
                # non-blocking way
                result = await service.process_download(url)

                # Utiliser JSONResponse explicitement pour garantir un Content-Type
                # correct
                response = JSONResponse(content=result, status_code=200)

                # Ajouter des en-têtes anti-cache
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                return response

            except Exception as e:
                error_msg = str(e)
                logger.log(
                    LogLevel.ERROR,
                    f"YouTubeRoutes: Download failed: {error_msg}",
                    exc_info=True,
                )

                # Utiliser JSONResponse pour l'erreur au lieu de HTTPException
                error_data = {"error": error_msg, "status": "error"}
                return JSONResponse(content=error_data, status_code=500)
