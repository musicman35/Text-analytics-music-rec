"""
Lyrics Data Collector
Fetches lyrics for songs using Genius API
"""

import lyricsgenius
import time
import json
import re
from typing import Optional, List, Dict
from pathlib import Path
from tqdm import tqdm
import config
from src.database.sqlite_manager import SQLiteManager


class LyricsCollector:
    """Collects lyrics from Genius API"""

    def __init__(self):
        self.genius = lyricsgenius.Genius(
            config.GENIUS_API_KEY,
            skip_non_songs=True,
            excluded_terms=["(Remix)", "(Live)"],
            remove_section_headers=True
        )
        self.cache_dir = config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db = SQLiteManager()

    def clean_lyrics(self, lyrics: str) -> str:
        """Clean and normalize lyrics text"""
        if not lyrics:
            return ""

        # Remove common tags and annotations
        lyrics = re.sub(r'\[.*?\]', '', lyrics)  # Remove [Verse], [Chorus], etc.
        lyrics = re.sub(r'\(.*?\)', '', lyrics)  # Remove parenthetical notes
        lyrics = re.sub(r'Lyrics?\s*$', '', lyrics, flags=re.IGNORECASE)  # Remove "Lyrics" suffix
        lyrics = re.sub(r'\d+Embed$', '', lyrics)  # Remove "12Embed" type endings

        # Normalize whitespace
        lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)  # Max 2 consecutive newlines
        lyrics = lyrics.strip()

        return lyrics

    def search_lyrics(self, song_name: str, artist_name: str) -> Optional[str]:
        """Search for lyrics on Genius"""
        try:
            # Clean artist name (take first artist if multiple)
            artist_name = artist_name.split(',')[0].strip()

            # Search for the song
            song = self.genius.search_song(song_name, artist_name)

            if song and song.lyrics:
                cleaned_lyrics = self.clean_lyrics(song.lyrics)
                time.sleep(config.GENIUS_RATE_LIMIT_DELAY)
                return cleaned_lyrics

        except Exception as e:
            # Silently handle errors (rate limits, not found, etc.)
            pass

        time.sleep(config.GENIUS_RATE_LIMIT_DELAY)
        return None

    def collect_lyrics_for_songs(self, songs: List[Dict]) -> List[Dict]:
        """Collect lyrics for a list of songs"""
        print(f"\nCollecting lyrics for {len(songs)} songs...")

        songs_with_lyrics = []
        lyrics_found = 0
        lyrics_missing = 0

        for song in tqdm(songs, desc="Fetching lyrics"):
            lyrics = self.search_lyrics(song['name'], song['artist'])

            song_with_lyrics = song.copy()
            song_with_lyrics['lyrics'] = lyrics

            if lyrics:
                lyrics_found += 1
            else:
                lyrics_missing += 1

            songs_with_lyrics.append(song_with_lyrics)

        print(f"\nLyrics found: {lyrics_found}/{len(songs)} ({lyrics_found/len(songs)*100:.1f}%)")
        print(f"Lyrics missing: {lyrics_missing}")

        return songs_with_lyrics

    def save_to_cache(self, songs: List[Dict], filename: str):
        """Save songs with lyrics to cache"""
        cache_file = self.cache_dir / filename
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(songs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(songs)} songs with lyrics to {cache_file}")

    def load_from_cache(self, filename: str) -> Optional[List[Dict]]:
        """Load songs with lyrics from cache"""
        cache_file = self.cache_dir / filename
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                songs = json.load(f)
            print(f"Loaded {len(songs)} songs from cache")
            return songs
        return None

    def update_database_with_lyrics(self, songs: List[Dict]):
        """Update database songs with lyrics"""
        print("\nUpdating database with lyrics...")

        for song in tqdm(songs, desc="Updating DB"):
            try:
                # Get existing song from database
                existing_song = self.db.get_song(spotify_id=song['spotify_id'])

                if existing_song:
                    # Update with lyrics
                    self.db.add_song(
                        spotify_id=song['spotify_id'],
                        name=song['name'],
                        artist=song['artist'],
                        album=song.get('album'),
                        genre=song.get('genre'),
                        features=song.get('features', existing_song['features']),
                        lyrics=song.get('lyrics')
                    )
            except Exception as e:
                print(f"Error updating song {song['name']}: {e}")

        print("Database update complete")

    def collect_lyrics_by_genre(self, genre: str, use_cache: bool = True):
        """Collect lyrics for songs of a specific genre"""
        cache_filename = f"lyrics_{genre}_songs.json"

        # Try to load from cache
        if use_cache:
            cached_songs = self.load_from_cache(cache_filename)
            if cached_songs:
                return cached_songs

        # Load songs from Spotify cache
        spotify_cache = f"spotify_{genre}_songs.json"
        songs = self.load_from_cache(spotify_cache)

        if not songs:
            print(f"No Spotify songs found for {genre}. Run Spotify collector first.")
            return []

        # Collect lyrics
        songs_with_lyrics = self.collect_lyrics_for_songs(songs)

        # Save to cache
        self.save_to_cache(songs_with_lyrics, cache_filename)

        return songs_with_lyrics

    def collect_all_lyrics(self, use_cache: bool = True) -> List[Dict]:
        """Collect lyrics for all genres"""
        all_songs = []

        for genre in config.GENRES:
            print(f"\n{'='*60}")
            print(f"Processing genre: {genre}")
            print(f"{'='*60}")

            genre_songs = self.collect_lyrics_by_genre(genre, use_cache=use_cache)
            all_songs.extend(genre_songs)

        print(f"\n{'='*60}")
        print(f"Total songs with lyrics: {len(all_songs)}")
        lyrics_count = sum(1 for s in all_songs if s.get('lyrics'))
        if len(all_songs) > 0:
            print(f"Lyrics found: {lyrics_count}/{len(all_songs)} ({lyrics_count/len(all_songs)*100:.1f}%)")
        else:
            print(f"Lyrics found: 0/0 (No songs to process)")
        print(f"{'='*60}")

        return all_songs

    def run_collection(self, use_cache: bool = True, save_to_db: bool = True):
        """Main method to run the lyrics collection process"""
        print("Starting lyrics collection...")
        print(f"Genres: {', '.join(config.GENRES)}")

        # Collect lyrics
        all_songs = self.collect_all_lyrics(use_cache=use_cache)

        # Update database
        if save_to_db and all_songs:
            self.update_database_with_lyrics(all_songs)

        return all_songs


def main():
    """Run lyrics collection as standalone script"""
    collector = LyricsCollector()
    songs = collector.run_collection(use_cache=True, save_to_db=True)
    print(f"\nLyrics collection complete! Total songs: {len(songs)}")


if __name__ == "__main__":
    main()
