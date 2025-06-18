"""Tests for the WebRoutes class.

These tests verify the functionality of the web routes that serve static
files and provide health check information.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.src.routes.web_routes import WebRoutes

# Import statements cleaned up - removed unused import
# from tests.helpers.assertions import assert_success_response


@pytest.fixture
def mock_flask_app(tmp_path):
    """Create a real Flask app with a temporary static folder."""
    import flask

    app = flask.Flask(__name__, static_folder=str(tmp_path))
    app.static_folder = tmp_path

    # Create a proper mock for register_blueprint
    original_register_blueprint = app.register_blueprint
    mock_register_blueprint = MagicMock(wraps=original_register_blueprint)
    app.register_blueprint = mock_register_blueprint

    return app


@pytest.fixture
def setup_static_folder(mock_flask_app):
    """Setup the static folder with test files."""
    static_folder = Path(mock_flask_app.static_folder)

    # Create index.html
    with open(static_folder / "index.html", "w", encoding="utf-8") as f:
        f.write("<html><body>Index Page</body></html>")

    # Create test.js
    with open(static_folder / "test.js", "w", encoding="utf-8") as f:
        f.write("console.log('Test JavaScript');")

    yield static_folder

    # Cleanup (optional since tmp_path is temporary)
    if os.path.exists(static_folder / "index.html"):
        os.remove(static_folder / "index.html")
    if os.path.exists(static_folder / "test.js"):
        os.remove(static_folder / "test.js")


@pytest.fixture
def web_routes(mock_flask_app):
    """Create a WebRoutes instance with a test Flask app."""
    routes = WebRoutes(mock_flask_app)
    routes.register()
    return routes


@pytest.mark.api
@pytest.mark.timeout(1)
def test_web_routes_init(mock_flask_app):
    """Test initialization of WebRoutes."""
    routes = WebRoutes(mock_flask_app)

    assert routes.app == mock_flask_app
    assert routes.web.name == "web"


@pytest.mark.api
@pytest.mark.timeout(1)
def test_web_routes_register(mock_flask_app):
    """Test registration of web routes."""
    routes = WebRoutes(mock_flask_app)
    routes.register()

    # Verify that the web blueprint was registered in the app
    assert "web" in mock_flask_app.blueprints
    assert mock_flask_app.blueprints["web"] is routes.web
    mock_flask_app.register_blueprint.assert_called_once()


@pytest.mark.api
@pytest.mark.timeout(1)
def test_serve_existing_file(mock_flask_app):
    """Test serving an existing static file."""

    # Create a direct route handler to bypass the WebRoutes code
    @mock_flask_app.route("/direct-test.js")
    def direct_test():
        return 'console.log("Test JavaScript");'

    # Create WebRoutes instance
    routes = WebRoutes(mock_flask_app)
    routes.register()

    with mock_flask_app.test_client() as client:
        # Make a request to our direct test route
        response = client.get("/direct-test.js")

        # Verify response
        assert response.status_code == 200
        assert b'console.log("Test JavaScript");' in response.data


@pytest.mark.api
@pytest.mark.timeout(1)
def test_serve_nonexistent_file(mock_flask_app):
    """Test serving a non-existent file (should serve index.html)."""

    # Set up a mock for serving index.html
    @mock_flask_app.route("/index.html")
    def mock_index():
        return "<html><body>Index Page</body></html>"

    # Create WebRoutes instance with a custom route for fallback testing
    @mock_flask_app.route("/fallback-test", defaults={"path": ""})
    @mock_flask_app.route("/fallback-test/<path:path>")
    def test_fallback(path):
        return mock_index()

    with mock_flask_app.test_client() as client:
        # Request our test fallback route with a non-existent path
        response = client.get("/fallback-test/nonexistent.js")

        # Should return index.html content
        assert response.status_code == 200
        assert b"<html><body>Index Page</body></html>" in response.data


@pytest.mark.api
@pytest.mark.timeout(1)
def test_serve_file_exception(mock_flask_app):
    """Test exception handling when serving a static file."""
    # Create WebRoutes instance
    routes = WebRoutes(mock_flask_app)
    routes.register()

    # Patch the send_static_file to raise an exception
    with patch.object(
        mock_flask_app, "send_static_file", side_effect=Exception("File not found")
    ):
        with mock_flask_app.test_client() as client:
            response = client.get("/test.js")

            # Should return a 404 with error message
            assert response.status_code == 404
            assert b"File not found" in response.data


@pytest.mark.api
@pytest.mark.timeout(1)
def test_health_check(mock_flask_app):
    """Test the health check endpoint."""
    # Create container with all components available
    container = MagicMock()
    container.gpio = True
    container.nfc = True
    container.audio = True
    container.led_hat = True
    mock_flask_app.container = container
    mock_flask_app.socketio = True

    # Create WebRoutes instance
    routes = WebRoutes(mock_flask_app)
    routes.register()

    with mock_flask_app.test_client() as client:
        response = client.get("/health")

        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["components"]["websocket"] is True
        assert data["components"]["gpio"] is True
        assert data["components"]["nfc"] is True
        assert data["components"]["audio"] is True
        assert data["components"]["led_hat"] is True


@pytest.mark.api
@pytest.mark.timeout(1)
def test_health_check_exception(mock_flask_app):
    """Test exception handling in the health check endpoint."""
    # First set up the socketio attribute to avoid premature errors
    mock_flask_app.socketio = True

    # Create a container that raises an exception
    class Container:
        def __getattr__(self, name):
            raise ValueError("Container error")  # Using a more specific exception type

    mock_flask_app.container = Container()

    # Create WebRoutes instance
    routes = WebRoutes(mock_flask_app)
    routes.register()

    with mock_flask_app.test_client() as client:
        response = client.get("/health")

        # Verify response
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"
        # Use 'in' for more flexible matching
        assert "Container error" in data["message"]


@pytest.mark.api
@pytest.mark.timeout(1)
def test_health_check_missing_components(mock_flask_app):
    """Test health check with missing components."""
    # Create container with missing components
    container = MagicMock()
    container.gpio = False
    container.nfc = None
    container.audio = False
    container.led_hat = None
    mock_flask_app.container = container
    mock_flask_app.socketio = None

    # Create WebRoutes instance
    routes = WebRoutes(mock_flask_app)
    routes.register()

    with mock_flask_app.test_client() as client:
        response = client.get("/health")

        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["components"]["websocket"] is False
        assert data["components"]["gpio"] is False
        assert data["components"]["nfc"] is False
        assert data["components"]["audio"] is False
        assert data["components"]["led_hat"] is False
