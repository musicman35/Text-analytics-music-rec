"""
Hugging Face Spotify Dataset Collector
Uses maharshipandya/spotify-tracks-dataset from Hugging Face
"""

import pandas as pd
from datasets import load_dataset
from typing import Dict, List, Optional
import time
from tqdm import tqdm

class HuggingFaceCollector:
    """Collect songs from Hugging Face Spotify dataset"""

    def __init__(self):
        self.dataset = None
        self.df = None

    def load_dataset(self):
        """Load the Spotify dataset from Hugging Face"""
        print("\nLoading Spotify dataset from Hugging Face...")
        print("Dataset: maharshipandya/spotify-tracks-dataset")

        try:
            # Load dataset
            self.dataset = load_dataset("maharshipandya/spotify-tracks-dataset")

            # Convert to pandas DataFrame for easier manipulation
            self.df = pd.DataFrame(self.dataset['train'])

            print(f"\n✓ Loaded {len(self.df)} songs from Hugging Face")
            print(f"\nColumns available: {list(self.df.columns)}")

            # Show sample
            print("\nSample data:")
            print(self.df.head(2))

            return True

        except Exception as e:
            print(f"\n✗ Error loading dataset: {e}")
            print("\nTrying to install datasets library...")
            import subprocess
            subprocess.run(["pip", "install", "datasets"], check=True)
            return self.load_dataset()

    def filter_by_genre(self, genres: List[str], songs_per_genre: int = 1000) -> pd.DataFrame:
        """
        Filter songs by genre

        Note: The dataset may use different genre naming.
        We'll need to inspect the actual genre field.
        """
        filtered_songs = []

        print(f"\nFiltering songs by genre...")
        print(f"Target: {songs_per_genre} songs per genre")

        for genre in genres:
            # Filter songs by genre (case-insensitive partial match)
            # This handles variations like "pop", "k-pop", "pop rock", etc.
            genre_songs = self.df[
                self.df['track_genre'].str.contains(genre, case=False, na=False)
            ]

            # Sample if we have more than needed
            if len(genre_songs) > songs_per_genre:
                genre_songs = genre_songs.sample(n=songs_per_genre, random_state=42)

            filtered_songs.append(genre_songs)
            print(f"  {genre}: {len(genre_songs)} songs")

        # Combine all genres
        result = pd.concat(filtered_songs, ignore_index=True)
        print(f"\nTotal filtered songs: {len(result)}")

        return result

    def prepare_song_data(self, row: pd.Series) -> Dict:
        """
        Convert DataFrame row to standardized song dictionary

        Maps Hugging Face dataset fields to our schema
        """
        song = {
            # Basic metadata
            'name': row.get('track_name', ''),
            'artist': row.get('artists', ''),
            'album': row.get('album_name', ''),
            'genre': row.get('track_genre', ''),

            # Spotify IDs (if available)
            'spotify_id': row.get('track_id', ''),
            'artist_id': row.get('artist_id', ''),

            # Audio features
            'features': {
                'danceability': row.get('danceability', 0.5),
                'energy': row.get('energy', 0.5),
                'valence': row.get('valence', 0.5),
                'tempo': row.get('tempo', 120.0),
                'loudness': row.get('loudness', -5.0),
                'speechiness': row.get('speechiness', 0.1),
                'acousticness': row.get('acousticness', 0.5),
                'instrumentalness': row.get('instrumentalness', 0.0),
                'liveness': row.get('liveness', 0.1),
                'key': row.get('key', 0),
                'mode': row.get('mode', 1),
                'time_signature': row.get('time_signature', 4),
            },

            # Additional metadata
            'popularity': row.get('popularity', 50),
            'duration_ms': row.get('duration_ms', 180000),
            'explicit': row.get('explicit', False),
        }

        return song

    def collect_songs(
        self,
        genres: List[str] = ['pop', 'rock', 'hip-hop', 'electronic', 'r&b'],
        songs_per_genre: int = 1000
    ) -> List[Dict]:
        """
        Collect songs from Hugging Face dataset

        Returns:
            List of song dictionaries with metadata and audio features
        """
        # Load dataset if not already loaded
        if self.df is None:
            self.load_dataset()

        # Filter by genre
        filtered_df = self.filter_by_genre(genres, songs_per_genre)

        # Convert to song dictionaries
        songs = []
        print("\nPreparing song data...")
        for idx, row in tqdm(filtered_df.iterrows(), total=len(filtered_df)):
            song = self.prepare_song_data(row)
            songs.append(song)

        print(f"\n✓ Prepared {len(songs)} songs from Hugging Face dataset")

        return songs

    def get_dataset_info(self) -> Dict:
        """Get information about the loaded dataset"""
        if self.df is None:
            self.load_dataset()

        info = {
            'total_songs': len(self.df),
            'columns': list(self.df.columns),
            'genres': self.df['track_genre'].value_counts().head(20).to_dict() if 'track_genre' in self.df.columns else {},
            'has_audio_features': all(
                col in self.df.columns
                for col in ['danceability', 'energy', 'valence', 'tempo']
            ),
        }

        return info


def test_huggingface_collector():
    """Test the Hugging Face collector"""
    print("="*60)
    print("HUGGING FACE COLLECTOR TEST")
    print("="*60)

    collector = HuggingFaceCollector()

    # Get dataset info
    info = collector.get_dataset_info()
    print("\nDataset Info:")
    print(f"  Total songs: {info['total_songs']}")
    print(f"  Has audio features: {info['has_audio_features']}")
    print(f"\nTop 10 genres:")
    for genre, count in list(info['genres'].items())[:10]:
        print(f"    {genre}: {count}")

    # Collect small sample
    print("\n" + "="*60)
    print("Collecting sample (10 songs per genre)...")
    print("="*60)

    songs = collector.collect_songs(
        genres=['pop', 'rock', 'hip-hop'],
        songs_per_genre=10
    )

    print(f"\n✓ Collected {len(songs)} songs")

    # Show sample song
    if songs:
        print("\nSample song:")
        sample = songs[0]
        print(f"  Name: {sample['name']}")
        print(f"  Artist: {sample['artist']}")
        print(f"  Genre: {sample['genre']}")
        print(f"  Audio features: {sample['features']}")


if __name__ == '__main__':
    test_huggingface_collector()
