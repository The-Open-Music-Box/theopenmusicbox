# back/app/main.py

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.src.config import config_singleton
from app.src.core.container_async import ContainerAsync
from app.src.core.application import Application
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync

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
    return {"status": "ok"}


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
app.application = Application(container)

# Register PlaylistRoutes
from app.src.routes.playlist_routes import PlaylistRoutes
PlaylistRoutes(app).register()


# Init Socket.IO handlers (async)
ws_handlers = WebSocketHandlersAsync(sio, app, container.nfc)
ws_handlers.register()

