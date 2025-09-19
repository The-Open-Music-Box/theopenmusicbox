# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Route Fix Verification Test

This test verifies that the route registration fix works correctly.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestRouteFixVerification:
    """Verify the route registration fix."""

    def test_playlist_routes_after_fix(self):
        """Test that both GET and POST /api/playlists work after the fix."""
        print("\n=== ROUTE FIX VERIFICATION ===")

        # Use TestClient with lifespan to ensure routes are registered
        with TestClient(app) as client:
            # Check routes after lifespan startup
            app_routes = []
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    for method in route.methods:
                        if method in ['GET', 'POST', 'PUT', 'DELETE']:
                            app_routes.append(f'{method} {route.path}')

            print(f"Total routes registered: {len(app_routes)}")

            playlist_routes = [r for r in app_routes if '/api/playlists' in r and not '{' in r]
            print(f"Base playlist routes:")
            for route in sorted(playlist_routes):
                print(f"  {route}")

            # Test the fixed routes
            print("\n=== TESTING FIXED ENDPOINTS ===")

            # GET /api/playlists (should work)
            get_response = client.get("/api/playlists")
            print(f"GET /api/playlists: {get_response.status_code}")

            # GET /api/playlists/ (should also work)
            get_slash_response = client.get("/api/playlists/")
            print(f"GET /api/playlists/: {get_slash_response.status_code}")

            # POST /api/playlists (SHOULD NOW WORK!)
            post_response = client.post("/api/playlists", json={"title": "Test Playlist"})
            print(f"POST /api/playlists: {post_response.status_code}")
            if post_response.status_code != 200:
                print(f"POST response: {post_response.text}")

            # POST /api/playlists/ (should also work)
            post_slash_response = client.post("/api/playlists/", json={"title": "Test Playlist 2"})
            print(f"POST /api/playlists/: {post_slash_response.status_code}")
            if post_slash_response.status_code != 200:
                print(f"POST/ response: {post_slash_response.text}")

            # Verify both work
            assert get_response.status_code == 200, f"GET /api/playlists failed: {get_response.status_code}"
            assert get_slash_response.status_code == 200, f"GET /api/playlists/ failed: {get_slash_response.status_code}"

            # The main fix: POST should now work!
            assert post_response.status_code in [200, 201], f"POST /api/playlists failed: {post_response.status_code}"
            assert post_slash_response.status_code in [200, 201], f"POST /api/playlists/ failed: {post_slash_response.status_code}"

            print("\n✅ ALL ROUTES WORKING CORRECTLY!")

    def test_upload_routes_exist(self):
        """Test that upload routes are also properly registered."""
        print("\n=== UPLOAD ROUTES VERIFICATION ===")

        with TestClient(app) as client:
            # Check for upload-related routes
            app_routes = []
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    for method in route.methods:
                        if method in ['GET', 'POST', 'PUT', 'DELETE']:
                            app_routes.append(f'{method} {route.path}')

            upload_routes = [r for r in app_routes if 'upload' in r.lower()]
            print(f"Upload-related routes:")
            for route in sorted(upload_routes):
                print(f"  {route}")

            # Test an upload session initialization
            test_playlist_id = "test-playlist-id"
            upload_session_response = client.post(
                f"/api/playlists/{test_playlist_id}/uploads/session",
                json={
                    "filename": "test.mp3",
                    "file_size": 1024000,
                    "chunk_size": 1024
                }
            )
            print(f"Upload session init: {upload_session_response.status_code}")

            # Should not be 404 (route not found)
            assert upload_session_response.status_code != 404, "Upload session route not found"

            print("✅ Upload routes properly registered!")

    def test_route_consistency(self):
        """Test that all major API routes are consistently available."""
        print("\n=== ROUTE CONSISTENCY CHECK ===")

        with TestClient(app) as client:
            # Test major endpoints for consistency
            test_cases = [
                ("GET", "/api/playlists", "List playlists"),
                ("GET", "/api/player/status", "Player status"),
                ("GET", "/api/system/info", "System info"),
                ("GET", "/api/nfc/status", "NFC status"),
            ]

            all_working = True
            for method, path, description in test_cases:
                try:
                    if method == "GET":
                        response = client.get(path)
                    elif method == "POST":
                        response = client.post(path, json={})

                    print(f"{method} {path} ({description}): {response.status_code}")

                    # Should not be 404 (not found) or 405 (method not allowed)
                    if response.status_code in [404, 405]:
                        all_working = False
                        print(f"  ❌ {description} not properly registered")
                    else:
                        print(f"  ✅ {description} available")

                except Exception as e:
                    print(f"  ❌ Error testing {description}: {e}")
                    all_working = False

            assert all_working, "Some major routes are not properly registered"
            print("\n✅ All major routes consistently available!")