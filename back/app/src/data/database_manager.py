# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Pure DDD Database Manager

Infrastructure service that provides database connectivity following DDD principles.
Implements the domain's DatabaseServiceProtocol using SQLite.
"""

from app.src.infrastructure.database.sqlite_database_service import SQLiteDatabaseService
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.config import config
import threading

# Optional migration support - will be None if not available
try:
    from app.src.data.migrations.migration_runner import MigrationRunner
except ImportError:
    MigrationRunner = None

logger = get_logger(__name__)


class DatabaseManager:
    """Pure DDD Database Manager - Infrastructure Service Layer.

    This is a singleton infrastructure service that provides database connectivity
    following DDD principles. It delegates to SQLiteDatabaseService for actual operations.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: str = None):
        if hasattr(self, "_initialized") and self._initialized:
            return

        if db_path is None:
            db_path = config.db_file

        # Initialize the SQLite database service
        self._database_service = SQLiteDatabaseService(
            database_path=db_path,
            pool_size=5
        )

        self._migration_runner = MigrationRunner(db_path) if MigrationRunner else None
        self._initialized = True

        # Run migrations if available
        self._run_migrations()

        logger.log(LogLevel.INFO, "✅ Pure DDD Database Manager initialized")

    def _run_migrations(self):
        """Run database migrations if migration runner is available."""
        if self._migration_runner:
            try:
                self._migration_runner.run_migrations()
                logger.log(LogLevel.INFO, "✅ Database migrations completed")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"❌ Migration failed: {e}")
                raise

    @property
    def database_service(self) -> SQLiteDatabaseService:
        """Get the database service for repositories.

        Returns:
            SQLiteDatabaseService instance for database operations
        """
        return self._database_service

    def get_health_info(self) -> dict:
        """Get database health information."""
        return self._database_service.get_health_info()

    def cleanup(self):
        """Clean up database manager resources."""
        if hasattr(self, '_database_service'):
            self._database_service.cleanup()
            logger.log(LogLevel.INFO, "✅ Database manager cleaned up")


# Global singleton instance functions for dependency injection
_database_manager_instance = None
_database_manager_lock = threading.Lock()


def get_database_manager() -> DatabaseManager:
    """Get the global database manager singleton instance.

    Returns:
        DatabaseManager singleton instance
    """
    global _database_manager_instance

    if _database_manager_instance is None:
        with _database_manager_lock:
            if _database_manager_instance is None:
                _database_manager_instance = DatabaseManager()
                logger.log(LogLevel.INFO, "✅ Created singleton DatabaseManager instance")

    return _database_manager_instance


def close_database_manager():
    """Close the global database manager and clean up resources."""
    global _database_manager_instance

    if _database_manager_instance is not None:
        with _database_manager_lock:
            if _database_manager_instance is not None:
                _database_manager_instance.cleanup()
                _database_manager_instance = None
                logger.log(LogLevel.INFO, "✅ Database manager singleton closed")
