import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from rx.subject import Subject

from app.src.services.nfc_service import NFCService
from app.src.module.nfc.nfc_handler import NFCHandler


@pytest.fixture
def mock_socketio():
    """Create a mock SocketIO instance."""
    mock = AsyncMock()
    mock.emit = AsyncMock()
    return mock


@pytest.fixture
def mock_nfc_handler():
    """Create a mock NFCHandler instance."""
    mock = MagicMock(spec=NFCHandler)
    mock.tag_subject = Subject()
    mock.start_nfc_reader = AsyncMock()
    mock.is_running = MagicMock(return_value=False)  # Set to False so start_nfc_reader is called
    return mock


@pytest.fixture
def nfc_service(mock_socketio, mock_nfc_handler):
    """Create an NFCService instance with mocked dependencies."""
    service = NFCService(socketio=mock_socketio, nfc_handler=mock_nfc_handler)
    return service


@pytest.mark.asyncio
async def test_nfc_service_initialization(nfc_service, mock_socketio, mock_nfc_handler):
    """Test NFCService initialization."""
    assert nfc_service.socketio == mock_socketio
    assert nfc_service._nfc_handler == mock_nfc_handler
    assert nfc_service.waiting_for_tag is False
    assert nfc_service.current_playlist_id is None
    assert nfc_service._association_mode is False
    assert nfc_service._sid is None
    assert nfc_service._scan_status_task is None
    assert nfc_service._last_tag_info is None
    assert nfc_service._allow_override is False


@pytest.mark.asyncio
async def test_start_observe(nfc_service, mock_nfc_handler):
    """Test starting observation mode."""
    result = await nfc_service.start_observe(playlist_id="test_playlist")
    
    # Verify the NFC reader was started
    mock_nfc_handler.start_nfc_reader.assert_called_once()
    
    # Verify the service state
    assert nfc_service.waiting_for_tag is True
    assert nfc_service.current_playlist_id == "test_playlist"
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_start_listening(nfc_service, mock_nfc_handler, mock_socketio):
    """Test starting tag association mode."""
    playlist_id = "test_playlist"
    sid = "test_sid"
    
    await nfc_service.start_listening(playlist_id, sid)
    
    # Verify the NFC reader was started (since is_running returns False)
    mock_nfc_handler.start_nfc_reader.assert_called_once()
    
    # Verify the service state
    assert nfc_service.current_playlist_id == playlist_id
    assert nfc_service._sid == sid
    assert nfc_service._association_mode is True
    assert nfc_service.waiting_for_tag is True
    
    # Verify the socket event was emitted
    mock_socketio.emit.assert_called_with(
        'nfc_status',
        {
            'type': 'nfc_status',
            'status': 'listening',
            'message': 'Listening for NFC tag...',
            'playlist_id': playlist_id
        },
        room=sid
    )


@pytest.mark.asyncio
async def test_stop_listening(nfc_service, mock_socketio):
    """Test stopping tag association mode."""
    # Setup initial state
    nfc_service._association_mode = True
    nfc_service.waiting_for_tag = True
    nfc_service._sid = "test_sid"
    
    await nfc_service.stop_listening()
    
    # Verify the service state
    assert nfc_service._association_mode is False
    assert nfc_service.waiting_for_tag is False
    assert nfc_service._sid is None
    
    # Verify the socket event was emitted
    mock_socketio.emit.assert_called_with(
        'nfc_status',
        {
            'type': 'nfc_status',
            'status': 'stopped',
            'message': 'NFC tag listening stopped'
        },
        room="test_sid"
    )


@pytest.mark.asyncio
async def test_handle_tag_detected_playback_mode(nfc_service):
    """Test handling a tag in playback mode."""
    # Setup initial state - not in association mode
    nfc_service._association_mode = False
    
    # Mock the _handle_playback_tag method
    nfc_service._handle_playback_tag = AsyncMock(return_value=True)
    
    # Call the method
    tag_id = "04:A2:B3:C4"
    result = await nfc_service.handle_tag_detected(tag_id)
    
    # Verify _handle_playback_tag was called
    nfc_service._handle_playback_tag.assert_called_once_with(tag_id, None)
    assert result is True
    assert nfc_service._last_tag_info is not None
    assert nfc_service._last_tag_info["tag_id"] == tag_id


@pytest.mark.asyncio
async def test_handle_tag_detected_association_mode(nfc_service, mock_socketio):
    """Test handling a tag in association mode."""
    # Setup initial state - in association mode
    nfc_service._association_mode = True
    nfc_service.waiting_for_tag = True
    nfc_service._sid = "test_sid"
    nfc_service.current_playlist_id = "test_playlist"
    
    # Setup playlists
    nfc_service._playlists = [
        {"id": "test_playlist", "title": "Test Playlist", "nfc_tag": None}
    ]
    
    # Mock the playlist service and config_singleton
    with patch('app.src.services.playlist_service.PlaylistService') as MockPlaylistService, \
         patch('app.src.config.config_singleton') as mock_config:
        mock_playlist_service = MockPlaylistService.return_value
        mock_playlist_service.associate_nfc_tag.return_value = True
        
        # Call the method
        tag_id = "04:A2:B3:C4"
        result = await nfc_service.handle_tag_detected(tag_id)
        
        # Verify the playlist service was called
        mock_playlist_service.associate_nfc_tag.assert_called_once_with("test_playlist", tag_id)
        
        # Verify the service state
        assert nfc_service._association_mode is False
        assert nfc_service.waiting_for_tag is False
        assert result is True
        
        # Verify socket events were emitted
        assert mock_socketio.emit.call_count >= 2  # At least two events should be emitted


@pytest.mark.asyncio
async def test_handle_playback_tag(nfc_service):
    """Test handling a tag in playback mode."""
    # Setup a subscriber to the playback subject
    events = []
    nfc_service._playback_subject.subscribe(lambda x: events.append(x))
    
    # Call the method
    tag_id = "04:A2:B3:C4"
    tag_data = {"some": "data"}
    result = await nfc_service._handle_playback_tag(tag_id, tag_data)
    
    # Verify the result
    assert result is True
    assert len(events) == 1
    assert events[0][0] == tag_id
    assert events[0][1] == tag_data


@pytest.mark.asyncio
async def test_playback_subject_property(nfc_service):
    """Test the playback_subject property."""
    subject = nfc_service.playback_subject
    
    # Verify the subject is accessible
    assert subject is not None
    assert subject == nfc_service._playback_subject
    
    # Test that events are emitted to the subject
    events = []
    subject.subscribe(lambda x: events.append(x))
    
    # Emit an event via _handle_playback_tag
    tag_id = "04:A2:B3:C4"
    await nfc_service._handle_playback_tag(tag_id, None)
    
    # Verify an event was emitted to the subject
    assert len(events) == 1
    assert events[0][0] == tag_id
