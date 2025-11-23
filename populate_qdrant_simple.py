#!/usr/bin/env python
"""
Simplified script to populate Qdrant with songs without fetching lyrics
Uses only Hugging Face dataset metadata for fast population
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Verify OpenAI key is loaded
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key or openai_key == "your_openai_api_key":
    print("ERROR: OpenAI API key not properly configured!")
    print("Please check your .env file")
    sys.exit(1)

from datasets import load_dataset
import pandas as pd
from src.database.qdrant_storage import QdrantStorage

def collect_songs_simple():
    """Collect songs from HuggingFace without fetching lyrics"""

    print("="*60)
    print("SIMPLE QDRANT POPULATION")
    print("="*60)

    # Load HuggingFace dataset
    print("\nLoading Spotify dataset from Hugging Face...")
    dataset = load_dataset("maharshipandya/spotify-tracks-dataset", split="train")
    df = pd.DataFrame(dataset)
    print(f"✓ Loaded {len(df)} songs")

    # Select diverse genres
    genres = ['pop', 'rock', 'hip-hop', 'electronic', 'indie', 'country', 'jazz', 'classical', 'r&b', 'metal']
    songs_per_genre = 15  # 15 songs per genre = 150 total

    all_songs = []

    for genre in genres:
        print(f"\nCollecting {genre} songs...")

        # Handle genre name variations
        genre_filter = genre
        if genre == 'hip-hop':
            genre_filter = 'hip-hop'
        elif genre == 'r&b':
            # Check if 'r-n-b' or 'r&b' exists in dataset
            if 'r-n-b' in df['track_genre'].unique():
                genre_filter = 'r-n-b'

        genre_songs = df[df['track_genre'] == genre_filter].head(songs_per_genre)

        # If we don't find enough songs for this genre, try to get more from similar genres
        if len(genre_songs) < songs_per_genre:
            print(f"  Only found {len(genre_songs)} {genre} songs, skipping...")
            continue

        for _, row in genre_songs.iterrows():
            # Clean artist names (remove brackets and quotes)
            artist_str = str(row.get('artists', 'Unknown'))
            if artist_str.startswith('[') and artist_str.endswith(']'):
                artist_str = artist_str[1:-1].replace("'", "").replace('"', '')

            song = {
                'spotify_id': row.get('track_id', ''),
                'name': row.get('track_name', 'Unknown'),
                'artist': artist_str,
                'album': row.get('album_name', 'Unknown'),
                'genre': genre,
                'popularity': int(row.get('popularity', 0)),
                'duration_ms': int(row.get('duration_ms', 0)),
                'explicit': bool(row.get('explicit', False)),
                'lyrics': f"Song: {row.get('track_name', 'Unknown')} by {artist_str}. Genre: {genre}.",  # Simple placeholder

                # Audio features
                'danceability': float(row.get('danceability', 0.5)),
                'energy': float(row.get('energy', 0.5)),
                'key': int(row.get('key', 0)),
                'loudness': float(row.get('loudness', -10)),
                'mode': int(row.get('mode', 0)),
                'speechiness': float(row.get('speechiness', 0.05)),
                'acousticness': float(row.get('acousticness', 0.5)),
                'instrumentalness': float(row.get('instrumentalness', 0)),
                'liveness': float(row.get('liveness', 0.1)),
                'valence': float(row.get('valence', 0.5)),
                'tempo': float(row.get('tempo', 120)),
            }
            all_songs.append(song)

        print(f"  ✓ Collected {len(genre_songs)} {genre} songs")

    print(f"\n✓ Total songs collected: {len(all_songs)}")
    return all_songs

def main():
    try:
        # Collect songs
        songs = collect_songs_simple()

        if not songs:
            print("✗ No songs collected!")
            return

        # Initialize Qdrant storage
        print("\n" + "="*60)
        print("SAVING TO QDRANT")
        print("="*60)

        storage = QdrantStorage()
        print("✓ Connected to Qdrant")

        # Add songs to Qdrant
        print(f"\nAdding {len(songs)} songs to Qdrant...")
        print("(This will generate embeddings for each song)")

        success = storage.add_songs(songs)

        if success:
            print(f"✓ Successfully added songs to Qdrant")

            # Verify collection
            try:
                info = storage.client.get_collection(storage.songs_collection)
                print(f"\nCollection stats:")
                print(f"  Points count: {info.points_count}")
                print(f"  Indexed vectors: {info.indexed_vectors_count if hasattr(info, 'indexed_vectors_count') else 'N/A'}")

                # Get a sample of songs to verify
                result, _ = storage.client.scroll(
                    collection_name=storage.songs_collection,
                    limit=5
                )

                if result:
                    print(f"\nSample songs added:")
                    for i, point in enumerate(result[:3], 1):
                        song = point.payload
                        print(f"  {i}. {song.get('name', 'Unknown')} by {song.get('artist', 'Unknown')}")
                        print(f"     Genre: {song.get('genre', 'Unknown')}, Popularity: {song.get('popularity', 0)}")
            except Exception as e:
                print(f"Could not get collection stats: {e}")
        else:
            print("✗ Failed to add songs to Qdrant")

        print("\n" + "="*60)
        print("COMPLETE!")
        print("="*60)
        print("\nYou can now test the Streamlit app with the populated data.")
        print("Run: streamlit run streamlit_app.py")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()