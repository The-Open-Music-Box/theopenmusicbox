# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unit tests for PlaylistCrudService.

This module contains comprehensive unit tests for the PlaylistCrudService class,
testing playlist CRUD operations and data validation.
"""

import pytest
from unittest.mock import Mock, patch

from app.src.services.playlist_crud_service import PlaylistCrudService


class TestPlaylistCrudService:
    """Test cases for PlaylistCrudService functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_config = Mock()
        self.mock_config.playlists_directory = "/test/playlists"
        
        self.mock_playlist_repository = Mock()
        
        with patch('app.src.services.playlist_crud_service.get_playlist_repository') as mock_get_repo:
            mock_get_repo.return_value = self.mock_playlist_repository
            self.service = PlaylistCrudService(self.mock_config)

    def test_initialization(self):
        """Test PlaylistCrudService initialization."""
        assert self.service.config == self.mock_config
        assert self.service.repository == self.mock_playlist_repository

    def test_get_all_playlists_success(self):
        """Test successful retrieval of all playlists."""
        mock_playlists = [
            {"id": 1, "name": "Playlist 1"},
            {"id": 2, "name": "Playlist 2"}
        ]
        self.mock_playlist_repository.get_all_playlists.return_value = mock_playlists
        
        result = self.service.get_all_playlists()
        
        assert result == mock_playlists
        self.mock_playlist_repository.get_all_playlists.assert_called_once_with(limit=50, offset=0)

    def test_get_all_playlists_empty(self):
        """Test retrieval when no playlists exist."""
        self.mock_playlist_repository.get_all_playlists.return_value = []
        
        result = self.service.get_all_playlists()
        
        assert result == []
        self.mock_playlist_repository.get_all_playlists.assert_called_once_with(limit=50, offset=0)

    def test_get_playlist_by_id_success(self):
        """Test successful retrieval of playlist by ID."""
        mock_playlist = {"id": 1, "name": "Test Playlist"}
        self.mock_playlist_repository.get_playlist_by_id.return_value = mock_playlist
        
        result = self.service.get_playlist_by_id(1)
        
        assert result == mock_playlist
        self.mock_playlist_repository.get_playlist_by_id.assert_called_once_with(1)

    def test_get_playlist_by_id_not_found(self):
        """Test retrieval of non-existent playlist."""
        self.mock_playlist_repository.get_playlist_by_id.return_value = None
        
        result = self.service.get_playlist_by_id(999)
        
        assert result is None
        self.mock_playlist_repository.get_playlist_by_id.assert_called_once_with(999)

    def test_create_playlist_success(self):
        """Test successful playlist creation."""
        playlist_data = {
            "name": "New Playlist",
            "description": "Test description"
        }
        mock_created_playlist = {"id": 1, **playlist_data}
        self.mock_playlist_repository.create_playlist.return_value = mock_created_playlist
        
        result = self.service.create_playlist(playlist_data)
        
        assert result == mock_created_playlist
        self.mock_playlist_repository.create_playlist.assert_called_once_with(playlist_data)

    def test_create_playlist_invalid_data(self):
        """Test playlist creation with invalid data."""
        invalid_data = {"description": "Missing name"}
        
        with pytest.raises(ValueError, match="Playlist name is required"):
            self.service.create_playlist(invalid_data)

    def test_create_playlist_empty_name(self):
        """Test playlist creation with empty name."""
        invalid_data = {"name": "", "description": "Empty name"}
        
        with pytest.raises(ValueError, match="Playlist name cannot be empty"):
            self.service.create_playlist(invalid_data)

    def test_update_playlist_success(self):
        """Test successful playlist update."""
        playlist_id = 1
        update_data = {"name": "Updated Playlist"}
        mock_updated_playlist = {"id": 1, "name": "Updated Playlist"}
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = {"id": 1, "name": "Old Name"}
        self.mock_playlist_repository.update_playlist.return_value = mock_updated_playlist
        
        result = self.service.update_playlist(playlist_id, update_data)
        
        assert result == mock_updated_playlist
        self.mock_playlist_repository.update_playlist.assert_called_once_with(playlist_id, update_data)

    def test_update_playlist_not_found(self):
        """Test update of non-existent playlist."""
        playlist_id = 999
        update_data = {"name": "Updated Playlist"}
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Playlist with ID 999 not found"):
            self.service.update_playlist(playlist_id, update_data)

    def test_update_playlist_invalid_name(self):
        """Test playlist update with invalid name."""
        playlist_id = 1
        update_data = {"name": ""}
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = {"id": 1, "name": "Old Name"}
        
        with pytest.raises(ValueError, match="Playlist name cannot be empty"):
            self.service.update_playlist(playlist_id, update_data)

    def test_delete_playlist_success(self):
        """Test successful playlist deletion."""
        playlist_id = 1
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = {"id": 1, "name": "Test"}
        self.mock_playlist_repository.delete_playlist.return_value = True
        
        result = self.service.delete_playlist(playlist_id)
        
        assert result is True
        self.mock_playlist_repository.delete_playlist.assert_called_once_with(playlist_id)

    def test_delete_playlist_not_found(self):
        """Test deletion of non-existent playlist."""
        playlist_id = 999
        
        self.mock_playlist_repository.get_playlist_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Playlist with ID 999 not found"):
            self.service.delete_playlist(playlist_id)

    def test_playlist_exists_true(self):
        """Test playlist existence check when playlist exists."""
        playlist_id = 1
        self.mock_playlist_repository.get_playlist_by_id.return_value = {"id": 1, "name": "Test"}
        
        result = self.service.playlist_exists(playlist_id)
        
        assert result is True
        self.mock_playlist_repository.get_playlist_by_id.assert_called_once_with(playlist_id)

    def test_playlist_exists_false(self):
        """Test playlist existence check when playlist doesn't exist."""
        playlist_id = 999
        self.mock_playlist_repository.get_playlist_by_id.return_value = None
        
        result = self.service.playlist_exists(playlist_id)
        
        assert result is False
        self.mock_playlist_repository.get_playlist_by_id.assert_called_once_with(playlist_id)

    def test_validate_playlist_data_valid(self):
        """Test validation of valid playlist data."""
        valid_data = {
            "name": "Valid Playlist",
            "description": "Valid description"
        }
        
        # Should not raise any exception
        self.service._validate_playlist_data(valid_data)

    def test_validate_playlist_data_missing_name(self):
        """Test validation with missing name."""
        invalid_data = {"description": "Missing name"}
        
        with pytest.raises(ValueError, match="Playlist name is required"):
            self.service._validate_playlist_data(invalid_data)

    def test_validate_playlist_data_empty_name(self):
        """Test validation with empty name."""
        invalid_data = {"name": "", "description": "Empty name"}
        
        with pytest.raises(ValueError, match="Playlist name cannot be empty"):
            self.service._validate_playlist_data(invalid_data)

    def test_validate_playlist_data_whitespace_name(self):
        """Test validation with whitespace-only name."""
        invalid_data = {"name": "   ", "description": "Whitespace name"}
        
        with pytest.raises(ValueError, match="Playlist name cannot be empty"):
            self.service._validate_playlist_data(invalid_data)

    def test_get_playlist_count(self):
        """Test getting total playlist count."""
        mock_playlists = [{"id": 1}, {"id": 2}, {"id": 3}]
        self.mock_playlist_repository.get_all_playlists.return_value = mock_playlists
        
        result = self.service.get_playlist_count()
        
        assert result == 3
        self.mock_playlist_repository.get_all_playlists.assert_called_once_with(limit=None, offset=0)

    def test_get_playlist_count_empty(self):
        """Test getting playlist count when no playlists exist."""
        self.mock_playlist_repository.get_all_playlists.return_value = []
        
        result = self.service.get_playlist_count()
        
        assert result == 0
        self.mock_playlist_repository.get_all_playlists.assert_called_once_with(limit=None, offset=0)
