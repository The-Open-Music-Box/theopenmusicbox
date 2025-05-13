import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.src.config import config_singleton
from app.src.core.container_async import ContainerAsync
from app.src.core.application import Application
from app.src.routes.playlist_routes import PlaylistRoutes
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.routes.nfc_routes import NFCRoutes
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
import traceback


logger = ImprovedLogger(__name__)

# Load config
env_config = config_singleton

# Dependency injection container
container = ContainerAsync(env_config)

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
    
        # Set up the WebSocket handlers and routes
        if container.nfc is not None:
            # Setup Socket.IO for the NFC service
            container.set_socketio(sio)  # Pass socketio to NFCService
            
            # Instantiate NFCRoutes after NFC service is initialized
            nfc_router = NFCRoutes(fastapi_app, sio, container.nfc)
            nfc_router.register()
            
            # Instantiate WebSocket handlers with the fully initialized NFC service
            ws_handlers = WebSocketHandlersAsync(sio, fastapi_app, container.nfc)
            ws_handlers.register()
            
            # Set up NFC tag event subscription using the Application's public method
            async def on_tag(tag_data):
                # Use the encapsulated handler in Application
                await fastapi_app.application.handle_nfc_event(tag_data)
            container.nfc.tag_subject.subscribe(on_tag) # Assuming subscribe can handle async callbacks

            logger.log(LogLevel.INFO, "NFC service, routes, and WebSocket handlers initialized successfully")
        else:
            logger.log(LogLevel.WARNING, "No NFC service available - WebSocket handlers initialized without NFC support")
        
        yield
    except Exception as e:
        import traceback
        print(f"Error during startup: {e}\n{traceback.format_exc()}")
        raise
    finally:
        # Cleanup when application stops
        await container.cleanup_async()

# FastAPI app
app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    nfc_status = {
        "available": getattr(app, 'container', None) and app.container.nfc is not None,
        "code": "NFC_OK" if getattr(app, 'container', None) and app.container.nfc is not None else "NFC_NOT_AVAILABLE"
    }
    return {"status": "ok", "nfc": nfc_status}


# CORS
# Read CORS origins from the config (.env)
cors_origins = [origin.strip() for origin in env_config.cors_allowed_origins.split(';') if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO AsyncServer - use the same origins list as for CORS
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=cors_origins)
app_sio = socketio.ASGIApp(sio, other_asgi_app=app)

# Register PlaylistRoutes - these don't depend on async initialization
PlaylistRoutes(app).register()
