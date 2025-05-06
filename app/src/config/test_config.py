"""
Configuration specific for tests.
"""
from pathlib import Path
from app.src.config.config_interface import IConfig


class TestConfig(IConfig):
    """
    Configuration for tests with configurable paths.
    All methods return fixed values suitable for testing.
    """

    def __init__(self, base_path=None):
        """
        Initialize the test configuration.
        
        Args:
            base_path: Base path for files and folders (if None, uses an in-memory path)
        """
        self._base_path = Path(base_path) if base_path else Path("/tmp/test_musicbox")
        self._db_path = self._base_path / "test.db"
        self._upload_path = self._base_path / "uploads"
        
        # Create necessary directories
        self._upload_path.mkdir(parents=True, exist_ok=True)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def debug(self) -> bool:
        return True

    @property
    def use_reloader(self) -> bool:
        return False

    @property
    def socketio_host(self) -> str:
        return "localhost"

    @property
    def socketio_port(self) -> int:
        return 5005

    @property
    def upload_folder(self) -> str:
        return str(self._upload_path)

    @property
    def db_file(self) -> str:
        return str(self._db_path)
    
    # Allow modifying the DB path for tests
    @db_file.setter
    def db_file(self, value):
        self._db_path = Path(value)

    @property
    def cors_allowed_origins(self) -> str:
        return "http://localhost:8080"

    @property
    def log_level(self) -> str:
        return "DEBUG"

    @property
    def log_format(self) -> str:
        return "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def use_mock_hardware(self) -> bool:
        return True

    @property
    def log_file(self) -> str:
        return str(self._base_path / "test.log")

    @property
    def app_module(self) -> str:
        return "app.main:app_sio"

    @property
    def uvicorn_reload(self) -> bool:
        return False
