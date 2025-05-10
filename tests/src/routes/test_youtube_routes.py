"""
Tests for the YouTubeRoutes class.

These tests verify the functionality of the YouTube routes that handle
YouTube video downloads.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, Mock
from flask import Flask, current_app

from app.src.routes.youtube_routes import YouTubeRoutes
from tests.helpers.assertions import assert_success_response, assert_error_response
from tests.helpers.utils import MockHelpers


@pytest.fixture
def mock_flask_app():
    """Create a Flask app for testing."""
    app = Flask('test_app')
    
    # Set up a proper mock for register_blueprint using Mock
    original_register_blueprint = app.register_blueprint
    mock_register_blueprint = Mock(wraps=original_register_blueprint)
    app.register_blueprint = mock_register_blueprint
    
    # Add test configuration
    app.config.update({
        'TESTING': True,
        'DEBUG': True
    })
    
    return app


@pytest.fixture
def mock_socketio():
    """Create a mock Socket.IO server."""
    return MagicMock()


@pytest.fixture
def youtube_routes(mock_flask_app, mock_socketio):
    """Create a YouTubeRoutes instance with mocks."""
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    routes.register()
    return routes


@pytest.mark.api
def test_youtube_routes_init(mock_flask_app, mock_socketio):
    """Test initialization of YouTubeRoutes."""
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    
    assert routes.app == mock_flask_app
    assert routes.socketio == mock_socketio
    assert routes.api.name == 'youtube_api'


@pytest.mark.api
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_youtube_routes_register(mock_flask_app, mock_socketio):
    """Test registration of YouTube routes."""
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    routes.register()
    
    # Verify that register_blueprint was called with the api blueprint
    mock_flask_app.register_blueprint.assert_called_once()
    # Check the arguments of the call
    args, kwargs = mock_flask_app.register_blueprint.call_args
    
    assert args[0] == routes.api
    assert kwargs.get('url_prefix') == '/api/youtube'


@pytest.mark.api
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_download_youtube_not_json(mock_flask_app, mock_socketio):
    """Test download_youtube with non-JSON request."""
    # Create YouTubeRoutes instance with the fixture mocks
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    routes.register()
    
    # Create a test client for the Flask app
    client = mock_flask_app.test_client()
    
    # Use app context to avoid "Working outside of application context" errors
    with mock_flask_app.app_context():
        # Make a request with invalid content type
        response = client.post(
            '/api/youtube/youtube/download',
            data='not a json payload',
            content_type='text/plain'
        )
        
        # Verify the response
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data.get('error') == 'Content-Type must be application/json'


@pytest.mark.api
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_download_youtube_no_url(mock_flask_app, mock_socketio):
    """Test download_youtube with missing URL."""
    # Create YouTubeRoutes instance with the fixture mocks
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    routes.register()
    
    # Create a test client for the Flask app
    client = mock_flask_app.test_client()
    
    # Use app context to avoid "Working outside of application context" errors
    with mock_flask_app.app_context():
        # Make a request with empty JSON data (missing URL)
        response = client.post(
            '/api/youtube/youtube/download',
            json={},  # Empty JSON with no URL
            content_type='application/json'
        )
        
        # Verify the response
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data.get('error') == 'Invalid YouTube URL'


@pytest.mark.api
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_download_youtube_success(mock_flask_app, mock_socketio):
    """Test successful YouTube download."""
    # Create YouTubeRoutes instance
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    routes.register()
    
    # Create a test client for the Flask app
    client = mock_flask_app.test_client()
    
    # Define the expected successful response
    expected_response = {
        'status': 'success',
        'playlist_id': 'playlist_123',
        'data': {
            'title': 'Test Video',
            'id': 'test123',
            'folder': 'test_video',
            'chapters': [
                {
                    'title': 'Chapter 1',
                    'start_time': 0,
                    'end_time': 60,
                    'filename': 'chapter1.mp3'
                },
                {
                    'title': 'Chapter 2',
                    'start_time': 60,
                    'end_time': 120,
                    'filename': 'chapter2.mp3'
                }
            ]
        }
    }
    
    # Use app context and patch service
    with patch('app.src.routes.youtube_routes.YouTubeService') as mock_service_class, \
         mock_flask_app.app_context():
        
        # Configure mock service to return success
        mock_service_instance = MagicMock()
        mock_service_instance.process_download.return_value = expected_response
        mock_service_class.return_value = mock_service_instance
        
        # Configure the app directly rather than patching current_app
        mock_flask_app.container = MagicMock()
        mock_flask_app.container.config = MagicMock()
        
        # Make a request with a valid YouTube URL
        response = client.post(
            '/api/youtube/youtube/download',
            json={'url': 'https://www.youtube.com/watch?v=test123'},
            content_type='application/json'
        )
        
        # Verify that the service was called correctly
        mock_service_class.assert_called_once()
        mock_service_instance.process_download.assert_called_once_with(
            'https://www.youtube.com/watch?v=test123'
        )
        
        # Verify the response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data == expected_response
        assert response_data['playlist_id'] == 'playlist_123'
        assert response_data['data']['title'] == 'Test Video'
        assert response_data['data']['id'] == 'test123'


@pytest.mark.api
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_download_youtube_error(mock_flask_app, mock_socketio):
    """Test YouTube download with error."""
    # Create YouTubeRoutes instance with the fixture mocks
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    routes.register()
    
    # Create a test client for the Flask app
    client = mock_flask_app.test_client()
    
    # Use app context and patch service
    with patch('app.src.routes.youtube_routes.YouTubeService') as mock_service_class, \
         mock_flask_app.app_context():
        
        # Configure mock service to raise an exception
        mock_service_instance = MagicMock()
        mock_service_instance.process_download.side_effect = Exception('Download failed')
        mock_service_class.return_value = mock_service_instance
        
        # Configure app container instead of patching current_app
        mock_flask_app.container = MagicMock()
        mock_flask_app.container.config = MagicMock()
        
        # Make a request with an invalid YouTube URL
        response = client.post(
            '/api/youtube/youtube/download',
            json={'url': 'https://www.youtube.com/watch?v=invalid'},
            content_type='application/json'
        )
        
        # Verify that the service was called correctly
        mock_service_class.assert_called_once()
        mock_service_instance.process_download.assert_called_once_with(
            'https://www.youtube.com/watch?v=invalid'
        )
        
        # Verify the response
        assert response.status_code == 500
        response_data = json.loads(response.data)
        assert response_data.get('error') == 'Download failed'


@pytest.mark.api
@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_download_youtube_with_real_service_mock(mock_flask_app, mock_socketio, tmp_path):
    """Test download_youtube with a more realistic service mock.
    
    This test uses real implementation classes with mocked dependencies
    to test the integration between the route and service without making actual
    YouTube API calls.
    """
    # Create YouTubeRoutes instance
    routes = YouTubeRoutes(mock_flask_app, mock_socketio)
    routes.register()
    
    # Create test client
    client = mock_flask_app.test_client()
    
    # Setup config with mock values
    class MockConfig:
        def __init__(self):
            self.upload_folder = str(tmp_path / "uploads")
            self.playlists_file = str(tmp_path / "playlists.json")
    
    # Create mock playlist service
    class MockPlaylistService:
        def __init__(self, playlists_file):
            self.playlists_file = playlists_file
        
        def add_playlist(self, playlist_data):
            return "new_playlist_id_123"
    
    # Create mock YouTube downloader
    class MockYouTubeDownloader:
        def __init__(self, upload_folder, progress_callback=None):
            self.upload_folder = upload_folder
            self.progress_callback = progress_callback
        
        def download(self, url):
            # Simulate successful download
            return {
                'title': 'Test Downloaded Video',
                'id': url.split('v=')[1],
                'folder': 'test_downloaded_video',
                'chapters': [{
                    'title': 'Full Video',
                    'start_time': 0,
                    'end_time': 180,
                    'filename': 'Full Video.mp3'
                }]
            }
    
    # Patch necessary components and set up app context
    with patch('app.src.services.youtube.service.PlaylistService', MockPlaylistService), \
         patch('app.src.services.youtube.service.YouTubeDownloader', MockYouTubeDownloader), \
         mock_flask_app.app_context():
        
        # Configure the app directly rather than patching current_app
        mock_flask_app.container = MagicMock()
        mock_flask_app.container.config = MockConfig()
        
        # Make a request with a valid YouTube URL
        response = client.post(
            '/api/youtube/youtube/download',
            json={'url': 'https://www.youtube.com/watch?v=test123'},
            content_type='application/json'
        )
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert response_data['playlist_id'] == 'new_playlist_id_123'
        assert response_data['data']['title'] == 'Test Downloaded Video'
        assert response_data['data']['id'] == 'test123'
