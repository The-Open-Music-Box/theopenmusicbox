import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.src.config import config_singleton
from app.src.core.container_async import ContainerAsync
from app.src.core.application import Application
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
from app.src.routes.playlist_routes import PlaylistRoutes
from app.src.routes.nfc_routes import NFCRoutes
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

# Load config
env_config = config_singleton

# Dependency injection container - créé avant le lifespan
container = ContainerAsync(env_config)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(fastapi_app):
    try:
        # Initialisation asynchrone des ressources
        await container.initialize_async()
        fastapi_app.container = container  # Assigner le conteneur à l'app
        
        # Créer et initialiser l'application de manière asynchrone
        app_instance = Application(container.config)
        fastapi_app.application = await app_instance.initialize_async()
    
        # Setup Socket.IO for the NFC service
        if container.nfc is not None:
            container.set_socketio(sio)  # Pass socketio to NFCService
    
        # --- NFC tag event subscription ---
        if container.nfc is not None:
            def on_tag(tag_data):
                try:
                    fastapi_app.application.handle_tag_scanned(tag_data)  # Utiliser la méthode publique
                except ValueError as e:
                    import traceback
                    logger.log(LogLevel.ERROR, f"[NFC] Error routing tag event: {e}\n{traceback.format_exc()}")
            container.nfc.tag_subject.subscribe(on_tag)
        
        yield  # Attendre la fin de l'application
    except Exception as e:
        import traceback
        print(f"Error during startup: {e}\n{traceback.format_exc()}")
        raise
    finally:
        # Nettoyage quand l'application s'arrête
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

# L'initialisation NFC est maintenant gérée dans le lifespan asynchrone

# Register PlaylistRoutes
PlaylistRoutes(app).register()

# Register NFCRoutes
NFCRoutes(app, sio, container.nfc).register()  # container.nfc now returns NFCService with NFCHandler injected

# Init Socket.IO handlers (async)
ws_handlers = WebSocketHandlersAsync(sio, app, container.nfc)
ws_handlers.register()

