import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.src.config import config_singleton
from app.src.core.container_async import ContainerAsync
from app.src.core.application import Application
# PlaylistRoutes will be handled by APIRoutes
# from app.src.routes.playlist_routes import PlaylistRoutes
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
# NFCRoutes and WebSocketHandlersAsync will be handled by APIRoutes
# from app.src.routes.nfc_routes import NFCRoutes
# from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
# Import init_api_routes
from app.src.routes.api_routes import init_api_routes
import traceback


logger = ImprovedLogger(__name__)

# Load config
env_config = config_singleton

# Dependency injection container
container = ContainerAsync(env_config)

# CORS
# Read CORS origins from the config (.env)
cors_origins = [origin.strip() for origin in env_config.cors_allowed_origins.split(';') if origin.strip()]

# Socket.IO AsyncServer - use the same origins list as for CORS
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=cors_origins)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(fastapi_app):
    try:
        # Async resource initialization
        await container.initialize_async()
        fastapi_app.container = container  # Assign container to app

        # Create and initialize the application asynchronously
        app_instance = Application(container.config)
        fastapi_app.application = await app_instance.initialize_async()

        # Centralized route initialization using APIRoutes
        # Ensure sio is available in this scope for APIRoutes
        # The original sio is defined later, so we need to ensure it's passed correctly.
        # For now, assuming sio is accessible or passed appropriately.
        # If container.nfc is None, APIRoutes will handle not registering NFC-dependent routes.

        # Pass sio to the container if NFC is available, as APIRoutes might need it for NFCService setup via container
        if container.nfc:
            container.set_socketio(sio) # Ensure socketio is set in container for NFCService

            # Set up NFC tag event subscription using the Application's public method
            # This logic should remain here as it's specific to the application's core behavior
            # and not just route registration.
            async def on_tag(tag_data):
                await fastapi_app.application.handle_nfc_event(tag_data)
            container.nfc.tag_subject.subscribe(on_tag)
            logger.log(LogLevel.INFO, "main.py: NFC tag event subscription setup complete.")

        # Initialize all API routes via the centralized APIRoutes
        init_api_routes(fastapi_app, sio, container)
        logger.log(LogLevel.INFO, "main.py: All API routes initialized via init_api_routes.")

        yield
    except Exception as e:
        # import traceback # Already imported at the top
        print(f"Error during startup: {e}\n{traceback.format_exc()}")
        raise
    finally:
        # Cleanup when application stops
        await container.cleanup_async()

# FastAPI app
app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the ASGI app with Socket.IO
app_sio = socketio.ASGIApp(sio, other_asgi_app=app)
