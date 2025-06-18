import traceback
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.src.config import config
from app.src.core.application import Application
from app.src.core.container_async import ContainerAsync
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.routes.api_routes import init_api_routes

logger = ImprovedLogger(__name__)

# Load config
env_config = config

# Dependency injection container
container = ContainerAsync(env_config)

# CORS
# Read CORS origins from the config (.env)
# Handle both string and list types for cors_allowed_origins
if isinstance(env_config.cors_allowed_origins, str):
    cors_origins = [
        origin.strip()
        for origin in env_config.cors_allowed_origins.split(";")
        if origin.strip()
    ]
else:
    cors_origins = env_config.cors_allowed_origins

# Socket.IO AsyncServer - use the same origins list as for CORS
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=cors_origins)


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
        # If container.nfc is None, APIRoutes will handle not registering
        # NFC-dependent routes.

        # Pass sio to the container if NFC is available, as APIRoutes might need
        # it for NFCService setup via container
        if container.nfc:
            # Ensure socketio is set in container for NFCService
            container.set_socketio(sio)

            # Set up NFC tag event subscription using the Application's public method
            # This logic should remain here as it's specific to the application's core behavior
            # and not just route registration.
            async def on_tag(tag_data):
                await fastapi_app.application.handle_nfc_event(tag_data)

            container.nfc.tag_subject.subscribe(on_tag)
            logger.log(
                LogLevel.INFO, "main.py: NFC tag event subscription setup complete."
            )

        # Initialize all API routes via the centralized APIRoutes
        init_api_routes(fastapi_app, sio, container)
        logger.log(
            LogLevel.INFO, "main.py: All API routes initialized via init_api_routes."
        )

        # Initialize physical controls after audio player is fully available
        # This happens after route initialization to ensure PlaylistRoutes has set
        # up its audio player reference
        playlist_routes = getattr(fastapi_app, "playlist_routes", None)
        if playlist_routes:
            # Setup controls integration with proper error handling
            try:
                # Call the controls setup method
                if hasattr(playlist_routes, "_setup_controls_integration"):
                    playlist_routes._setup_controls_integration()
                    logger.log(
                        LogLevel.INFO,
                        "main.py: Physical controls initialized successfully.",
                    )
                else:
                    logger.log(
                        LogLevel.WARNING,
                        "main.py: Could not find _setup_controls_integration method on playlist_routes",
                    )
            except Exception as e:
                logger.log(
                    LogLevel.ERROR,
                    f"main.py: Failed to initialize physical controls: {str(e)}\n{traceback.format_exc()}",
                )
        else:
            logger.log(
                LogLevel.WARNING,
                "main.py: No playlist_routes instance found, physical controls not initialized.",
            )

        yield
    except Exception as e:
        # import traceback # Already imported at the top
        print(f"Error during startup: {e}\n{traceback.format_exc()}")
        raise
    finally:
        # Cleanup when application stops
        # First shut down any physical controls
        playlist_routes = getattr(fastapi_app, "playlist_routes", None)
        if playlist_routes and hasattr(playlist_routes, "_cleanup_controls"):
            try:
                playlist_routes._cleanup_controls()
                logger.log(
                    LogLevel.INFO, "main.py: Physical controls cleaned up successfully."
                )
            except Exception as e:
                logger.log(
                    LogLevel.ERROR,
                    f"main.py: Error while cleaning up physical controls: {str(e)}",
                )

        # Then proceed with normal container cleanup
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
