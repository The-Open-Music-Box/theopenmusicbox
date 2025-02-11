# app/src/config.py

from pathlib import Path
from typing import Any
from dotenv import load_dotenv
import os
from .helpers.exceptions import AppError

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
            Path(os.environ['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
            Path(os.environ['LOG_FILE']).parent.mkdir(parents=True, exist_ok=True)
            Path(os.environ['LOG_FILE']).touch(exist_ok=True)

            nfc_path = Path(os.environ['NFC_MAPPING'])
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
        return os.environ['UPLOAD_FOLDER']

    @property
    def nfc_mapping_file(self) -> str:
        return str(Path(__file__).parent.parent / os.environ['NFC_MAPPING'])

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