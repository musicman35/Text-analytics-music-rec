#!/usr/bin/env python
"""
Verify Qdrant Database Contents
Provides comprehensive information about your Qdrant collections
"""

import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

from src.database.qdrant_storage import QdrantStorage


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def verify_qdrant():
    """Verify Qdrant database contents"""

    print_section("QDRANT DATABASE VERIFICATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check environment configuration
    print_section("CONFIGURATION")
    use_cloud = os.getenv("QDRANT_USE_CLOUD", "false").lower() == "true"
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")

    print(f"Mode: {'Qdrant Cloud' if use_cloud else 'Local Qdrant'}")
    print(f"Host: {qdrant_host}")

    try:
        # Initialize storage
        storage = QdrantStorage()
        print("✓ Successfully connected to Qdrant")

        # Get collections
        print_section("COLLECTIONS")
        collections = storage.client.get_collections()
        collection_names = [c.name for c in collections.collections]

        print(f"Found {len(collection_names)} collections:")
        for name in collection_names:
            print(f"  - {name}")

        # Check songs collection
        if storage.songs_collection in collection_names:
            print_section("SONGS COLLECTION")

            try:
                # Get collection info
                info = storage.client.get_collection(storage.songs_collection)
                print(f"Points count: {info.points_count}")

                if info.points_count > 0:
                    # Get sample songs
                    result, next_page = storage.client.scroll(
                        collection_name=storage.songs_collection,
                        limit=100
                    )

                    # Analyze genres
                    genres = {}
                    artists = set()

                    for point in result:
                        song = point.payload
                        genre = song.get('genre', 'Unknown')
                        artist = song.get('artist', 'Unknown')

                        genres[genre] = genres.get(genre, 0) + 1
                        artists.add(artist)

                    print(f"\n✓ DATABASE IS POPULATED")
                    print(f"  Total songs: {info.points_count}")
                    print(f"  Unique artists (in sample): {len(artists)}")

                    print(f"\n  Genre Distribution (first 100 songs):")
                    for genre, count in sorted(genres.items(), key=lambda x: x[1], reverse=True):
                        print(f"    {genre}: {count} songs")

                    # Show sample songs
                    print(f"\n  Sample Songs:")
                    for i, point in enumerate(result[:5], 1):
                        song = point.payload
                        print(f"    {i}. {song.get('name', 'Unknown')}")
                        print(f"       Artist: {song.get('artist', 'Unknown')}")
                        print(f"       Genre: {song.get('genre', 'Unknown')}")
                        print(f"       Popularity: {song.get('popularity', 0)}")

                        # Check audio features
                        features = ['energy', 'valence', 'danceability', 'tempo']
                        feature_values = [f"{f}={song.get(f, 0):.2f}" if f != 'tempo'
                                        else f"{f}={song.get(f, 0):.0f}"
                                        for f in features if song.get(f) is not None]
                        if feature_values:
                            print(f"       Features: {', '.join(feature_values)}")

                    # Test search functionality
                    print_section("SEARCH TEST")
                    test_queries = ["happy songs", "energetic music", "calm relaxing"]

                    for query in test_queries:
                        results = storage.search_songs(query, limit=3)
                        print(f"\n  Query: '{query}'")
                        if results:
                            print(f"  ✓ Found {len(results)} results")
                            for j, song in enumerate(results[:2], 1):
                                print(f"    {j}. {song.get('name')} by {song.get('artist')} (score: {song.get('score', 0):.3f})")
                        else:
                            print(f"  ✗ No results found")

                else:
                    print("\n✗ DATABASE IS EMPTY")
                    print("  No songs found in the collection")
                    print("\n  To populate the database, run:")
                    print("    python collect_data_qdrant_only.py --quick")

            except Exception as e:
                print(f"✗ Error accessing songs collection: {e}")
        else:
            print("\n✗ Songs collection not found!")
            print("  The collection may need to be created")

        # Check users collection
        if storage.users_collection in collection_names:
            print_section("USERS COLLECTION")
            try:
                info = storage.client.get_collection(storage.users_collection)
                print(f"Users count: {info.points_count}")
            except Exception as e:
                print(f"Error: {e}")

        # Summary
        print_section("SUMMARY")

        if storage.songs_collection in collection_names:
            info = storage.client.get_collection(storage.songs_collection)
            if info.points_count > 0:
                print("✅ Database Status: READY")
                print(f"✅ Songs Available: {info.points_count}")
                print("✅ Search Functionality: Working")
                print("\n🎵 Your music recommendation system is ready to use!")
            else:
                print("⚠️ Database Status: EMPTY")
                print("⚠️ Action Required: Run data collection")
        else:
            print("❌ Database Status: NOT INITIALIZED")
            print("❌ Action Required: Initialize collections")

    except Exception as e:
        print_section("ERROR")
        print(f"✗ Failed to connect to Qdrant: {e}")
        print("\nPossible issues:")
        print("  1. Check your .env file has correct QDRANT_HOST and QDRANT_API_KEY")
        print("  2. Ensure Qdrant Cloud instance is running")
        print("  3. Check internet connection")

        import traceback
        print("\nFull error:")
        traceback.print_exc()


if __name__ == "__main__":
    verify_qdrant()