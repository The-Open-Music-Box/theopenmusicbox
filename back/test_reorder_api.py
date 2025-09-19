#!/usr/bin/env python3
"""
Test the playlist reorder API endpoint.
"""

import asyncio
import aiohttp
import json
import sys


async def test_reorder_api():
    """Test the reorder API endpoint."""
    base_url = "http://127.0.0.1:5005/api/playlists"

    async with aiohttp.ClientSession() as session:
        try:
            # 1. Create a test playlist
            print("1. Creating test playlist...")
            playlist_data = {
                "title": "Test Reorder API",
                "description": "Testing reorder endpoint"
            }
            async with session.post(base_url, json=playlist_data) as resp:
                if resp.status not in [200, 201]:
                    print(f"   ❌ Failed to create playlist: {resp.status}")
                    return
                result = await resp.json()
                playlist_id = result["data"]["id"]
                print(f"   ✅ Created playlist: {playlist_id}")

            # 2. Get the playlist to confirm it exists
            print("2. Getting playlist...")
            async with session.get(f"{base_url}/{playlist_id}") as resp:
                if resp.status != 200:
                    print(f"   ❌ Failed to get playlist: {resp.status}")
                else:
                    print(f"   ✅ Playlist retrieved successfully")

            # 3. Test reorder endpoint (will fail for empty playlist but shouldn't give 500)
            print("3. Testing reorder endpoint...")
            reorder_data = {
                "track_order": []  # Empty for now
            }
            async with session.post(f"{base_url}/{playlist_id}/reorder", json=reorder_data) as resp:
                print(f"   Response status: {resp.status}")
                result = await resp.json()

                if resp.status == 500:
                    print(f"   ❌ Got 500 error: {result}")
                    print("   The update_track_numbers issue may not be fully resolved")
                elif resp.status == 400:
                    print(f"   ✅ Got expected 400 for empty track_order")
                elif resp.status == 200:
                    print(f"   ✅ Reorder succeeded (unexpected for empty playlist)")
                else:
                    print(f"   ℹ️  Got status {resp.status}: {result}")

            # 4. Clean up
            print("4. Deleting test playlist...")
            async with session.delete(f"{base_url}/{playlist_id}", json={}) as resp:
                if resp.status in [200, 204]:
                    print(f"   ✅ Deleted test playlist")
                else:
                    print(f"   ⚠️  Failed to delete: {resp.status}")

            print("\n✅ API test completed!")

        except aiohttp.ClientConnectorError:
            print("❌ Could not connect to server. Make sure it's running on port 5005")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_reorder_api())