"""
Interface defining the contract for all configurations.
"""
from abc import ABC, abstractmethod


class IConfig(ABC):
    """Common interface for all configurations."""

    @property
    @abstractmethod
    def debug(self) -> bool:
        """Enable debug mode."""
        pass

    @property
    @abstractmethod
    def use_reloader(self) -> bool:
        """Enable auto-reload for development."""
        pass

    @property
    @abstractmethod
    def socketio_host(self) -> str:
        """Host for Socket.IO server."""
        pass

    @property
    @abstractmethod
    def socketio_port(self) -> int:
        """Port for Socket.IO server."""
        pass

    @property
    @abstractmethod
    def upload_folder(self) -> str:
        """Uploads directory (absolute path)."""
        pass

    @property
    @abstractmethod
    def db_file(self) -> str:
        """Absolute path to SQLite database file."""
        pass

    @property
    @abstractmethod
    def cors_allowed_origins(self) -> str:
        """CORS allowed origins (semicolon-separated)."""
        pass

    @property
    @abstractmethod
    def log_level(self) -> str:
        """Logging level (e.g., INFO, DEBUG)."""
        pass

    @property
    @abstractmethod
    def log_format(self) -> str:
        """Logging format string."""
        pass

    @property
    @abstractmethod
    def use_mock_hardware(self) -> bool:
        """Whether to use mock hardware (for dev/testing)."""
        pass

    @property
    @abstractmethod
    def log_file(self) -> str:
        """Path to log file."""
        pass

    @property
    @abstractmethod
    def app_module(self) -> str:
        """ASGI app module for Uvicorn (e.g., app.main:app_sio)."""
        pass

    @property
    @abstractmethod
    def uvicorn_reload(self) -> bool:
        """Enable Uvicorn reload (for development)."""
        pass
