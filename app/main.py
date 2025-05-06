import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.src.config import config_singleton
from app.src.core.container_async import ContainerAsync
from app.src.core.application import Application
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
from app.src.routes.playlist_routes import PlaylistRoutes

# Load config
env_config = config_singleton

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    yield
    await container.cleanup_async()

# FastAPI app
app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    nfc_status = {
        "available": app.container.nfc is not None,
        "code": "NFC_OK" if app.container.nfc is not None else "NFC_NOT_AVAILABLE"
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

# Dependency injection
container = ContainerAsync(env_config)
app.container = container
app.application = Application(container.config)

# --- NFC tag event subscription ---
if container.nfc is not None:
    def on_tag(tag_data):
        try:
            app.application._handle_tag_scanned(tag_data)
        except Exception as e:
            import traceback
            print(f"[NFC] Error routing tag event: {e}\n{traceback.format_exc()}")
    container.nfc.tag_subject.subscribe(on_tag)

# Register PlaylistRoutes
PlaylistRoutes(app).register()

# Register NFCRoutes
from app.src.routes.nfc_routes import NFCRoutes
NFCRoutes(app, sio, container.nfc).register()

# Init Socket.IO handlers (async)
ws_handlers = WebSocketHandlersAsync(sio, app, container.nfc)
ws_handlers.register()

