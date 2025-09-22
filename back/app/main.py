# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
FastAPI Application Entry Point for TheOpenMusicBox

This module provides the main FastAPI application with Socket.IO integration
for the TheOpenMusicBox music management system. It handles application
lifecycle, domain bootstrap initialization, and proper resource cleanup.

Key Components:
- FastAPI application with CORS middleware
- Socket.IO server for real-time communication
- Domain-driven architecture initialization
- Physical controls integration
- Graceful startup and shutdown procedures
"""

from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.src.config import config
from app.src.core.application import Application
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.routes.api_routes_state import init_api_routes_state
from app.src.domain.bootstrap import domain_bootstrap
from app.src.infrastructure.error_handling.unified_error_handler import (
    UnifiedErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
)
from app.src.services.error.unified_error_decorator import handle_errors

logger = get_logger(__name__)
error_handler = UnifiedErrorHandler()

env_config = config

if isinstance(env_config.cors_allowed_origins, str):
    cors_origins = [
        origin.strip() for origin in env_config.cors_allowed_origins.split(";") if origin.strip()
    ]
else:
    cors_origins = env_config.cors_allowed_origins
if "*" in cors_origins:
    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
else:
    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=cors_origins)


@handle_errors(operation_name="initialize_application", component="main.startup")
async def _initialize_application(fastapi_app):
    """Initialize the application instance."""
    # Initialize database first to ensure tables exist
    from app.src.data.database_manager import get_database_manager
    logger.log(LogLevel.INFO, "🔧 Ensuring database is initialized...")
    try:
        db_manager = get_database_manager()
        health_info = db_manager.get_health_info()
        if health_info["status"] == "healthy":
            logger.log(LogLevel.INFO, f"✅ Database ready with {health_info['tables_count']} tables")
        else:
            logger.log(LogLevel.ERROR, f"❌ Database health check failed: {health_info}")
            raise RuntimeError(f"Database initialization failed: {health_info.get('error', 'Unknown error')}")
    except Exception as e:
        logger.log(LogLevel.ERROR, f"❌ Critical database initialization error: {e}")
        raise

    # Now initialize the application
    app_instance = Application(env_config)
    fastapi_app.application = await app_instance.initialize_async()
    return app_instance


@handle_errors(operation_name="start_domain_bootstrap", component="main.startup")
async def _start_domain_bootstrap():
    """Start the domain bootstrap."""
    if domain_bootstrap.is_initialized:
        await domain_bootstrap.start()
    else:
        context = ErrorContext(
            component="main.startup",
            operation="start_domain_bootstrap",
            category=ErrorCategory.GENERAL,
            severity=ErrorSeverity.MEDIUM,
        )
        error_handler.handle_error(RuntimeError("Domain bootstrap not initialized"), context)


@handle_errors(operation_name="setup_physical_controls", component="main.startup")
async def _setup_physical_controls(playlist_routes):
    """Setup physical controls integration with GPIO."""
    if not playlist_routes:
        context = ErrorContext(
            component="main.startup",
            operation="setup_physical_controls",
            category=ErrorCategory.HARDWARE,
            severity=ErrorSeverity.HIGH,
        )
        error_handler.handle_error(
            RuntimeError("No playlist_routes instance found, physical controls not initialized"),
            context,
        )
        return

    if hasattr(playlist_routes, "setup_controls_integration"):
        await playlist_routes.setup_controls_integration()
        logger.log(LogLevel.INFO, "✅ Physical controls integration setup completed")
    else:
        context = ErrorContext(
            component="main.startup",
            operation="setup_physical_controls",
            category=ErrorCategory.HARDWARE,
            severity=ErrorSeverity.MEDIUM,
        )
        error_handler.handle_error(
            AttributeError("Could not find setup_controls_integration method on playlist_routes"),
            context,
        )


@handle_errors(operation_name="cleanup_playlist_routes", component="main.shutdown")
async def _cleanup_playlist_routes(playlist_routes):
    """Cleanup playlist routes resources."""
    if not playlist_routes:
        return

    # Stop background tasks first
    if hasattr(playlist_routes, "cleanup_background_tasks"):
        await playlist_routes.cleanup_background_tasks()
        logger.log(LogLevel.INFO, "main.py: Background tasks cleaned up successfully.")

    # Then cleanup physical controls
    if hasattr(playlist_routes, "cleanup_controls"):
        await playlist_routes.cleanup_controls()
        logger.log(LogLevel.INFO, "main.py: Physical controls cleaned up successfully.")


@handle_errors(operation_name="cleanup_application", component="main.shutdown")
async def _cleanup_application(fastapi_app):
    """Cleanup application instance."""
    app_instance = getattr(fastapi_app, "application", None)
    if app_instance and hasattr(app_instance, "cleanup"):
        await app_instance.cleanup()
        logger.log(LogLevel.INFO, "main.py: Application instance cleaned up successfully.")


@handle_errors(operation_name="cleanup_domain", component="main.shutdown")
async def _cleanup_domain():
    """Cleanup domain architecture."""
    if domain_bootstrap.is_initialized:
        await domain_bootstrap.stop()
        domain_bootstrap.cleanup()
        logger.log(LogLevel.INFO, "✅ Domain architecture cleaned up")


@asynccontextmanager
async def lifespan(fastapi_app):
    """Application lifespan event handler for FastAPI startup and shutdown.

    Args:
        fastapi_app: The FastAPI application instance.

    Yields:
        None: Control during application runtime.
    """
    routes_organizer = None
    try:
        await _initialize_application(fastapi_app)
        await _start_domain_bootstrap()

        routes_organizer = init_api_routes_state(fastapi_app, sio, env_config)
        playlist_routes = getattr(routes_organizer, "playlist_routes", None)
        await _setup_physical_controls(playlist_routes)

        logger.log(LogLevel.INFO, "🟢 Application startup completed successfully")
        yield
        logger.log(LogLevel.INFO, "🟡 Application shutdown sequence starting...")
    except (RuntimeError, OSError, ImportError, AttributeError) as e:
        context = ErrorContext(
            component="main.lifespan",
            operation="startup",
            category=ErrorCategory.GENERAL,
            severity=ErrorSeverity.CRITICAL,
        )
        error_handler.handle_error(e, context)
        raise
    except Exception as e:
        context = ErrorContext(
            component="main.lifespan",
            operation="startup",
            category=ErrorCategory.GENERAL,
            severity=ErrorSeverity.CRITICAL,
        )
        error_handler.handle_error(e, context)
        raise
    finally:
        playlist_routes = (
            getattr(routes_organizer, "playlist_routes", None) if routes_organizer else None
        )
        await _cleanup_playlist_routes(playlist_routes)
        await _cleanup_application(fastapi_app)
        await _cleanup_domain()

        logger.log(LogLevel.INFO, "✅ Application shutdown completed")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_sio = socketio.ASGIApp(sio, other_asgi_app=app)
