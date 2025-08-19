# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.youtube import YouTubeService

logger = ImprovedLogger(__name__)

# Define request model


class YouTubeDownloadRequest(BaseModel):
    """Request model for YouTube video download requests."""
    url: str


class YouTubeRoutes:
    """Register and manage YouTube-related API routes for TheOpenMusicBox backend."""
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

                # Add anti-cache headers
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

        @self.app.get("/api/youtube/search", tags=["youtube"])
        async def search_youtube(request: Request, query: str, max_results: int = 10):
            """Search for YouTube videos."""
            logger.log(LogLevel.INFO, f"YouTubeRoutes: Received YouTube search request for: {query}")

            if not query:
                logger.log(LogLevel.WARNING, "YouTubeRoutes: Empty search query provided")
                error_data = {"error": "Search query is required", "status": "error"}
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
                # Perform YouTube search
                search_results = await service.search_videos(query, max_results)

                response_data = {
                    "status": "success",
                    "query": query,
                    "results": search_results,
                    "count": len(search_results)
                }

                response = JSONResponse(content=response_data, status_code=200)

                # Add anti-cache headers
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
                    f"YouTubeRoutes: Search failed: {error_msg}",
                    exc_info=True,
                )

                error_data = {"error": error_msg, "status": "error"}
                return JSONResponse(content=error_data, status_code=500)

        @self.app.get("/api/youtube/status/{task_id}", tags=["youtube"])
        async def get_youtube_status(request: Request, task_id: str):
            """Get the status of a YouTube download task."""
            logger.log(LogLevel.INFO, f"YouTubeRoutes: Checking status for task: {task_id}")

            if not task_id:
                logger.log(LogLevel.WARNING, "YouTubeRoutes: Empty task_id provided")
                error_data = {"error": "Task ID is required", "status": "error"}
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
                # Get task status
                task_status = await service.get_task_status(task_id)

                if task_status:
                    response_data = {
                        "status": "found",
                        "task_id": task_id,
                        "task_status": task_status
                    }
                    status_code = 200
                else:
                    response_data = {
                        "status": "not_found",
                        "task_id": task_id,
                        "message": "Task not found or expired"
                    }
                    status_code = 404

                response = JSONResponse(content=response_data, status_code=status_code)

                # Add anti-cache headers
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
                    f"YouTubeRoutes: Status check failed: {error_msg}",
                    exc_info=True,
                )

                error_data = {"error": error_msg, "status": "error"}
                return JSONResponse(content=error_data, status_code=500)
