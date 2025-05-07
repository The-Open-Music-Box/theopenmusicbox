"""
Standard implementation of the configuration for production environment.
"""
from pathlib import Path
from typing import Any
import os
from dotenv import load_dotenv

from app.src.helpers.exceptions import AppError
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.config.config_interface import IConfig

logger = ImprovedLogger(__name__)


class StandardConfig(IConfig):
    """
    Standard implementation of the configuration.
    Reads values from environment or uses default values.
    """
    # Defaults
    DEFAULTS = {
        'USE_MOCK_HARDWARE': False,
        'DEBUG': True,
        'SOCKETIO_HOST': '0.0.0.0',
        'SOCKETIO_PORT': 5004,
        'UPLOAD_FOLDER': 'uploads',
        'DB_FILE': 'database/app.db',
        'CORS_ALLOWED_ORIGINS': 'http://10.0.0.83:8081;http://10.0.0.10:8081;http://10.0.0.10:8080',
        'USE_RELOADER': False,
        'LOG_LEVEL': 'INFO',
        'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'LOG_FILE': 'logs/app.log',
        'APP_MODULE': 'app.main:app_sio',
        'UVICORN_RELOAD': False,
    }

    def __init__(self):
        self._load_environment()
        self._validate_directories()

    def _load_environment(self) -> None:
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            
    def _convert_env_value(self, value: str, target_type: type) -> Any:
        try:
            if target_type == bool:
                return str(value).lower() in ('true', '1', 't', 'yes')
            return target_type(value)
        except ValueError as exc:
            raise AppError.configuration_error(
                message="Invalid type for environment variable",
                config_key="type_conversion",
                details={"value": value, "expected_type": str(target_type)}
            ) from exc

    def _validate_directories(self) -> None:
        try:
            upload_path = Path(self.upload_folder)
            upload_path.mkdir(parents=True, exist_ok=True)

            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.touch(exist_ok=True)

            db_path = Path(self.db_file)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            logger.log(LogLevel.INFO, f"Config paths: uploads={upload_path}, db={db_path}")
        except Exception as exc:
            raise AppError.configuration_error(
                message="Failed to create required directories/files",
                config_key="filesystem",
                details={"error": str(exc)}
            ) from exc

    def _get(self, key, cast_type):
        val = os.environ.get(key, None)
        if val is None:
            val = self.DEFAULTS[key]
        try:
            if cast_type == bool:
                return str(val).lower() in ("true", "1", "t", "yes")
            return cast_type(val)
        except Exception as exc:
            raise AppError.configuration_error(
                message=f"Invalid value for {key}",
                config_key=key,
                details={"value": val, "expected_type": str(cast_type)}
            ) from exc

    @property
    def debug(self) -> bool:
        """Enable debug mode."""
        return self._get('DEBUG', bool)

    @property
    def use_reloader(self) -> bool:
        """Enable auto-reload for development."""
        return self._get('USE_RELOADER', bool)

    @property
    def socketio_host(self) -> str:
        """Host for Socket.IO server."""
        return self._get('SOCKETIO_HOST', str)

    @property
    def socketio_port(self) -> int:
        """Port for Socket.IO server."""
        return self._get('SOCKETIO_PORT', int)

    @property
    def upload_folder(self) -> str:
        """Uploads directory (absolute path)."""
        base = Path(__file__).parent.parent.parent
        folder = self._get('UPLOAD_FOLDER', str)
        return str(base / folder)

    @property
    def db_file(self) -> str:
        """Absolute path to SQLite database file."""
        base = Path(__file__).parent.parent.parent
        db = self._get('DB_FILE', str)
        return str(base / db)

    @property
    def cors_allowed_origins(self) -> str:
        """CORS allowed origins (semicolon-separated)."""
        return self._get('CORS_ALLOWED_ORIGINS', str)

    @property
    def log_level(self) -> str:
        """Logging level (e.g., INFO, DEBUG)."""
        return self._get('LOG_LEVEL', str)

    @property
    def log_format(self) -> str:
        """Logging format string."""
        return self._get('LOG_FORMAT', str)

    @property
    def use_mock_hardware(self) -> bool:
        """Whether to use mock hardware (for dev/testing)."""
        return self._get('USE_MOCK_HARDWARE', bool)

    @property
    def log_file(self) -> str:
        """Path to log file."""
        return self._get('LOG_FILE', str)

    @property
    def app_module(self) -> str:
        """ASGI app module for Uvicorn (e.g., app.main:app_sio)."""
        return self._get('APP_MODULE', str)

    @property
    def uvicorn_reload(self) -> bool:
        """Enable Uvicorn reload (for development)."""
        return self._get('UVICORN_RELOAD', bool)
