# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class WebRoutes:
    """Registers and manages web (static file) routes for TheOpenMusicBox backend.

    This class sets up FastAPI endpoints for serving static files, SPA index, and health check
    endpoints. It ensures proper SPA routing and static asset delivery for the web client.
    """
    def __init__(self, app: FastAPI):
        self.app = app
        self.router = None
        # We'll set up static file serving in register()

    def register(self):
        """Register web routes with the FastAPI application."""
        """Register web routes with FastAPI app."""
        try:
            logger.log(LogLevel.INFO, "WebRoutes: Registering web routes")
            self._init_routes()
            logger.log(LogLevel.INFO, "WebRoutes: Web routes registered successfully")
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"WebRoutes: Failed to register routes: {e}",
                exc_info=True,
            )
            raise

    def _init_routes(self):
        """Initialize web routes for serving static files and SPA routing."""
        """Initialize web routes for serving static files and health check."""
        # Mount static files directory if it exists
        try:
            # Assuming static files are in app/static
            static_dir = Path("app/static")
            if static_dir.exists() and static_dir.is_dir():
                # Mount static files first
                self.app.mount(
                    "/static", StaticFiles(directory=str(static_dir)), name="static"
                )
                logger.log(
                    LogLevel.INFO, f"WebRoutes: Mounted static files from {static_dir}"
                )

                # Add root path handler to serve index.html
                @self.app.get("/")
                async def serve_spa_index():
                    return FileResponse(f"{static_dir}/index.html")

                # Add catch-all route to handle SPA client-side routing
                # This must have a lower priority than API routes
                @self.app.get("/{full_path:path}", include_in_schema=False)
                async def serve_spa(full_path: str):
                    # IMPORTANT: Ne PAS traiter les chemins API du tout
                    # Cela permet aux routes API d'être gérées par leurs propres
                    # routeurs
                    if full_path.startswith("api/"):
                        # Retourner None pour permettre à FastAPI de continuer à chercher une route correspondante
                        # C'est crucial pour que les routes API fonctionnent
                        # correctement
                        return None

                    # Check if the requested file exists
                    requested_file = static_dir / full_path
                    if requested_file.exists() and requested_file.is_file():
                        return FileResponse(str(requested_file))

                    # Otherwise return index.html for SPA routing
                    return FileResponse(f"{static_dir}/index.html")

                logger.log(LogLevel.INFO, "WebRoutes: SPA routing configured")
            else:
                logger.log(
                    LogLevel.WARNING,
                    f"WebRoutes: Static directory {static_dir} not found",
                )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"WebRoutes: Error mounting static files: {e}")
