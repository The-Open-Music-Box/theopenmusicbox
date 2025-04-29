import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.src.config import Config
from app.src.core.container_async import ContainerAsync
from app.src.core.application import Application
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
from app.src.routes.playlist_routes import router as playlist_router

# Load config
env_config = Config()

# FastAPI app
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=env_config.cors_allowed_origins.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO AsyncServer
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=env_config.cors_allowed_origins.split(","))
app_sio = socketio.ASGIApp(sio, other_asgi_app=app)

# Dependency injection
container = ContainerAsync(env_config)
app.container = container
app.application = Application(container)

# Register playlist REST API router (FastAPI)
app.include_router(playlist_router, prefix="/api")

# Init Socket.IO handlers (async)
ws_handlers = WebSocketHandlersAsync(sio, app, container.nfc)
ws_handlers.register()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await container.cleanup_async()
