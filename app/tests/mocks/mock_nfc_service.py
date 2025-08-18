# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Mock NFC service for testing.

This module provides a mock implementation of the NFC service
for testing purposes without requiring actual NFC hardware.
"""

from typing import Dict, List, Optional


class MockNfcService:
    """Mock NFC service implementation for testing.
    
    Simulates NFC tag reading and writing without actual hardware dependencies,
    enabling comprehensive testing of NFC-related functionality.
    """

    def __init__(self):
        """Initialize the mock NFC service."""
        self._is_available = True
        self._is_listening = False
        self._simulated_tags: Dict[str, Dict] = {}
        self._last_read_tag: Optional[Dict] = None

    def is_available(self) -> bool:
        """Check if the NFC service is available.
        
        Returns:
            True if NFC service is available, False otherwise
        """
        return self._is_available

    def start_listening(self) -> bool:
        """Start listening for NFC tags.
        
        Returns:
            True if listening started successfully, False otherwise
        """
        if not self._is_available:
            return False
        self._is_listening = True
        return True

    def stop_listening(self) -> bool:
        """Stop listening for NFC tags.
        
        Returns:
            True if listening stopped successfully, False otherwise
        """
        self._is_listening = False
        return True

    def is_listening(self) -> bool:
        """Check if the service is currently listening for tags.
        
        Returns:
            True if listening, False otherwise
        """
        return self._is_listening

    def read_tag(self) -> Optional[Dict]:
        """Read data from an NFC tag.
        
        Returns:
            Dictionary containing tag data, or None if no tag available
        """
        if not self._is_available or not self._is_listening:
            return None
        return self._last_read_tag

    def write_tag(self, tag_id: str, data: Dict) -> bool:
        """Write data to an NFC tag.
        
        Args:
            tag_id: Unique identifier for the tag
            data: Data to write to the tag
            
        Returns:
            True if write was successful, False otherwise
        """
        if not self._is_available:
            return False
        
        self._simulated_tags[tag_id] = data.copy()
        return True

    def get_tag_info(self, tag_id: str) -> Optional[Dict]:
        """Get information about a specific tag.
        
        Args:
            tag_id: Unique identifier for the tag
            
        Returns:
            Dictionary containing tag information, or None if not found
        """
        return self._simulated_tags.get(tag_id)

    # Mock-specific methods for testing
    def set_availability(self, available: bool):
        """Set the availability state for testing.
        
        Args:
            available: Whether the service should be available
        """
        self._is_available = available

    def simulate_tag_detection(self, tag_id: str, data: Optional[Dict] = None):
        """Simulate detection of an NFC tag.
        
        Args:
            tag_id: Unique identifier for the simulated tag
            data: Optional data to associate with the tag
        """
        tag_data = {
            "tag_id": tag_id,
            "timestamp": "2025-01-27T12:00:00Z"
        }
        
        if data:
            tag_data.update(data)
        
        self._last_read_tag = tag_data
        
        # Store in simulated tags if not already present
        if tag_id not in self._simulated_tags:
            self._simulated_tags[tag_id] = tag_data

    def simulate_playlist_tag(self, tag_id: str, playlist_id: int):
        """Simulate detection of a playlist-associated tag.
        
        Args:
            tag_id: Unique identifier for the tag
            playlist_id: ID of the associated playlist
        """
        self.simulate_tag_detection(tag_id, {
            "playlist_id": playlist_id,
            "type": "playlist"
        })

    def get_simulated_tags(self) -> Dict[str, Dict]:
        """Get all simulated tags.
        
        Returns:
            Dictionary of tag_id -> tag_data mappings
        """
        return self._simulated_tags.copy()

    def clear_simulated_tags(self):
        """Clear all simulated tags."""
        self._simulated_tags.clear()
        self._last_read_tag = None

    def remove_simulated_tag(self, tag_id: str) -> bool:
        """Remove a simulated tag.
        
        Args:
            tag_id: Unique identifier for the tag to remove
            
        Returns:
            True if tag was removed, False if not found
        """
        if tag_id in self._simulated_tags:
            del self._simulated_tags[tag_id]
            if self._last_read_tag and self._last_read_tag.get("tag_id") == tag_id:
                self._last_read_tag = None
            return True
        return False

    def get_tag_count(self) -> int:
        """Get the number of simulated tags.
        
        Returns:
            Number of simulated tags
        """
        return len(self._simulated_tags)

    def reset(self):
        """Reset the mock NFC service to initial state."""
        self._is_available = True
        self._is_listening = False
        self._simulated_tags.clear()
        self._last_read_tag = None
