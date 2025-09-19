# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Route Registration Investigation Tests

This test suite investigates why GET/POST /api/playlists routes return 404
despite being defined in the PlaylistRoutesState class.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import socketio
from unittest.mock import MagicMock, patch

from app.main import app
from app.src.routes.playlist_routes_state import PlaylistRoutesState
from app.src.routes.api_routes_state import APIRoutesState


class TestRouteRegistrationInvestigation:
    """Investigate route registration issues."""

    def test_app_routes_inspection(self):
        """Inspect what routes are actually registered with the FastAPI app."""
        print("\n=== APP ROUTES INSPECTION ===")

        # Get all routes from the FastAPI app
        all_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method in ['GET', 'POST', 'PUT', 'DELETE']:
                        all_routes.append(f'{method} {route.path}')

        print(f"Total routes registered: {len(all_routes)}")

        # Filter for playlist-related routes
        playlist_routes = [r for r in all_routes if '/api/playlists' in r]
        upload_routes = [r for r in all_routes if '/api/uploads' in r]

        print(f"\nPlaylist routes found: {len(playlist_routes)}")
        for route in sorted(playlist_routes):
            print(f"  {route}")

        print(f"\nUpload routes found: {len(upload_routes)}")
        for route in sorted(upload_routes):
            print(f"  {route}")

        print(f"\nAll routes:")
        for route in sorted(all_routes):
            print(f"  {route}")

        # The issue: we expect playlist routes but they're not registered
        assert len(all_routes) > 0, "No routes registered at all"

    def test_playlist_routes_state_initialization(self):
        """Test if PlaylistRoutesState initializes correctly."""
        print("\n=== PLAYLIST ROUTES STATE INITIALIZATION ===")

        # Create mock dependencies
        mock_app = FastAPI()
        mock_socketio = MagicMock()
        mock_config = MagicMock()

        # Try to initialize PlaylistRoutesState
        try:
            with patch('app.src.routes.playlist_routes_state.get_database_manager'):
                with patch('app.src.routes.playlist_routes_state.StateManager'):
                    playlist_routes = PlaylistRoutesState(mock_app, mock_socketio, mock_config)

                    print(f"PlaylistRoutesState initialized: {playlist_routes}")
                    print(f"Router prefix: {playlist_routes.router.prefix}")
                    print(f"Router tags: {playlist_routes.router.tags}")

                    # Check if routes are defined in the router
                    routes_in_router = []
                    for route in playlist_routes.router.routes:
                        if hasattr(route, 'path') and hasattr(route, 'methods'):
                            for method in route.methods:
                                if method in ['GET', 'POST', 'PUT', 'DELETE']:
                                    routes_in_router.append(f'{method} {route.path}')

                    print(f"Routes in router: {len(routes_in_router)}")
                    for route in sorted(routes_in_router):
                        print(f"  {route}")

                    # Test router registration
                    print(f"\nTesting router registration...")
                    playlist_routes.register()

                    # Check if routes are now in the app
                    app_routes_after = []
                    for route in mock_app.routes:
                        if hasattr(route, 'path') and hasattr(route, 'methods'):
                            for method in route.methods:
                                if method in ['GET', 'POST', 'PUT', 'DELETE']:
                                    app_routes_after.append(f'{method} {route.path}')

                    print(f"Routes in app after registration: {len(app_routes_after)}")
                    for route in sorted(app_routes_after):
                        print(f"  {route}")

                    # The key test: are GET/POST /api/playlists in the router?
                    expected_routes = [
                        'GET /api/playlists',
                        'POST /api/playlists'
                    ]

                    for expected in expected_routes:
                        route_parts = expected.split(' ', 1)
                        method = route_parts[0]
                        path = route_parts[1].replace('/api/playlists', '')  # Remove prefix

                        # Check if this route exists in the router
                        found = False
                        for route in playlist_routes.router.routes:
                            if hasattr(route, 'path') and hasattr(route, 'methods'):
                                if (method in route.methods and
                                    (route.path == path or route.path == path + '/' or route.path == path.rstrip('/'))):
                                    found = True
                                    break

                        print(f"Route {expected} found in router: {found}")

        except Exception as e:
            print(f"Error initializing PlaylistRoutesState: {e}")
            import traceback
            traceback.print_exc()

    def test_api_routes_state_initialization(self):
        """Test if APIRoutesState initializes and registers routes correctly."""
        print("\n=== API ROUTES STATE INITIALIZATION ===")

        mock_app = FastAPI()
        mock_socketio = MagicMock()
        mock_config = MagicMock()

        try:
            with patch('app.src.routes.playlist_routes_state.get_database_manager'):
                with patch('app.src.routes.playlist_routes_state.StateManager'):
                    # Initialize APIRoutesState (this is what main.py does)
                    api_routes = APIRoutesState(mock_app, mock_socketio, mock_config)

                    print(f"APIRoutesState initialized: {api_routes}")
                    print(f"Playlist routes: {api_routes.playlist_routes}")

                    # Initialize routes
                    api_routes.init_routes()

                    # Check what routes are now registered
                    app_routes = []
                    for route in mock_app.routes:
                        if hasattr(route, 'path') and hasattr(route, 'methods'):
                            for method in route.methods:
                                if method in ['GET', 'POST', 'PUT', 'DELETE']:
                                    app_routes.append(f'{method} {route.path}')

                    print(f"Routes registered via APIRoutesState: {len(app_routes)}")
                    for route in sorted(app_routes):
                        print(f"  {route}")

                    # Check for the problematic routes
                    problematic_routes = [
                        'GET /api/playlists',
                        'POST /api/playlists'
                    ]

                    for route in problematic_routes:
                        found = route in app_routes
                        print(f"Route {route} registered: {found}")

        except Exception as e:
            print(f"Error with APIRoutesState: {e}")
            import traceback
            traceback.print_exc()

    def test_direct_router_functionality(self):
        """Test the router directly to see if routes are defined correctly."""
        print("\n=== DIRECT ROUTER FUNCTIONALITY ===")

        # Create a minimal router test
        from fastapi import APIRouter, Body

        # Create router exactly like PlaylistRoutesState does
        router = APIRouter(prefix="/api/playlists", tags=["playlists"])

        # Add the problematic routes manually
        @router.get("")
        @router.get("/")
        async def list_playlists():
            return {"message": "List playlists"}

        @router.post("/")
        async def create_playlist(body: dict = Body(...)):
            return {"message": "Create playlist"}

        # Test router routes
        router_routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method in ['GET', 'POST', 'PUT', 'DELETE']:
                        router_routes.append(f'{method} {route.path}')

        print(f"Routes in test router: {len(router_routes)}")
        for route in sorted(router_routes):
            print(f"  {route}")

        # Test with FastAPI app
        test_app = FastAPI()
        test_app.include_router(router)

        app_routes = []
        for route in test_app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method in ['GET', 'POST', 'PUT', 'DELETE']:
                        app_routes.append(f'{method} {route.path}')

        print(f"Routes in test app after include_router: {len(app_routes)}")
        for route in sorted(app_routes):
            print(f"  {route}")

        # Test the routes with TestClient
        client = TestClient(test_app)

        get_response = client.get("/api/playlists")
        post_response = client.post("/api/playlists", json={"title": "test"})

        print(f"GET /api/playlists status: {get_response.status_code}")
        print(f"POST /api/playlists status: {post_response.status_code}")

        # This should work if the issue is not with route definition
        assert get_response.status_code == 200
        assert post_response.status_code == 200

    def test_main_app_route_registration_flow(self):
        """Test the actual flow that happens in main.py."""
        print("\n=== MAIN APP ROUTE REGISTRATION FLOW ===")

        # Import what main.py uses
        from app.main import app as main_app

        # Check what's currently registered
        current_routes = []
        for route in main_app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method in ['GET', 'POST', 'PUT', 'DELETE']:
                        current_routes.append(f'{method} {route.path}')

        print(f"Current routes in main app: {len(current_routes)}")

        playlist_routes = [r for r in current_routes if '/api/playlists' in r]
        print(f"Playlist routes: {len(playlist_routes)}")
        for route in sorted(playlist_routes):
            print(f"  {route}")

        # Check if PlaylistRoutesState is attached to the app
        playlist_routes_state = getattr(main_app, 'playlist_routes_state', None)
        print(f"PlaylistRoutesState attached to app: {playlist_routes_state is not None}")

        if playlist_routes_state:
            print(f"PlaylistRoutesState type: {type(playlist_routes_state)}")
            print(f"PlaylistRoutesState router: {playlist_routes_state.router}")

        # Test the actual endpoints
        client = TestClient(main_app)

        print("\nTesting actual endpoints:")
        get_response = client.get("/api/playlists")
        print(f"GET /api/playlists: {get_response.status_code}")
        if get_response.status_code != 200:
            print(f"Response: {get_response.text}")

        post_response = client.post("/api/playlists", json={"title": "test"})
        print(f"POST /api/playlists: {post_response.status_code}")
        if post_response.status_code != 200:
            print(f"Response: {post_response.text}")

    def test_route_registration_step_by_step(self):
        """Test route registration step by step to find where it fails."""
        print("\n=== STEP BY STEP ROUTE REGISTRATION ===")

        # Step 1: Create clean FastAPI app
        test_app = FastAPI()
        print(f"Step 1 - Clean app routes: {len(test_app.routes)}")

        # Step 2: Create router
        from fastapi import APIRouter
        router = APIRouter(prefix="/api/playlists", tags=["playlists"])
        print(f"Step 2 - Router created with prefix: {router.prefix}")

        # Step 3: Add a simple route
        @router.get("/test")
        async def test_route():
            return {"test": "ok"}

        print(f"Step 3 - Routes in router: {len(router.routes)}")

        # Step 4: Include router in app
        test_app.include_router(router)
        print(f"Step 4 - App routes after include: {len(test_app.routes)}")

        # Step 5: Test the route
        client = TestClient(test_app)
        response = client.get("/api/playlists/test")
        print(f"Step 5 - Test route response: {response.status_code}")

        # Step 6: Now try with empty path routes
        router2 = APIRouter(prefix="/api/test", tags=["test"])

        @router2.get("")
        async def list_items():
            return {"items": []}

        @router2.get("/")
        async def list_items_slash():
            return {"items": []}

        test_app.include_router(router2)

        # Test both variants
        response1 = client.get("/api/test")
        response2 = client.get("/api/test/")

        print(f"Step 6 - GET /api/test: {response1.status_code}")
        print(f"Step 6 - GET /api/test/: {response2.status_code}")

        # This will help us understand if the issue is with empty path routes