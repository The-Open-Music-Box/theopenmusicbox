# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Production database diagnosis test.

This test uses the actual production database to diagnose the persistence issue.
"""

import pytest
import asyncio
from unittest.mock import patch

from app.src.dependencies import get_playlist_repository_adapter
from app.src.application.services.playlist_application_service import playlist_app_service


class TestProductionDatabaseDiagnosis:
    """Diagnosis using production database setup."""

    @pytest.mark.asyncio
    async def test_production_app_service_persistence(self):
        """Test the exact same path used in production."""
        print("\n=== PRODUCTION DATABASE DIAGNOSIS ===")

        # Use the actual production singleton instances
        adapter = get_playlist_repository_adapter()
        app_service = playlist_app_service

        print(f"Using adapter: {adapter}")
        print(f"Using app service: {app_service}")
        print(f"App service repository: {app_service._playlist_repository}")

        # Check initial count
        initial_result = await app_service.get_all_playlists_use_case(page=1, page_size=50)
        initial_count = len(initial_result.get("playlists", []))
        print(f"Initial playlist count: {initial_count}")

        # Create a playlist (same as production)
        create_result = await app_service.create_playlist_use_case(
            "Production Diagnosis Test",
            "Testing production persistence"
        )
        print(f"Create result: {create_result}")

        # Check count immediately after creation
        immediate_result = await app_service.get_all_playlists_use_case(page=1, page_size=50)
        immediate_count = len(immediate_result.get("playlists", []))
        print(f"Immediate count after creation: {immediate_count}")

        # Should have increased by 1
        assert immediate_count == initial_count + 1, f"Expected {initial_count + 1}, got {immediate_count}"

        # Create a new app service instance to simulate different request
        new_app_service = playlist_app_service  # This should be the same singleton
        second_result = await new_app_service.get_all_playlists_use_case(page=1, page_size=50)
        second_count = len(second_result.get("playlists", []))
        print(f"Count with 'new' app service instance: {second_count}")

        # Should still be the same
        assert second_count == immediate_count, f"Expected {immediate_count}, got {second_count}"

        print("=== DIAGNOSIS SUCCESSFUL ===")

    @pytest.mark.asyncio
    async def test_repository_instance_consistency(self):
        """Test that all components use the same repository instance."""
        print("\n=== REPOSITORY INSTANCE CONSISTENCY ===")

        # Get instances
        adapter1 = get_playlist_repository_adapter()
        adapter2 = get_playlist_repository_adapter()

        print(f"Adapter 1: {id(adapter1)}")
        print(f"Adapter 2: {id(adapter2)}")
        print(f"Same adapter instance: {adapter1 is adapter2}")

        # Check if they use the same repository
        repo1 = adapter1._repo
        repo2 = adapter2._repo

        print(f"Repository 1: {id(repo1)}")
        print(f"Repository 2: {id(repo2)}")
        print(f"Same repository instance: {repo1 is repo2}")

        # Check database service
        db_service1 = repo1._db_service
        db_service2 = repo2._db_service

        print(f"DB Service 1: {id(db_service1)}")
        print(f"DB Service 2: {id(db_service2)}")
        print(f"Same database service: {db_service1 is db_service2}")

        assert adapter1 is adapter2, "Adapters should be the same singleton instance"
        assert repo1 is repo2, "Repositories should be the same singleton instance"
        assert db_service1 is db_service2, "Database services should be the same instance"

    @pytest.mark.asyncio
    async def test_database_file_path_consistency(self):
        """Test that all components use the same database file path."""
        print("\n=== DATABASE FILE PATH CONSISTENCY ===")

        from app.src.config import config
        from app.src.data.database_manager import get_database_manager

        print(f"Config DB file: {config.db_file}")

        # Get database manager
        db_manager = get_database_manager()
        print(f"Database manager: {db_manager}")
        print(f"Database service path: {db_manager.database_service.database_path}")

        # Get repository and check its path
        adapter = get_playlist_repository_adapter()
        repo = adapter._repo
        db_service = repo._db_service

        print(f"Repository DB service path: {db_service.database_path}")

        # All paths should be the same
        config_path = config.db_file
        manager_path = db_manager.database_service.database_path
        repo_path = db_service.database_path

        print(f"Config path: {config_path}")
        print(f"Manager path: {manager_path}")
        print(f"Repository path: {repo_path}")

        assert manager_path == repo_path, f"Manager and repository paths differ: {manager_path} vs {repo_path}"

    @pytest.mark.asyncio
    async def test_raw_database_verification(self):
        """Test by checking the actual database file directly."""
        print("\n=== RAW DATABASE VERIFICATION ===")

        from app.src.data.database_manager import get_database_manager

        # Get the actual database service
        db_manager = get_database_manager()
        db_service = db_manager.database_service

        print(f"Database file: {db_service.database_path}")

        # Check what's actually in the database before creating
        before_raw = db_service.execute_query(
            "SELECT COUNT(*) as count FROM playlists",
            None,
            "count_before"
        )
        before_count = before_raw[0]["count"] if before_raw else 0
        print(f"Raw DB count before: {before_count}")

        # Create via app service
        app_service = playlist_app_service
        create_result = await app_service.create_playlist_use_case(
            "Raw DB Test",
            "Testing raw database access"
        )
        print(f"Created via app service: {create_result}")

        # Check raw database immediately after
        after_raw = db_service.execute_query(
            "SELECT COUNT(*) as count FROM playlists",
            None,
            "count_after"
        )
        after_count = after_raw[0]["count"] if after_raw else 0
        print(f"Raw DB count after: {after_count}")

        # Check via app service
        app_result = await app_service.get_all_playlists_use_case(page=1, page_size=50)
        app_count = len(app_result.get("playlists", []))
        print(f"App service count: {app_count}")

        # Raw database should have increased
        assert after_count == before_count + 1, f"Raw DB should have {before_count + 1}, has {after_count}"

        # App service count should match raw count
        assert app_count == after_count, f"App service count {app_count} doesn't match raw DB count {after_count}"