"""Simple tests for UploadRoutes functionality."""

import pytest
from unittest.mock import Mock, patch

def test_upload_routes_import():
    """Test that UploadRoutes can be imported and initialized."""
    # Mock the missing ErrorHandler
    with patch('app.src.routes.upload_routes.ErrorHandler', Mock()):
        from app.src.routes.upload_routes import UploadRoutes

        mock_app = Mock()
        mock_socketio = Mock()

        routes = UploadRoutes(mock_app, mock_socketio)

        assert routes.app == mock_app
        assert routes.socketio == mock_socketio
        assert hasattr(routes, 'router')

def test_upload_routes_registration():
    """Test route registration functionality."""
    with patch('app.src.routes.upload_routes.ErrorHandler', Mock()):
        from app.src.routes.upload_routes import UploadRoutes

        mock_app = Mock()
        mock_socketio = Mock()

        routes = UploadRoutes(mock_app, mock_socketio)
        routes.register_with_app()

        # Verify registration was called
        mock_app.include_router.assert_called_once()