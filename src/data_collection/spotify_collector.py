"""
Spotify Data Collector
Collects 5000 songs (1000 per genre) with audio features from Spotify API
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import json
from typing import List, Dict, Optional
from pathlib import Path
from tqdm import tqdm
import config
from src.database.sqlite_manager import SQLiteManager


class SpotifyCollector:
    """Collects song data from Spotify API"""

    def __init__(self):
        # Initialize Spotify client
        auth_manager = SpotifyClientCredentials(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        self.cache_dir = config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db = SQLiteManager()

    def search_songs_by_query(self, query: str, genre: str, limit: int = 50) -> List[Dict]:
        """Search songs using a query string"""
        try:
            results = self.sp.search(
                q=query,
                type='track',
                limit=limit,
                market='US'
            )

            songs = []
            for item in results['tracks']['items']:
                if item and item.get('id'):
                    song_data = {
                        'spotify_id': item['id'],
                        'name': item['name'],
                        'artist': ', '.join([artist['name'] for artist in item['artists']]),
                        'album': item['album']['name'],
                        'genre': genre,
                        'popularity': item['popularity']
                    }
                    songs.append(song_data)

            time.sleep(config.SPOTIFY_RATE_LIMIT_DELAY)
            return songs

        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return []

    def get_audio_features(self, track_ids: List[str]) -> Dict[str, Dict]:
        """Get audio features for multiple tracks"""
        features_map = {}

        try:
            # Spotify API allows up to 100 tracks per request
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                results = self.sp.audio_features(batch)

                for track_id, features in zip(batch, results):
                    if features:
                        features_map[track_id] = {
                            'danceability': features['danceability'],
                            'energy': features['energy'],
                            'valence': features['valence'],
                            'tempo': features['tempo'],
                            'acousticness': features['acousticness'],
                            'instrumentalness': features['instrumentalness'],
                            'speechiness': features['speechiness'],
                            'loudness': features['loudness']
                        }

                time.sleep(config.SPOTIFY_RATE_LIMIT_DELAY)

        except Exception as e:
            print(f"Error getting audio features: {e}")

        return features_map

    def collect_genre_songs(self, genre: str, target_count: int = 1000) -> List[Dict]:
        """Collect songs for a specific genre"""
        print(f"\nCollecting {target_count} songs for genre: {genre}")

        all_songs = []
        seen_ids = set()

        # Use multiple search queries for diversity
        queries = config.GENRE_SEARCH_QUERIES.get(genre, [genre])

        for query in queries:
            if len(all_songs) >= target_count:
                break

            print(f"  Searching: {query}")

            # Try different offsets to get more songs
            for offset in range(0, 500, 50):
                if len(all_songs) >= target_count:
                    break

                try:
                    results = self.sp.search(
                        q=f"genre:{query}",
                        type='track',
                        limit=50,
                        offset=offset,
                        market='US'
                    )

                    for item in results['tracks']['items']:
                        if item and item.get('id') and item['id'] not in seen_ids:
                            song_data = {
                                'spotify_id': item['id'],
                                'name': item['name'],
                                'artist': ', '.join([artist['name'] for artist in item['artists']]),
                                'album': item['album']['name'],
                                'genre': genre,
                                'popularity': item['popularity']
                            }
                            all_songs.append(song_data)
                            seen_ids.add(item['id'])

                            if len(all_songs) >= target_count:
                                break

                    time.sleep(config.SPOTIFY_RATE_LIMIT_DELAY)

                except Exception as e:
                    print(f"  Error at offset {offset}: {e}")
                    continue

        print(f"  Collected {len(all_songs)} songs for {genre}")
        return all_songs[:target_count]

    def enrich_songs_with_features(self, songs: List[Dict]) -> List[Dict]:
        """Add audio features to songs"""
        print("Fetching audio features...")

        track_ids = [song['spotify_id'] for song in songs]
        features_map = self.get_audio_features(track_ids)

        enriched_songs = []
        for song in tqdm(songs, desc="Enriching songs"):
            if song['spotify_id'] in features_map:
                song['features'] = features_map[song['spotify_id']]
                enriched_songs.append(song)

        print(f"Successfully enriched {len(enriched_songs)}/{len(songs)} songs")
        return enriched_songs

    def save_to_cache(self, songs: List[Dict], filename: str):
        """Save collected songs to cache"""
        cache_file = self.cache_dir / filename
        with open(cache_file, 'w') as f:
            json.dump(songs, f, indent=2)
        print(f"Saved {len(songs)} songs to {cache_file}")

    def load_from_cache(self, filename: str) -> Optional[List[Dict]]:
        """Load songs from cache"""
        cache_file = self.cache_dir / filename
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                songs = json.load(f)
            print(f"Loaded {len(songs)} songs from cache")
            return songs
        return None

    def save_to_database(self, songs: List[Dict]):
        """Save songs to SQLite database"""
        print("\nSaving songs to database...")

        for song in tqdm(songs, desc="Saving to DB"):
            try:
                self.db.add_song(
                    spotify_id=song['spotify_id'],
                    name=song['name'],
                    artist=song['artist'],
                    album=song['album'],
                    genre=song['genre'],
                    features=song['features']
                )
            except Exception as e:
                print(f"Error saving song {song['name']}: {e}")

        print(f"Database now contains {self.db.get_songs_count()} songs")

    def collect_all_songs(self, use_cache: bool = True) -> List[Dict]:
        """Collect all 5000 songs across all genres"""
        all_songs = []

        for genre in config.GENRES:
            cache_filename = f"spotify_{genre}_songs.json"

            # Try to load from cache
            if use_cache:
                cached_songs = self.load_from_cache(cache_filename)
                if cached_songs:
                    all_songs.extend(cached_songs)
                    continue

            # Collect new songs
            genre_songs = self.collect_genre_songs(genre, config.TARGET_SONGS_PER_GENRE)

            if genre_songs:
                # Enrich with audio features
                enriched_songs = self.enrich_songs_with_features(genre_songs)

                # Save to cache
                self.save_to_cache(enriched_songs, cache_filename)

                all_songs.extend(enriched_songs)

        print(f"\n{'='*60}")
        print(f"Total songs collected: {len(all_songs)}")
        print(f"{'='*60}")

        return all_songs

    def run_collection(self, use_cache: bool = True, save_to_db: bool = True):
        """Main method to run the collection process"""
        print("Starting Spotify data collection...")
        print(f"Target: {config.TOTAL_SONGS_TARGET} songs ({config.TARGET_SONGS_PER_GENRE} per genre)")
        print(f"Genres: {', '.join(config.GENRES)}")

        # Collect songs
        all_songs = self.collect_all_songs(use_cache=use_cache)

        # Save to database
        if save_to_db and all_songs:
            self.save_to_database(all_songs)

        return all_songs


def main():
    """Run Spotify collection as standalone script"""
    collector = SpotifyCollector()
    songs = collector.run_collection(use_cache=True, save_to_db=True)
    print(f"\nCollection complete! Total songs: {len(songs)}")


if __name__ == "__main__":
    main()
