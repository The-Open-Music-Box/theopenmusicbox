from unittest.mock import MagicMock, call, patch

import pytest
from fastapi import FastAPI

from app.src.monitoring.improved_logger import LogLevel
from app.src.routes.api_routes import APIRoutes, init_api_routes
from app.src.routes.nfc_routes import NFCRoutes
from app.src.routes.playlist_routes import PlaylistRoutes
from app.src.routes.web_routes import WebRoutes
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
from app.src.routes.youtube_routes import YouTubeRoutes
from app.src.services.nfc_service import NFCService


@pytest.fixture
def mock_app():
    """Fixture for a mocked FastAPI application."""
    return MagicMock(spec=FastAPI)


@pytest.fixture
def mock_socketio():
    """Fixture for a mocked Socket.IO instance."""
    return MagicMock()


@pytest.fixture
def mock_nfc_service():
    """Fixture for a mocked NFCService."""
    return MagicMock(spec=NFCService)


class TestAPIRoutes:
    """Tests for the APIRoutes class."""

    @patch("app.src.routes.api_routes.NFCService")
    @patch("app.src.routes.api_routes.WebRoutes")
    @patch("app.src.routes.api_routes.NFCRoutes")
    @patch("app.src.routes.api_routes.YouTubeRoutes")
    @patch("app.src.routes.api_routes.WebSocketHandlersAsync")
    @patch("app.src.routes.api_routes.PlaylistRoutes")
    def test_api_routes_initialization(
        self,
        MockPlaylistRoutes,
        MockWebSocketHandlersAsync,
        MockYouTubeRoutes,
        MockNFCRoutes,
        MockWebRoutes,
        MockNFCService,
        mock_app,
        mock_socketio,
    ):
        """Test that APIRoutes initializes all its components correctly."""
        # Arrange
        mock_nfc_instance = MockNFCService.return_value

        # Act
        api_routes = APIRoutes(app=mock_app, socketio=mock_socketio)

        # Assert
        MockNFCService.assert_called_once_with(mock_socketio)
        MockWebRoutes.assert_called_once_with(mock_app)
        MockNFCRoutes.assert_called_once_with(
            mock_app, mock_socketio, mock_nfc_instance
        )
        MockYouTubeRoutes.assert_called_once_with(mock_app, mock_socketio)
        MockWebSocketHandlersAsync.assert_called_once_with(
            mock_socketio, mock_app, mock_nfc_instance
        )
        MockPlaylistRoutes.assert_called_once_with(mock_app)

        assert api_routes.app == mock_app
        assert api_routes.socketio == mock_socketio
        assert api_routes.web_routes == MockWebRoutes.return_value
        assert api_routes.nfc_routes == MockNFCRoutes.return_value
        assert api_routes.youtube_routes == MockYouTubeRoutes.return_value
        assert api_routes.websocket_handlers == MockWebSocketHandlersAsync.return_value
        assert api_routes.playlist_routes == MockPlaylistRoutes.return_value

    @patch("app.src.routes.api_routes.logger")
    def test_api_routes_init_routes_success(self, mock_logger, mock_app, mock_socketio):
        """Test the successful initialization of all routes via init_routes."""
        # Arrange
        api_routes = APIRoutes(app=mock_app, socketio=mock_socketio)
        api_routes.web_routes = MagicMock(spec=WebRoutes)
        api_routes.nfc_routes = MagicMock(spec=NFCRoutes)
        api_routes.youtube_routes = MagicMock(spec=YouTubeRoutes)
        api_routes.websocket_handlers = MagicMock(spec=WebSocketHandlersAsync)
        api_routes.playlist_routes = MagicMock(spec=PlaylistRoutes)

        # Act
        api_routes.init_routes()

        # Assert
        api_routes.web_routes.register.assert_called_once()
        api_routes.nfc_routes.register.assert_called_once()
        api_routes.youtube_routes.register.assert_called_once()
        api_routes.websocket_handlers.register.assert_called_once()
        api_routes.playlist_routes.register.assert_called_once()

        expected_logs = [
            call(LogLevel.INFO, "Initializing routes"),
            call(LogLevel.INFO, "Routes initialized successfully"),
        ]
        mock_logger.log.assert_has_calls(expected_logs, any_order=False)

    @patch("app.src.routes.api_routes.logger")
    def test_api_routes_init_routes_failure(self, mock_logger, mock_app, mock_socketio):
        """Test route initialization failure."""
        # Arrange
        api_routes = APIRoutes(app=mock_app, socketio=mock_socketio)
        api_routes.web_routes = MagicMock(spec=WebRoutes)
        api_routes.nfc_routes = MagicMock(spec=NFCRoutes)
        # Simulate an error during youtube_routes.register()
        api_routes.youtube_routes = MagicMock(spec=YouTubeRoutes)
        api_routes.youtube_routes.register.side_effect = Exception(
            "Test registration error"
        )
        api_routes.websocket_handlers = MagicMock(spec=WebSocketHandlersAsync)
        api_routes.playlist_routes = MagicMock(spec=PlaylistRoutes)

        # Act & Assert
        with pytest.raises(Exception, match="Test registration error"):
            api_routes.init_routes()

        api_routes.web_routes.register.assert_called_once()
        api_routes.nfc_routes.register.assert_called_once()
        api_routes.youtube_routes.register.assert_called_once()
        # Ensure other registrations aren't called after failure
        api_routes.websocket_handlers.register.assert_not_called()
        api_routes.playlist_routes.register.assert_not_called()

        expected_logs = [
            call(LogLevel.INFO, "Initializing routes"),
            call(
                LogLevel.ERROR, "Failed to initialize routes: Test registration error"
            ),
        ]
        mock_logger.log.assert_has_calls(expected_logs, any_order=False)


@patch("app.src.routes.api_routes.APIRoutes")
def test_module_init_routes(MockAPIRoutes, mock_app, mock_socketio):
    """Test the module-level init_routes function."""
    # Arrange
    mock_api_routes_instance = MockAPIRoutes.return_value

    # Act
    returned_routes = init_routes(app=mock_app, socketio=mock_socketio)

    # Assert
    MockAPIRoutes.assert_called_once_with(mock_app, mock_socketio)
    mock_api_routes_instance.init_routes.assert_called_once()
    assert returned_routes == mock_api_routes_instance
