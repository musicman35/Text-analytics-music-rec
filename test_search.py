#!/usr/bin/env python
"""Test Qdrant search functionality"""

import os
from dotenv import load_dotenv
load_dotenv()

from src.database.qdrant_storage import QdrantStorage
from openai import OpenAI

# Create storage instance
storage = QdrantStorage()
print("Connected to Qdrant")

# Check if we have songs
result, _ = storage.client.scroll(
    collection_name=storage.songs_collection,
    limit=5
)

print(f"\nFound {len(result)} songs in collection")
if result:
    print("\nFirst song details:")
    first_song = result[0]
    print(f"  ID: {first_song.id}")
    print(f"  Name: {first_song.payload.get('name')}")
    print(f"  Artist: {first_song.payload.get('artist')}")
    print(f"  Genre: {first_song.payload.get('genre')}")

    # Check if it has a vector
    if hasattr(first_song, 'vector'):
        if first_song.vector:
            print(f"  Vector length: {len(first_song.vector)}")
        else:
            print("  Vector: None")
    else:
        print("  Vector: Not found in point")

# Try to search
print("\n" + "="*60)
print("Testing search for 'happy songs'")
print("="*60)

# Generate embedding
try:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = openai_client.embeddings.create(
        input="happy songs",
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    print(f"✓ Generated embedding (dim: {len(embedding)})")

    # Try direct query_points
    print("\nTrying query_points...")
    results = storage.client.query_points(
        collection_name=storage.songs_collection,
        query=embedding,
        limit=5
    )

    print(f"Query result type: {type(results)}")
    print(f"Query result: {results}")

    if results:
        print(f"\n✓ Found {len(results)} results")
        for i, res in enumerate(results[:3], 1):
            if hasattr(res, 'payload'):
                print(f"  {i}. {res.payload.get('name')} - Score: {getattr(res, 'score', 'N/A')}")
    else:
        print("✗ No results returned")

except Exception as e:
    print(f"✗ Search error: {e}")
    import traceback
    traceback.print_exc()

# Also test the storage.search_songs method
print("\n" + "="*60)
print("Testing storage.search_songs method")
print("="*60)

results = storage.search_songs("happy songs", limit=5)
print(f"Results: {len(results)} songs found")
if results:
    for i, song in enumerate(results[:3], 1):
        print(f"  {i}. {song.get('name')} by {song.get('artist')}")
        print(f"     Score: {song.get('score', 'N/A')}")