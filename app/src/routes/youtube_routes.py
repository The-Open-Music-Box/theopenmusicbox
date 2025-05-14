from fastapi import FastAPI, HTTPException, Request, Body, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
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
        """Register YouTube routes with FastAPI app"""
        try:
            logger.log(LogLevel.INFO, "YouTubeRoutes: Registering YouTube routes")
            self._init_routes()
            logger.log(LogLevel.INFO, "YouTubeRoutes: YouTube routes registered successfully")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"YouTubeRoutes: Failed to register routes: {e}", exc_info=True)
            raise

    def _init_routes(self):
        """Initialize YouTube routes"""

        @self.app.post("/api/youtube/download", tags=["youtube"])
        async def download_youtube(request: Request, download_req: YouTubeDownloadRequest):
            """Download a YouTube video"""
            logger.log(LogLevel.INFO, "YouTubeRoutes: Received YouTube download request")

            url = download_req.url
            if not url:
                logger.log(LogLevel.WARNING, "YouTubeRoutes: Invalid YouTube URL provided")
                raise HTTPException(status_code=400, detail="Invalid YouTube URL")

            try:
                # Get container from app state
                container = getattr(request.app, "container", None)
                if not container:
                    logger.log(LogLevel.ERROR, "YouTubeRoutes: Container not available")
                    raise HTTPException(status_code=500, detail="Application container not available")

                service = YouTubeService(self.socketio, container.config)
                # Call the asynchronous method which handles the download in a non-blocking way
                result = await service.process_download(url)
                return result

            except Exception as e:
                error_msg = str(e)
                logger.log(LogLevel.ERROR, f"YouTubeRoutes: Download failed: {error_msg}", exc_info=True)
                raise HTTPException(status_code=500, detail=error_msg)
