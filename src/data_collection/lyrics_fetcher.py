"""
Lyrics Fetcher using Genius API via lyricsgenius library
Fetches song lyrics to enhance recommendation semantic search
"""

import os
import time
import re
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

# Import will be wrapped in try/except for graceful handling
try:
    from lyricsgenius import Genius
    LYRICSGENIUS_AVAILABLE = True
except ImportError:
    LYRICSGENIUS_AVAILABLE = False
    Genius = None

import config


class LyricsFetcher:
    """
    Fetches lyrics from Genius API using lyricsgenius library

    Usage:
        fetcher = LyricsFetcher()
        lyrics = fetcher.get_lyrics("Bohemian Rhapsody", "Queen")
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the lyrics fetcher

        Args:
            api_key: Genius API access token. If not provided, uses GENIUS_API_KEY from env/config
        """
        if not LYRICSGENIUS_AVAILABLE:
            raise ImportError(
                "lyricsgenius is not installed. "
                "Install it with: pip install lyricsgenius"
            )

        # Get API key from parameter, environment, or config
        self.api_key = api_key or os.getenv("GENIUS_API_KEY") or config.GENIUS_API_KEY

        if not self.api_key or self.api_key == "your_genius_api_key":
            raise ValueError(
                "Genius API key not found. Set GENIUS_API_KEY environment variable "
                "or pass api_key parameter. Get a free key at https://genius.com/api-clients"
            )

        # Initialize Genius client with configuration
        self.genius = Genius(self.api_key, timeout=10, retries=3)

        # Configure the client
        self.genius.verbose = False  # Suppress status messages
        self.genius.remove_section_headers = True  # Remove [Verse], [Chorus], etc.
        self.genius.skip_non_songs = True  # Skip non-song results
        self.genius.excluded_terms = ["(Remix)", "(Live)", "(Acoustic)", "(Cover)"]

        # Rate limiting
        self.request_delay = 0.5  # seconds between requests
        self.last_request_time = 0

        # Cache to avoid duplicate lookups
        self._cache: Dict[str, Optional[str]] = {}

    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for cache key and matching"""
        if not text:
            return ""
        # Lowercase, remove special characters, normalize whitespace
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _create_cache_key(self, song_name: str, artist_name: str) -> str:
        """Create a normalized cache key"""
        return f"{self._normalize_text(artist_name)}:{self._normalize_text(song_name)}"

    def _clean_lyrics(self, lyrics: str) -> str:
        """
        Clean up fetched lyrics

        - Remove contributor annotations
        - Remove embed markers
        - Normalize whitespace
        """
        if not lyrics:
            return ""

        # Remove common Genius artifacts
        # Remove "XXX Contributors" and similar lines
        lyrics = re.sub(r'\d+\s*Contributors?.*?\n', '', lyrics, flags=re.IGNORECASE)

        # Remove "Embed" at the end
        lyrics = re.sub(r'Embed$', '', lyrics.strip())

        # Remove "You might also like" sections
        lyrics = re.sub(r'You might also like.*?(?=\n|$)', '', lyrics, flags=re.IGNORECASE)

        # Normalize multiple newlines
        lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)

        # Strip leading/trailing whitespace
        lyrics = lyrics.strip()

        return lyrics

    def get_lyrics(self, song_name: str, artist_name: str) -> Optional[str]:
        """
        Fetch lyrics for a song

        Args:
            song_name: Name of the song
            artist_name: Name of the artist

        Returns:
            Lyrics string or None if not found
        """
        if not song_name or not artist_name:
            return None

        # Check cache first
        cache_key = self._create_cache_key(song_name, artist_name)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Rate limit
            self._rate_limit()

            # Search for the song
            song = self.genius.search_song(song_name, artist_name)

            if song and song.lyrics:
                lyrics = self._clean_lyrics(song.lyrics)
                self._cache[cache_key] = lyrics
                return lyrics

            # Song not found
            self._cache[cache_key] = None
            return None

        except Exception as e:
            print(f"Error fetching lyrics for '{song_name}' by '{artist_name}': {e}")
            self._cache[cache_key] = None
            return None

    def get_lyrics_preview(self, song_name: str, artist_name: str, max_chars: int = 500) -> Optional[str]:
        """
        Get a preview/snippet of the lyrics (first N characters)

        Useful for embedding generation without using full lyrics

        Args:
            song_name: Name of the song
            artist_name: Name of the artist
            max_chars: Maximum characters to return

        Returns:
            Lyrics preview or None
        """
        lyrics = self.get_lyrics(song_name, artist_name)

        if not lyrics:
            return None

        if len(lyrics) <= max_chars:
            return lyrics

        # Try to cut at a word boundary
        preview = lyrics[:max_chars]
        last_space = preview.rfind(' ')
        if last_space > max_chars * 0.8:  # Only if we don't lose too much
            preview = preview[:last_space]

        return preview + "..."

    def get_lyrics_batch(
        self,
        songs: List[Dict],
        progress_callback=None
    ) -> List[Dict]:
        """
        Fetch lyrics for multiple songs

        Args:
            songs: List of song dictionaries with 'name' and 'artist' keys
            progress_callback: Optional callback function(current, total) for progress updates

        Returns:
            Same list of songs with 'lyrics' and 'lyrics_preview' fields added
        """
        total = len(songs)

        for i, song in enumerate(songs):
            song_name = song.get('name', '')
            artist_name = song.get('artist', '')

            if song_name and artist_name:
                lyrics = self.get_lyrics(song_name, artist_name)
                song['lyrics'] = lyrics

                # Also create a preview for embedding
                if lyrics:
                    song['lyrics_preview'] = lyrics[:500] + "..." if len(lyrics) > 500 else lyrics
                else:
                    song['lyrics_preview'] = None

            if progress_callback:
                progress_callback(i + 1, total)

        return songs

    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache"""
        total = len(self._cache)
        found = sum(1 for v in self._cache.values() if v is not None)
        return {
            "total_lookups": total,
            "found": found,
            "not_found": total - found,
            "hit_rate": found / total if total > 0 else 0
        }

    def clear_cache(self):
        """Clear the lyrics cache"""
        self._cache.clear()


def test_lyrics_fetcher():
    """Test the lyrics fetcher"""
    print("=" * 60)
    print("LYRICS FETCHER TEST")
    print("=" * 60)

    try:
        fetcher = LyricsFetcher()
        print("Genius API client initialized\n")

        # Test songs
        test_songs = [
            ("Bohemian Rhapsody", "Queen"),
            ("Blinding Lights", "The Weeknd"),
            ("Shape of You", "Ed Sheeran"),
        ]

        for song_name, artist_name in test_songs:
            print(f"\nFetching: '{song_name}' by {artist_name}")
            print("-" * 40)

            preview = fetcher.get_lyrics_preview(song_name, artist_name, max_chars=200)

            if preview:
                print(f"Preview ({len(preview)} chars):")
                print(preview[:200])
            else:
                print("Lyrics not found")

        # Show cache stats
        print("\n" + "=" * 60)
        stats = fetcher.get_cache_stats()
        print(f"Cache stats: {stats}")

    except ValueError as e:
        print(f"\nConfiguration error: {e}")
        print("\nTo use the lyrics fetcher:")
        print("1. Get a free API key at https://genius.com/api-clients")
        print("2. Set GENIUS_API_KEY in your .env file")
    except ImportError as e:
        print(f"\nDependency error: {e}")


if __name__ == "__main__":
    test_lyrics_fetcher()
