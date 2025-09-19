"""Audio domain protocols for dependency injection and testing."""

from .audio_backend_protocol import AudioBackendProtocol
from .audio_engine_protocol import AudioEngineProtocol
from .playlist_manager_protocol import PlaylistManagerProtocol
from .event_bus_protocol import EventBusProtocol
from .state_manager_protocol import StateManagerProtocol

__all__ = [
    "AudioBackendProtocol",
    "AudioEngineProtocol",
    "PlaylistManagerProtocol",
    "EventBusProtocol",
    "StateManagerProtocol",
]
