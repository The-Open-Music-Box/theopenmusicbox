# app/src/config.py

"""Application configuration management module.
"""

import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from dotenv import load_dotenv
from .helpers.exceptions import AppError

@dataclass
class LogConfig:
    level: str
    format: str
    file: str

@dataclass
class ServerConfig:
    host: str
    port: int
    cors_origins: str
    use_reloader: bool

class Config:
    REQUIRED_SETTINGS = {
        'DEBUG': bool,
        'SOCKETIO_HOST': str,
        'SOCKETIO_PORT': int,
        'UPLOAD_FOLDER': str,
        'NFC_MAPPING': str,
        'CORS_ALLOWED_ORIGINS': str,
        'USE_RELOADER': bool,
        'LOG_LEVEL': str,
        'LOG_FORMAT': str,
        'LOG_FILE': str,
    }

    def __init__(self):
        self._debug = None
        self._log = LogConfig(
        level='INFO',
        format='text',
        file='logs/app.log'
        )
        self._server = ServerConfig(
            host='0.0.0.0',
            port=5000,
            cors_origins='*',
            use_reloader=False
        )

        self._upload_folder = None
        self._nfc_mapping = None

        self._load_environment()
        self._validate_required_settings()
        self._validate_directories()

    def _load_environment(self) -> None:
        env_path = Path(__file__).parent.parent / '.env'
        if not env_path.exists():
            raise AppError.configuration_error(
                message=".env file not found",
                config_key="env_file",
                details={"path": str(env_path)}
            )
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

    def _validate_required_settings(self) -> None:
        missing_vars = []

        for key, expected_type in self.REQUIRED_SETTINGS.items():
            if key not in os.environ:
                missing_vars.append(key)
                continue

            try:
                value = self._convert_env_value(os.environ[key], expected_type)
                setattr(self, f"_{key.lower()}", value)
            except Exception as exc:
                raise AppError.configuration_error(
                    message=f"Invalid configuration value for {key}",
                    config_key=key,
                    details={"error": str(exc)}
                ) from exc

        if missing_vars:
            raise AppError.configuration_error(
                message="Missing required environment variables",
                config_key="env_vars",
                details={"missing": missing_vars}
            )

    def _validate_directories(self) -> None:
        try:
            upload_path = Path(self._upload_folder)
            upload_path.mkdir(parents=True, exist_ok=True)

            log_path = Path(self._log.file).parent
            log_path.mkdir(parents=True, exist_ok=True)

            Path(self._log.file).touch(exist_ok=True)

            nfc_path = Path(self._nfc_mapping)
            nfc_path.parent.mkdir(parents=True, exist_ok=True)
            if not nfc_path.exists():
                nfc_path.write_text('[]', encoding='utf-8')

        except Exception as exc:
            raise AppError.configuration_error(
                message="Failed to create required directories/files",
                config_key="filesystem",
                details={"error": str(exc)}
            ) from exc

    @property
    def debug(self) -> bool:
        """Get debug mode flag."""
        return self._debug

    @property
    def use_reloader(self) -> bool:
        """Whether code auto-reloader is enabled."""
        return self._server.use_reloader

    @property
    def socketio_host(self) -> str:
        """Socket.IO server host address."""
        return self._server.host

    @property
    def socketio_port(self) -> int:
        """Socket.IO server port number."""
        return self._server.port

    @property
    def upload_folder(self) -> str:
        """Path to uploads directory."""
        return self._upload_folder

    @property
    def nfc_mapping_file(self) -> str:
        """Path to NFC mapping file."""
        return self._nfc_mapping

    @property
    def cors_allowed_origins(self) -> str:
        """Allowed CORS origins."""
        return self._server.cors_origins

    @property
    def log_level(self) -> str:
        """Logging level."""
        return self._log.level

    @property
    def log_format(self) -> str:
        """Log output format."""
        return self._log.format

    @property
    def log_file(self) -> str:
        """Path to log file."""
        return self._log.file
