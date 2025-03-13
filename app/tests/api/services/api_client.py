# app/tests/api/services/api_client.py

import requests
from typing import Dict, Any, Optional, List
import json
import logging

logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with the Music Box API."""

    def __init__(self, base_url: str = "http://tmbdev.local:5005"):
        # Ensure the base URL has the correct format
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"
        self.base_url = base_url.rstrip('/')
        logger.info(f"APIClient initialized with base URL: {self.base_url}")

    def _make_request(self, method: str, endpoint: str,
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Making {method} request to {url}")
        if data:
            logger.info(f"Request data: {json.dumps(data)}")
        if params:
            logger.info(f"Request params: {json.dumps(params)}")

        try:
            logger.debug(f"Sending request to {url}")
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=5  # Add timeout to prevent hanging
            )
            logger.info(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response content: {response.content}")

            response.raise_for_status()

            # Handle empty responses
            if not response.content:
                return {
                    'status': 'success',
                    'message': f'{method} request to {endpoint} completed successfully',
                    'code': response.status_code
                }

            # Try to parse JSON response
            try:
                result = response.json()
                # If result is a list, wrap it in a dict for consistent handling
                if isinstance(result, list):
                    return {'data': result, 'count': len(result)}
                return result
            except json.JSONDecodeError:
                # If response is not JSON, return the text content
                return {
                    'status': 'success',
                    'message': response.text,
                    'code': response.status_code
                }

        except requests.exceptions.Timeout:
            error_msg = f"Request to {url} timed out after 5 seconds"
            logger.error(error_msg)
            return {'error': error_msg, 'status': 'error'}

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to {url}. Please check if the server is running. Error: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg, 'status': 'error'}

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg, 'status': 'error'}

        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg, 'status': 'error'}

    # Playlist Management
    def get_playlists(self) -> Dict[str, Any]:
        """Get all available playlists."""
        logger.info("Fetching playlists")
        response = self._make_request('GET', '/api/nfc_mapping')

        # Si nous avons une erreur, la retourner
        if 'error' in response:
            return response

        # La réponse devrait être une liste de mappings NFC
        if isinstance(response, dict) and 'data' in response:
            mappings = response['data']
            return {
                'status': 'success',
                'data': mappings,
                'count': len(mappings)
            }

        return {'error': 'Unexpected response format', 'status': 'error'}

    def play_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Start playing a playlist."""
        logger.info(f"Playing playlist {playlist_id}")
        return self._make_request('POST', f'/api/playlist/{playlist_id}/play', {
            'playlist_id': playlist_id
        })

    def pause_playback(self) -> Dict[str, Any]:
        """Pause the current playback."""
        logger.info("Pausing playback")
        return self._make_request('POST', '/api/playlist/control/pause')  # Correct route from PlaylistRoutes

    def resume_playback(self) -> Dict[str, Any]:
        """Resume the current playback."""
        logger.info("Resuming playback")
        return self._make_request('POST', '/api/playlist/control/play')  # Correct route from PlaylistRoutes

    def stop_playback(self) -> Dict[str, Any]:
        """Stop the current playback."""
        logger.info("Stopping playback")
        return self._make_request('POST', '/api/playlist/control/stop')  # Correct route from PlaylistRoutes

    def next_track(self) -> Dict[str, Any]:
        """Skip to the next track."""
        logger.info("Skipping to next track")
        return self._make_request('POST', '/api/playlist/control/next')  # Correct route from PlaylistRoutes

    def previous_track(self) -> Dict[str, Any]:
        """Go back to the previous track."""
        logger.info("Going to previous track")
        return self._make_request('POST', '/api/playlist/control/previous')  # Correct route from PlaylistRoutes

    # Volume Control
    def set_volume(self, volume: int) -> Dict[str, Any]:
        """Set the playback volume (0-100)."""
        logger.info(f"Setting volume to {volume}")
        return self._make_request('POST', '/api/player/volume', {'level': volume})  # Added 'level' parameter

    def get_volume(self) -> Dict[str, Any]:
        """Get the current volume level."""
        logger.info("Getting current volume")
        return self._make_request('GET', '/api/player/volume')

    # System Information
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        logger.info("Getting system information")
        return self._make_request('GET', '/health')  # Changed to health check endpoint

    def get_playback_status(self) -> Dict[str, Any]:
        """Get current playback status."""
        return self._make_request('GET', '/api/player/status')  # Changed to match player status endpoint