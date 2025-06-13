"""
Assertion helpers for TheOpenMusicBox tests.

This module provides standardized assertion functions to ensure consistent
test validation across the test suite.
"""


def assert_success_response(response, message=None):
    """
    Assert that an API response indicates success.

    Args:
        response: The FastAPI TestClient response object
        message: Optional expected message in the response
    """
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    if message:
        assert response.json().get('message') == message


def assert_error_response(response, status_code, error_message=None):
    """
    Assert that an API response indicates an error.

    Args:
        response: The FastAPI TestClient response object
        status_code: Expected HTTP status code
        error_message: Optional expected error message substring
    """
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
    if error_message:
        assert error_message in response.json().get('error', '')


def assert_nfc_status(response, expected_status):
    """
    Assert that an NFC status response contains the expected status.

    Args:
        response: The FastAPI TestClient response object
        expected_status: Expected status string (e.g., 'listening', 'stopped')
    """
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json().get('status') == expected_status


def assert_playback_status(response, expected_status):
    """
    Assert that a playback status response contains the expected status.

    Args:
        response: The FastAPI TestClient response object
        expected_status: Expected status string (e.g., 'playing', 'paused', 'stopped')
    """
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json().get('status') == expected_status
