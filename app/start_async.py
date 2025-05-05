# back/app/start_async.py

"""
Async FastAPI/Socket.IO stack launcher.
Centralizes configuration using the Config class.
The ASGI app module can be set via the APP_MODULE environment variable.
"""
from app.src.config import config_singleton as config
import uvicorn

if __name__ == "__main__":
    print(
        f"[TheMusicBox] Starting ASGI app {config.app_module} on "
        f"{config.socketio_host}:{config.socketio_port} "
        f"(reload={config.uvicorn_reload})"
    )
    uvicorn.run(
        config.app_module,
        host=config.socketio_host,
        port=config.socketio_port,
        reload=config.uvicorn_reload,
        factory=False,
    )
