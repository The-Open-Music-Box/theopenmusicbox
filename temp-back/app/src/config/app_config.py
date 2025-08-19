# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""
Unified configuration system for TheOpenMusicBox application.

Loads settings exclusively from .env file and provides centralized configuration for all
modules.
"""

import logging
import os
from pathlib import Path
from typing import Any, List

from dotenv import load_dotenv

from app.src.config.audio_config import AudioConfig
from app.src.config.hardware_config import HardwareConfig
from app.src.config.nfc_config import NFCConfig

logger = logging.getLogger(__name__)


class AppConfig:
    """
    Unified configuration class for TheOpenMusicBox application.

    This class handles all configuration settings, loading them from: 1. Default values
    2. Environment variables / .env file

    Usage:     from app.src.config import config     db_path = config.db_file
    """

    # mDNS/zeroconf configuration keys:
    #   - mdns_service_type: Service type (e.g., _http._tcp.local.)
    #   - mdns_service_name: Service name (e.g., TheOpenMusicBox._http._tcp.local)
    #   - mdns_service_hostname: Hostname for the service (e.g., tmbdev.local.)
    #   - mdns_service_path: Path property for service (e.g., /api)
    #   - mdns_service_version: Version property (e.g., 1.0)
    #   - mdns_service_friendly_name: Human-friendly name (e.g., The Open Music Box)

    # Default configuration values
    DEFAULTS = {
        "debug": True,
        "use_reloader": False,
        "socketio_host": "0.0.0.0",
        "socketio_port": 5004,
        "upload_folder": "data/uploads",
        "db_file": "data/app.db",
        "cors_allowed_origins": "http://localhost:8080;http://localhost:8081;http://theopenmusicbox.local:5004;*",
        "log_level": "INFO",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_file": "logs/app.log",
        "use_mock_hardware": False,
        "app_module": "app.main:app_sio",
        "uvicorn_reload": False,
        "upload_allowed_extensions": "mp3;wav;flac;ogg;m4a",
        "upload_max_size": 50 * 1024 * 1024,
        # mDNS/zeroconf service defaults
        "mdns_service_type": "_http._tcp.local.",
        "mdns_service_path": "/api",
        "mdns_service_version": "1.0",
        "mdns_service_friendly_name": "The Open Music Box",
    }

    def __init__(self):
        """
        Initialize the configuration with values from environment.
        """
        self._values = {}
        self._load_defaults()
        self._load_environment()
        self._validate_directories()

        # Initialize sub-configurations
        self.audio = AudioConfig()
        self.hardware = HardwareConfig()
        self.nfc = NFCConfig()

        # Override sub-config values from environment if present
        self._load_subconfig_overrides()

        # Validate all configurations
        self._validate_configs()

    def _load_defaults(self) -> None:
        """
        Load default configuration values.
        """
        self._values.update(self.DEFAULTS)

    def _load_environment(self) -> None:
        """
        Load configuration from environment variables and .env file.
        """
        # Try to load from .env file
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info("Loaded configuration from %s", env_path)
        else:
            logger.warning("No .env file found at %s, using defaults", env_path)

        # Override with environment variables
        for key in self.DEFAULTS.keys():
            env_key = key.upper()
            if env_key in os.environ:
                self._values[key] = self._convert_env_value(
                    os.environ[env_key], type(self.DEFAULTS[key])
                )
                logger.debug("Loaded %s=%s from environment", key, self._values[key])

    def _validate_directories(self) -> None:
        """
        Ensure required directories exist.
        """
        # Get the app directory path (parent of src)
        app_dir = Path(__file__).parent.parent.parent

        # Use property methods to get the fully resolved paths
        # This ensures we use the same logic as the rest of the application

        # Handle upload folder
        upload_path = Path(self.upload_folder)
        if not upload_path.is_absolute():
            upload_path = app_dir / upload_path
        upload_path.mkdir(parents=True, exist_ok=True)
        logger.info("✓ Config paths: uploads=%s", upload_path)

        # Handle database file - create its parent directory
        db_path = Path(self.db_file)
        if not db_path.is_absolute():
            db_path = app_dir / db_path
        db_dir = db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✓ Config paths: db=%s", db_dir)

        # Ensure log directory exists
        log_path = Path(self.log_file)
        if not log_path.is_absolute():
            log_path = app_dir / log_path
        log_dir = log_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)

    def _convert_env_value(self, value: str, target_type: type) -> Any:
        """
        Convert string environment variable to the appropriate type.

        Args:     value: String value from environment     target_type: Target type to
        convert to

        Returns:     Converted value
        """
        try:
            if target_type == bool:
                return str(value).lower() in ("true", "1", "t", "yes")
            elif target_type == int:
                return int(value)
            elif target_type == float:
                return float(value)
            elif target_type == list:
                return value.split(";")
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.error("Error converting value '%s' to %s: %s", value, target_type, e)
            # Fallback: return the default for the requested type if possible
            if target_type == bool:
                return False
            elif target_type == int:
                return 0
            elif target_type == float:
                return 0.0
            elif target_type == list:
                return []
            else:
                return None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:     key: Configuration key     default: Default value if key doesn't exist

        Returns:     Configuration value or default
        """
        return self._values.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """
        Access configuration values as attributes.

        Args:     name: Attribute name

        Returns:     Configuration value

        Raises:     AttributeError: If configuration key doesn't exist
        """
        if name in self._values:
            return self._values[name]
        raise AttributeError(f"Configuration has no attribute '{name}'")

    @property
    def debug(self) -> bool:
        """
        Whether debug mode is enabled.
        """
        return self._values.get("debug", False)

    @property
    def use_reloader(self) -> bool:
        """
        Whether to use auto-reloader.
        """
        return self._values.get("use_reloader", False)

    @property
    def socketio_host(self) -> str:
        """
        Host for Socket.IO server.
        """
        return self._values.get("socketio_host", "0.0.0.0")

    @property
    def socketio_port(self) -> int:
        """
        Port for Socket.IO server (required).
        """
        value = self._values.get("socketio_port")
        if value is None:
            raise ValueError(
                "Critical config missing: 'socketio_port' must be set in config/environment."
            )
        return int(value)

    @property
    def upload_folder(self) -> str:
        """
        Directory for uploaded files (required).

        Returns the absolute path to the upload folder, ensuring it resolves correctly
        regardless of the working directory at runtime.
        """
        value = self._values.get("upload_folder")
        if not value:
            raise ValueError(
                "Critical config missing: 'upload_folder' must be set in config/environment."
            )

        # Get the app directory path (parent of src)
        app_dir = Path(__file__).parent.parent.parent

        # If value is a relative path, make it absolute from app_dir
        path = Path(value)
        if not path.is_absolute():
            path = app_dir / path

        # Log the absolute path for debugging
        logger.debug("Resolved upload_folder path: %s", path)

        return str(path)

    @property
    def upload_allowed_extensions(self) -> List[str]:
        """
        List of allowed upload extensions.
        """
        value = self._values.get("upload_allowed_extensions", "")
        return value.split(";") if isinstance(value, str) else value

    @property
    def upload_max_size(self) -> int:
        """
        Maximum upload file size in bytes.
        """
        value = self._values.get("upload_max_size")
        if value is None:
            raise ValueError(
                "Critical config missing: 'upload_max_size' must be set in config/environment."
            )
        return int(value)

    @property
    def cors_allowed_origins(self) -> List[str]:
        """
        List of allowed CORS origins.
        """
        value = self._values.get("cors_allowed_origins", "")
        return value.split(";") if isinstance(value, str) else value

    @property
    def db_file(self) -> str:
        """
        Path to SQLite database file (required).

        Returns the absolute path to the database file, ensuring it resolves correctly
        regardless of the working directory at runtime.
        """
        value = self._values.get("db_file")
        if not value:
            raise ValueError(
                "Critical config missing: 'db_file' must be set in config/environment."
            )

        # Get the app directory path (parent of src)
        app_dir = Path(__file__).parent.parent.parent

        # If value is a relative path, make it absolute from app_dir
        path = Path(value)
        if not path.is_absolute():
            path = app_dir / path

        # Log the absolute path for debugging
        logger.debug("Resolved db_file path: %s", path)

        return str(path)

    @property
    def log_format(self) -> str:
        """
        Logging format.
        """
        return self._values.get(
            "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    @property
    def log_file(self) -> str:
        """
        Path to log file.
        """
        return self._values.get("log_file", "logs/app.log")

    @property
    def use_mock_hardware(self) -> bool:
        """
        Whether to use mock hardware.
        """
        return self._values.get("use_mock_hardware", False)

    @property
    def app_module(self) -> str:
        """
        ASGI app module for Uvicorn.
        """
        return self._values.get("app_module", "app.main:app_sio")

    @property
    def uvicorn_reload(self) -> bool:
        """
        Whether to enable Uvicorn reload.
        """
        return self._values.get("uvicorn_reload", False)

    # mDNS/zeroconf properties
    @property
    def mdns_service_type(self) -> str:
        """
        Service type for mDNS/zeroconf (e.g. _http._tcp.local.).

        Returns the service type string.
        """
        return self._values.get("mdns_service_type", "_http._tcp.local.")

    @property
    def mdns_service_name(self) -> str:
        """
        Service name for mDNS/zeroconf.

        If not set in config/env, generates a unique name using the system hostname.
        Example: MusicBox-<hostname>._http._tcp.local
        """
        value = self._values.get("mdns_service_name")
        if value:
            return value
        import socket

        hostname = socket.gethostname()
        return f"MusicBox-{hostname}._http._tcp.local"

    @property
    def mdns_service_hostname(self) -> str:
        """
        Get the hostname property for mDNS/zeroconf service.

        Example: <hostname>.local. If not set in config/env, generates <hostname>.local.
        using the system hostname.
        """
        value = self._values.get("mdns_service_hostname")
        if value:
            return value
        import socket

        hostname = socket.gethostname()
        return f"{hostname}.local."

    @property
    def mdns_service_path(self) -> str:
        """
        Path property for mDNS/zeroconf service (e.g. /api).
        """
        return self._values.get("mdns_service_path", "/api")

    @property
    def mdns_service_version(self) -> str:
        """
        Version property for mDNS/zeroconf service (e.g. 1.0).
        """
        return self._values.get("mdns_service_version", "1.0")

    @property
    def mdns_service_friendly_name(self) -> str:
        """
        Human-friendly name for mDNS/zeroconf service.

        The name is used to identify the service in a user-friendly way.
        """
        return self._values.get("mdns_service_friendly_name", "The Open Music Box")

    def _load_subconfig_overrides(self) -> None:
        """
        Load environment overrides for sub-configurations.
        """
        # Audio config overrides
        if "AUDIO_DEFAULT_VOLUME" in os.environ:
            self.audio.default_volume = int(os.environ["AUDIO_DEFAULT_VOLUME"])
        if "AUDIO_VOLUME_STEP" in os.environ:
            self.audio.volume_step = int(os.environ["AUDIO_VOLUME_STEP"])

        # Hardware config overrides
        if "HARDWARE_MOCK" in os.environ:
            self.hardware.mock_hardware = os.environ["HARDWARE_MOCK"].lower() in (
                "true",
                "1",
                "yes",
            )
        if "GPIO_NEXT_BUTTON" in os.environ:
            self.hardware.gpio_next_track_button = int(os.environ["GPIO_NEXT_BUTTON"])
        if "GPIO_PREV_BUTTON" in os.environ:
            self.hardware.gpio_previous_track_button = int(
                os.environ["GPIO_PREV_BUTTON"]
            )
        if "GPIO_VOLUME_CLK" in os.environ:
            self.hardware.gpio_volume_encoder_clk = int(os.environ["GPIO_VOLUME_CLK"])
        if "GPIO_VOLUME_DT" in os.environ:
            self.hardware.gpio_volume_encoder_dt = int(os.environ["GPIO_VOLUME_DT"])
        if "GPIO_VOLUME_SW" in os.environ:
            self.hardware.gpio_volume_encoder_sw = int(os.environ["GPIO_VOLUME_SW"])

        # NFC config overrides
        if "NFC_AUTO_PAUSE" in os.environ:
            self.nfc.auto_pause_enabled = os.environ["NFC_AUTO_PAUSE"].lower() in (
                "true",
                "1",
                "yes",
            )
        if "NFC_AUTO_RESUME" in os.environ:
            self.nfc.auto_resume_enabled = os.environ["NFC_AUTO_RESUME"].lower() in (
                "true",
                "1",
                "yes",
            )

    def _validate_configs(self) -> None:
        """
        Validate all sub-configurations.
        """
        try:
            self.audio.validate()
            self.hardware.validate()
            self.nfc.validate()
        except ValueError as e:
            logger.error("Configuration validation failed: %s", e)
            raise


# Create the single global instance
config = AppConfig()
