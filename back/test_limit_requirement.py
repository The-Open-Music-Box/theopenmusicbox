#!/usr/bin/env python3
"""
Test script to verify that the limit parameter is required for the playlists endpoint.
"""

import requests
import json

BASE_URL = "http://localhost:5005"

def test_without_limit():
    """Test the playlists endpoint without providing a limit parameter."""
    print("Testing /api/playlists/ without limit parameter...")
    try:
        response = requests.get(f"{BASE_URL}/api/playlists/", timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 422:
            print("✅ Good! Server returned 422 (Unprocessable Entity) - limit parameter is required")
            print(f"Error details: {json.dumps(response.json(), indent=2)}")
        elif response.status_code == 200:
            print("❌ Bad! Server returned 200 - limit parameter should be required")
            data = response.json()
            if 'data' in data and 'limit' in data['data']:
                print(f"Used limit: {data['data']['limit']}")
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
    except Exception as e:
        print(f"Error: {e}")

def test_with_limit():
    """Test the playlists endpoint with a valid limit parameter."""
    print("\nTesting /api/playlists/ with limit=100...")
    try:
        response = requests.get(f"{BASE_URL}/api/playlists/", params={"limit": 100}, timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✅ Good! Server returned 200 with limit parameter")
            data = response.json()
            if 'data' in data and 'limit' in data['data']:
                print(f"Used limit: {data['data']['limit']}")
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_without_limit()
    test_with_limit()