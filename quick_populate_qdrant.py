#!/usr/bin/env python
"""
Quick script to populate Qdrant with songs without fetching lyrics
Uses only Hugging Face dataset data for immediate population
"""

import os
from dotenv import load_dotenv
from datasets import load_dataset
import pandas as pd
from src.database.qdrant_storage import QdrantStorage

# Load environment variables
load_dotenv()

def collect_songs_no_lyrics():
    """Collect songs from HuggingFace without fetching lyrics"""

    print("="*60)
    print("QUICK QDRANT POPULATION (NO LYRICS)")
    print("="*60)

    # Load HuggingFace dataset
    print("\nLoading Spotify dataset from Hugging Face...")
    dataset = load_dataset("maharshipandya/spotify-tracks-dataset", split="train")
    df = pd.DataFrame(dataset)
    print(f"✓ Loaded {len(df)} songs")

    # Select diverse genres
    genres = ['pop', 'rock', 'hip-hop', 'electronic', 'indie', 'country', 'jazz', 'classical']
    songs_per_genre = 20

    all_songs = []

    for genre in genres:
        print(f"\nCollecting {genre} songs...")
        genre_songs = df[df['track_genre'] == genre].head(songs_per_genre)

        for _, row in genre_songs.iterrows():
            song = {
                'spotify_id': row.get('track_id', ''),
                'name': row.get('track_name', 'Unknown'),
                'artist': row.get('artists', 'Unknown'),
                'album': row.get('album_name', 'Unknown'),
                'genre': genre,
                'popularity': int(row.get('popularity', 0)),
                'duration_ms': int(row.get('duration_ms', 0)),
                'explicit': bool(row.get('explicit', False)),
                'lyrics': '',  # Empty lyrics for now

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
        songs = collect_songs_no_lyrics()

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
        success = storage.add_songs(songs)

        if success:
            print(f"✓ Successfully added songs to Qdrant")

            # Verify collection
            try:
                info = storage.client.get_collection(storage.songs_collection)
                print(f"\nCollection stats:")
                print(f"  Points count: {info.points_count}")
                print(f"  Indexed vectors: {info.indexed_vectors_count}")
            except Exception as e:
                print(f"Could not get collection stats: {e}")
        else:
            print("✗ Failed to add songs to Qdrant")

        print("\n" + "="*60)
        print("COMPLETE!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()