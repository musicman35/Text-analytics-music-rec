"""
Test Spotify API Authentication
"""

import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()

print("="*60)
print("SPOTIFY API AUTHENTICATION TEST")
print("="*60)

# Get credentials
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

print(f"\nClient ID: {client_id[:10]}...{client_id[-10:] if client_id and len(client_id) > 20 else 'MISSING'}")
print(f"Client Secret: {client_secret[:10] if client_secret else 'MISSING'}...{client_secret[-10:] if client_secret and len(client_secret) > 20 else 'MISSING'}")

# Check if credentials exist
if not client_id or client_id.startswith("your_"):
    print("\n❌ SPOTIFY_CLIENT_ID is not set or is using template value")
    print("Please update your .env file with your actual Spotify Client ID")
    exit(1)

if not client_secret or client_secret.startswith("your_"):
    print("\n❌ SPOTIFY_CLIENT_SECRET is not set or is using template value")
    print("Please update your .env file with your actual Spotify Client Secret")
    exit(1)

print("\n✓ Credentials found in .env file")
print("\nTesting authentication...")

try:
    # Try to authenticate
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Try a simple search
    results = sp.search(q='test', type='track', limit=1)

    print("✓ Authentication successful!")
    print("✓ API connection working!")

    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        print(f"\nTest search result:")
        print(f"  Song: {track['name']}")
        print(f"  Artist: {track['artists'][0]['name']}")

    print("\n" + "="*60)
    print("SUCCESS - Your Spotify credentials are valid!")
    print("="*60)
    print("\nYou can now run: python collect_data.py --quick")

except Exception as e:
    print(f"\n❌ Authentication failed!")
    print(f"Error: {str(e)}")
    print("\n" + "="*60)
    print("TROUBLESHOOTING STEPS:")
    print("="*60)
    print("\n1. Check your Spotify Developer Dashboard:")
    print("   https://developer.spotify.com/dashboard")
    print("\n2. Make sure you're copying the correct credentials:")
    print("   - Click on your app")
    print("   - Click 'Settings'")
    print("   - Copy 'Client ID'")
    print("   - Click 'View client secret' and copy it")
    print("\n3. Update your .env file:")
    print("   SPOTIFY_CLIENT_ID=your_actual_client_id")
    print("   SPOTIFY_CLIENT_SECRET=your_actual_client_secret")
    print("\n4. Make sure there are NO spaces or quotes around the values")
    print("\n5. Save the .env file and run this test again")
    exit(1)
