# app/src/config.py

from pathlib import Path
from typing import Any
from dotenv import load_dotenv
import os
from .helpers.exceptions import AppError
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class Config:
    REQUIRED_SETTINGS = {
        'DEBUG': bool,
        'SOCKETIO_HOST': str,
        'SOCKETIO_PORT': int,
        'UPLOAD_FOLDER': str,
        'DB_FILE': str,
        'CORS_ALLOWED_ORIGINS': str,
        'USE_RELOADER': bool,
        'LOG_LEVEL': str,
        'LOG_FORMAT': str,
        'LOG_FILE': str,
    }

    def __init__(self):
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
                self._convert_env_value(os.environ[key], expected_type)
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
            # Créer le dossier d'uploads s'il n'existe pas
            upload_path = Path(__file__).parent.parent / os.environ['UPLOAD_FOLDER']
            upload_path.mkdir(parents=True, exist_ok=True)

            # Créer le dossier des logs s'il n'existe pas
            log_path = Path(os.environ['LOG_FILE'])
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.touch(exist_ok=True)

            # Vérifier le fichier de base de données
            db_path = Path(__file__).parent.parent / os.environ['DB_FILE']
            db_path.parent.mkdir(parents=True, exist_ok=True)
            # Ne pas toucher au fichier de base de données s'il existe déjà

            logger.log(LogLevel.INFO, f"Config paths: uploads={upload_path}, db={db_path}")

        except Exception as exc:
            raise AppError.configuration_error(
                message="Failed to create required directories/files",
                config_key="filesystem",
                details={"error": str(exc)}
            ) from exc

    @property
    def debug(self) -> bool:
        return self._convert_env_value(os.environ['DEBUG'], bool)

    @property
    def use_reloader(self) -> bool:
        return self._convert_env_value(os.environ['USE_RELOADER'], bool)

    @property
    def socketio_host(self) -> str:
        return os.environ['SOCKETIO_HOST']

    @property
    def socketio_port(self) -> int:
        return int(os.environ['SOCKETIO_PORT'])

    @property
    def upload_folder(self) -> str:
        return str(Path(__file__).parent.parent / os.environ['UPLOAD_FOLDER'])

    @property
    def db_file(self) -> str:
        """
        Returns the absolute path to the SQLite database file as defined by the DB_FILE environment variable.
        By convention, this should be 'database/themusicbox.db' (relative to the project root).
        All code must use this property for database access.
        """
        return str(Path(__file__).parent.parent / os.environ['DB_FILE'])

    @property
    def cors_allowed_origins(self) -> str:
        return os.environ['CORS_ALLOWED_ORIGINS']

    @property
    def log_level(self) -> str:
        return os.environ['LOG_LEVEL']

    @property
    def log_format(self) -> str:
        return os.environ['LOG_FORMAT']

    @property
    def log_file(self) -> str:
        return os.environ['LOG_FILE']