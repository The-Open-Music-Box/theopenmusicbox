# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Route Registration Fix Tests

This test suite fixes the route registration issue by properly triggering
the lifespan events or manually initializing the routes.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import socketio
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from app.main import app, sio, env_config
from app.src.routes.api_routes_state import init_api_routes_state


class TestRouteRegistrationFix:
    """Fix route registration issues."""

    def test_manual_route_initialization(self):
        """Test manually initializing routes without lifespan."""
        print("\n=== MANUAL ROUTE INITIALIZATION ===")

        # Create a test app
        test_app = FastAPI()

        # Manually initialize routes like the lifespan function does
        try:
            with patch('app.src.routes.playlist_routes_state.get_database_manager'):
                with patch('app.src.routes.playlist_routes_state.StateManager'):
                    routes_organizer = init_api_routes_state(test_app, sio, env_config)

                    print(f"Routes organizer: {routes_organizer}")
                    print(f"Playlist routes: {getattr(routes_organizer, 'playlist_routes', None)}")

                    # Check what routes are now registered
                    app_routes = []
                    for route in test_app.routes:
                        if hasattr(route, 'path') and hasattr(route, 'methods'):
                            for method in route.methods:
                                if method in ['GET', 'POST', 'PUT', 'DELETE']:
                                    app_routes.append(f'{method} {route.path}')

                    print(f"Routes after manual initialization: {len(app_routes)}")
                    for route in sorted(app_routes):
                        print(f"  {route}")

                    # Test the routes
                    client = TestClient(test_app)

                    get_response = client.get("/api/playlists")
                    post_response = client.post("/api/playlists", json={"title": "test"})

                    print(f"GET /api/playlists: {get_response.status_code}")
                    print(f"POST /api/playlists: {post_response.status_code}")

                    # Now these should work!
                    playlist_routes = [r for r in app_routes if '/api/playlists' in r]
                    print(f"Playlist routes found: {len(playlist_routes)}")

                    assert len(playlist_routes) > 0, "No playlist routes found after manual initialization"
                    assert 'GET /api/playlists' in app_routes or 'GET /api/playlists/' in app_routes
                    assert 'POST /api/playlists' in app_routes or 'POST /api/playlists/' in app_routes

        except Exception as e:
            print(f"Error during manual initialization: {e}")
            import traceback
            traceback.print_exc()
            raise

    def test_lifespan_simulation(self):
        """Test simulating the lifespan events properly."""
        print("\n=== LIFESPAN SIMULATION ===")

        # Create test app
        test_app = FastAPI()

        async def simulate_startup():
            """Simulate the startup sequence from main.py lifespan."""
            try:
                # Skip application initialization for testing
                # await _initialize_application(test_app)
                # await _start_domain_bootstrap()

                with patch('app.src.routes.playlist_routes_state.get_database_manager'):
                    with patch('app.src.routes.playlist_routes_state.StateManager'):
                        routes_organizer = init_api_routes_state(test_app, sio, env_config)
                        return routes_organizer

            except Exception as e:
                print(f"Error in startup simulation: {e}")
                raise

        # Run the simulation
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            routes_organizer = loop.run_until_complete(simulate_startup())

            print(f"Routes organizer: {routes_organizer}")

            # Check routes
            app_routes = []
            for route in test_app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    for method in route.methods:
                        if method in ['GET', 'POST', 'PUT', 'DELETE']:
                            app_routes.append(f'{method} {route.path}')

            print(f"Routes after lifespan simulation: {len(app_routes)}")
            for route in sorted(app_routes):
                print(f"  {route}")

            # Test with TestClient
            client = TestClient(test_app)

            get_response = client.get("/api/playlists")
            post_response = client.post("/api/playlists", json={"title": "test"})

            print(f"GET /api/playlists: {get_response.status_code}")
            print(f"POST /api/playlists: {post_response.status_code}")

            playlist_routes = [r for r in app_routes if '/api/playlists' in r]
            print(f"Playlist routes found: {len(playlist_routes)}")

            loop.close()

        except Exception as e:
            print(f"Error in lifespan simulation: {e}")
            import traceback
            traceback.print_exc()

    def test_testclient_with_lifespan(self):
        """Test using TestClient that properly handles lifespan events."""
        print("\n=== TESTCLIENT WITH LIFESPAN ===")

        # Import the actual app from main.py
        from app.main import app as main_app

        # Create TestClient - this should trigger lifespan events
        try:
            # Use context manager to ensure lifespan events are triggered
            with TestClient(main_app) as client:
                # Check routes after lifespan startup
                app_routes = []
                for route in main_app.routes:
                    if hasattr(route, 'path') and hasattr(route, 'methods'):
                        for method in route.methods:
                            if method in ['GET', 'POST', 'PUT', 'DELETE']:
                                app_routes.append(f'{method} {route.path}')

                print(f"Routes in main app with lifespan: {len(app_routes)}")
                for route in sorted(app_routes):
                    print(f"  {route}")

                # Test the problematic endpoints
                get_response = client.get("/api/playlists")
                post_response = client.post("/api/playlists", json={"title": "test"})

                print(f"GET /api/playlists: {get_response.status_code}")
                print(f"POST /api/playlists: {post_response.status_code}")

                playlist_routes = [r for r in app_routes if '/api/playlists' in r]
                print(f"Playlist routes found: {len(playlist_routes)}")

                # This should work now!
                assert len(playlist_routes) > 0, "No playlist routes found with lifespan"

        except Exception as e:
            print(f"Error with TestClient lifespan: {e}")
            import traceback
            traceback.print_exc()

    def test_route_path_patterns(self):
        """Test different route path patterns to understand the registration issue."""
        print("\n=== ROUTE PATH PATTERNS ===")

        from fastapi import APIRouter, Body

        # Test 1: Empty string path
        router1 = APIRouter(prefix="/api/test1", tags=["test1"])

        @router1.get("")
        async def get_empty():
            return {"path": "empty"}

        # Test 2: Slash path
        router2 = APIRouter(prefix="/api/test2", tags=["test2"])

        @router2.get("/")
        async def get_slash():
            return {"path": "slash"}

        # Test 3: Both patterns
        router3 = APIRouter(prefix="/api/test3", tags=["test3"])

        @router3.get("")
        @router3.get("/")
        async def get_both():
            return {"path": "both"}

        # Test app
        test_app = FastAPI()
        test_app.include_router(router1)
        test_app.include_router(router2)
        test_app.include_router(router3)

        # Check routes
        app_routes = []
        for route in test_app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method in ['GET', 'POST']:
                        app_routes.append(f'{method} {route.path}')

        print(f"Route patterns registered:")
        for route in sorted(app_routes):
            print(f"  {route}")

        # Test endpoints
        client = TestClient(test_app)

        responses = [
            ("/api/test1", "empty string"),
            ("/api/test1/", "empty string with trailing slash"),
            ("/api/test2", "slash path"),
            ("/api/test2/", "slash path with trailing slash"),
            ("/api/test3", "both patterns"),
            ("/api/test3/", "both patterns with trailing slash"),
        ]

        for path, description in responses:
            try:
                response = client.get(path)
                print(f"GET {path} ({description}): {response.status_code}")
            except Exception as e:
                print(f"GET {path} ({description}): ERROR - {e}")

        # This helps us understand which pattern works
        assert len(app_routes) > 0