#!/usr/bin/env python
"""Check if Qdrant has song data"""

from dotenv import load_dotenv
load_dotenv()

from src.database.qdrant_storage import QdrantStorage

storage = QdrantStorage()

# Check collection info
try:
    info = storage.client.get_collection(storage.songs_collection)
    print(f"Songs collection info:")
    print(f"  Points count: {info.points_count}")
    print(f"  Indexed vectors count: {info.indexed_vectors_count}")

    # Try to get some songs
    result, _ = storage.client.scroll(
        collection_name=storage.songs_collection,
        limit=5
    )

    print(f"\nFound {len(result)} songs in collection")

    if result:
        print("\nSample songs:")
        for i, point in enumerate(result[:3], 1):
            song = point.payload
            print(f"  {i}. {song.get('name', 'Unknown')} by {song.get('artist', 'Unknown')}")
            print(f"     Genre: {song.get('genre', 'Unknown')}")
    else:
        print("\n⚠️ WARNING: Songs collection is EMPTY!")
        print("You need to run data collection first:")
        print("  python collect_data.py")

except Exception as e:
    print(f"Error: {e}")