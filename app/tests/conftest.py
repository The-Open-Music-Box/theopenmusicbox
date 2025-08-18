# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Test configuration and fixtures for pytest.

This module provides common test fixtures and configuration for all tests
in the TheOpenMusicBox backend test suite.
"""

import pytest
from unittest.mock import Mock

from app.tests.mocks.mock_audio_service import MockAudioService
from app.tests.mocks.mock_controls_manager import MockControlsManager
from app.tests.mocks.mock_nfc_service import MockNfcService


@pytest.fixture
def mock_config():
    """Provide a mock configuration object for testing."""
    config = Mock()
    config.playlists_directory = "/test/playlists"
    config.volume_default = 50
    config.volume_min = 0
    config.volume_max = 100
    config.volume_step = 5
    config.debounce_time = 0.2
    return config


@pytest.fixture
def mock_audio_service():
    """Provide a mock audio service for testing."""
    service = MockAudioService()
    service.reset()
    return service


@pytest.fixture
def mock_controls_manager():
    """Provide a mock controls manager for testing."""
    manager = MockControlsManager()
    manager.reset()
    return manager


@pytest.fixture
def mock_nfc_service():
    """Provide a mock NFC service for testing."""
    service = MockNfcService()
    service.reset()
    return service


@pytest.fixture
def mock_playlist_repository():
    """Provide a mock playlist repository for testing."""
    repo = Mock()
    repo.get_all.return_value = []
    repo.get_by_id.return_value = None
    repo.create.return_value = None
    repo.update.return_value = None
    repo.delete.return_value = False
    return repo


@pytest.fixture
def mock_track_repository():
    """Provide a mock track repository for testing."""
    repo = Mock()
    repo.get_by_playlist_id.return_value = []
    repo.create.return_value = None
    repo.update.return_value = None
    repo.delete.return_value = False
    repo.update_order.return_value = False
    return repo


@pytest.fixture
def sample_playlist_data():
    """Provide sample playlist data for testing."""
    return {
        "id": 1,
        "name": "Test Playlist",
        "description": "A test playlist",
        "tracks": [
            {"id": 1, "order": 1, "filename": "track1.mp3", "title": "Track 1"},
            {"id": 2, "order": 2, "filename": "track2.mp3", "title": "Track 2"},
            {"id": 3, "order": 3, "filename": "track3.mp3", "title": "Track 3"}
        ]
    }


@pytest.fixture
def sample_track_data():
    """Provide sample track data for testing."""
    return [
        {"id": 1, "order": 1, "filename": "track1.mp3", "title": "Track 1", "duration": 180},
        {"id": 2, "order": 2, "filename": "track2.mp3", "title": "Track 2", "duration": 210},
        {"id": 3, "order": 3, "filename": "track3.mp3", "title": "Track 3", "duration": 195}
    ]


@pytest.fixture(autouse=True)
def reset_mocks():
    """Automatically reset all mock services after each test."""
    yield
    # This runs after each test to ensure clean state
