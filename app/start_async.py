# app/start_async.py
"""
Async FastAPI/Socket.IO stack launcher.
Centralizes configuration using the Config class. The ASGI app module can be set via the APP_MODULE environment variable.
"""
from app.src.config import Config
import uvicorn

if __name__ == "__main__":
    config = Config()
    host = config.socketio_host
    port = config.socketio_port
    uvicorn.run(
        config.app_module,
        host=host,
        port=port,
        reload=config.uvicorn_reload,
        factory=False,
    )

