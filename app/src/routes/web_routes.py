from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, Optional

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class WebRoutes:
    def __init__(self, app: FastAPI):
        self.app = app
        self.router = None
        # We'll set up static file serving in register()

    def register(self):
        """Register web routes with FastAPI app"""
        try:
            logger.log(LogLevel.INFO, "WebRoutes: Registering web routes")
            self._init_routes()
            logger.log(LogLevel.INFO, "WebRoutes: Web routes registered successfully")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"WebRoutes: Failed to register routes: {e}", exc_info=True)
            raise

    def _init_routes(self):
        """Initialize web routes for serving static files and health check"""
        # Mount static files directory if it exists
        try:
            # Assuming static files are in app/static
            static_dir = Path("app/static")
            if static_dir.exists() and static_dir.is_dir():
                self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
                logger.log(LogLevel.INFO, f"WebRoutes: Mounted static files from {static_dir}")
            else:
                logger.log(LogLevel.WARNING, f"WebRoutes: Static directory {static_dir} not found")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"WebRoutes: Error mounting static files: {e}")
