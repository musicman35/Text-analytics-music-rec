"""
Smart Lyrics Collector with Validation
Ensures we only keep songs that have lyrics available on Genius
"""

import os
from typing import Dict, List, Optional, Tuple
import time
from tqdm import tqdm
import lyricsgenius
from config import GENIUS_API_KEY


class SmartLyricsCollector:
    """
    Lyrics collector with built-in validation

    Strategy:
    1. Attempt to fetch lyrics from Genius
    2. Validate lyrics are real (not instrumental/empty)
    3. Track success/failure rates
    4. Only keep songs with valid lyrics
    """

    def __init__(self, max_retries: int = 2, timeout: int = 10):
        """
        Initialize smart lyrics collector

        Args:
            max_retries: Number of retries per song
            timeout: Request timeout in seconds
        """
        self.genius = lyricsgenius.Genius(
            GENIUS_API_KEY,
            timeout=timeout,
            retries=max_retries,
            remove_section_headers=True,
            skip_non_songs=True,
            excluded_terms=["(Remix)", "(Live)", "(Acoustic)"],
        )

        # Disable verbose output
        self.genius.verbose = False

        # Statistics
        self.stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'instrumental': 0,
            'too_short': 0,
            'api_errors': 0,
        }

    def validate_lyrics(self, lyrics: str, min_words: int = 50) -> Tuple[bool, str]:
        """
        Validate that lyrics are legitimate

        Args:
            lyrics: Lyrics text
            min_words: Minimum word count for valid lyrics

        Returns:
            (is_valid, reason)
        """
        if not lyrics or len(lyrics.strip()) == 0:
            return False, "empty"

        # Check for instrumental markers
        instrumental_markers = [
            'instrumental',
            'no lyrics',
            'this song is an instrumental',
            '[instrumental]',
        ]

        lyrics_lower = lyrics.lower()
        for marker in instrumental_markers:
            if marker in lyrics_lower:
                return False, "instrumental"

        # Count words (split by whitespace)
        word_count = len(lyrics.split())
        if word_count < min_words:
            return False, f"too_short ({word_count} words)"

        return True, "valid"

    def fetch_with_validation(
        self,
        song_name: str,
        artist_name: str,
        min_words: int = 50
    ) -> Optional[str]:
        """
        Fetch lyrics and validate they're legitimate

        Args:
            song_name: Song title
            artist_name: Artist name
            min_words: Minimum word count

        Returns:
            Cleaned lyrics text if valid, None otherwise
        """
        self.stats['attempted'] += 1

        try:
            # Search for song
            song = self.genius.search_song(
                title=song_name,
                artist=artist_name,
                get_full_info=False
            )

            if not song:
                self.stats['failed'] += 1
                return None

            # Get lyrics
            lyrics = song.lyrics

            # Clean up Genius formatting
            lyrics = self._clean_lyrics(lyrics)

            # Validate
            is_valid, reason = self.validate_lyrics(lyrics, min_words)

            if is_valid:
                self.stats['successful'] += 1
                return lyrics
            else:
                if 'instrumental' in reason:
                    self.stats['instrumental'] += 1
                elif 'too_short' in reason:
                    self.stats['too_short'] += 1
                else:
                    self.stats['failed'] += 1
                return None

        except Exception as e:
            self.stats['api_errors'] += 1
            return None

    def _clean_lyrics(self, lyrics: str) -> str:
        """Clean Genius-specific formatting from lyrics"""
        if not lyrics:
            return ""

        # Remove embed tags
        lyrics = lyrics.replace('EmbedShare URLCopyEmbedCopy', '')

        # Remove "X Lyrics" header that Genius adds
        lines = lyrics.split('\n')
        if lines and 'Lyrics' in lines[0]:
            lines = lines[1:]

        # Remove contributor info at the end
        if lines and 'Embed' in lines[-1]:
            lines = lines[:-1]

        # Rejoin and clean
        lyrics = '\n'.join(lines)
        lyrics = lyrics.strip()

        return lyrics

    def collect_lyrics_for_songs(
        self,
        songs: List[Dict],
        min_words: int = 50,
        rate_limit_delay: float = 0.5
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Collect lyrics for a list of songs, filtering out those without lyrics

        Args:
            songs: List of song dictionaries (must have 'name' and 'artist')
            min_words: Minimum word count for valid lyrics
            rate_limit_delay: Delay between API calls (seconds)

        Returns:
            (songs_with_lyrics, songs_without_lyrics)
        """
        print(f"\nCollecting lyrics for {len(songs)} songs...")
        print(f"Validation: Minimum {min_words} words")

        songs_with_lyrics = []
        songs_without_lyrics = []

        for song in tqdm(songs, desc="Fetching lyrics"):
            # Fetch and validate lyrics
            lyrics = self.fetch_with_validation(
                song_name=song['name'],
                artist_name=song['artist'],
                min_words=min_words
            )

            if lyrics:
                # Add lyrics to song
                song['lyrics'] = lyrics
                songs_with_lyrics.append(song)
            else:
                songs_without_lyrics.append(song)

            # Rate limiting
            time.sleep(rate_limit_delay)

        # Print statistics
        self._print_stats(len(songs))

        return songs_with_lyrics, songs_without_lyrics

    def _print_stats(self, total: int):
        """Print collection statistics"""
        print("\n" + "="*60)
        print("LYRICS COLLECTION STATISTICS")
        print("="*60)

        print(f"\nTotal songs processed: {total}")
        print(f"\n✓ Successful: {self.stats['successful']} ({self.stats['successful']/total*100:.1f}%)")
        print(f"✗ Failed: {self.stats['failed']} ({self.stats['failed']/total*100:.1f}%)")
        print(f"  - Instrumental: {self.stats['instrumental']}")
        print(f"  - Too short: {self.stats['too_short']}")
        print(f"  - API errors: {self.stats['api_errors']}")

        if self.stats['successful'] > 0:
            print(f"\n✓ Lyrics success rate: {self.stats['successful']/total*100:.1f}%")

    def get_stats(self) -> Dict:
        """Get collection statistics"""
        return self.stats.copy()


def test_smart_lyrics_collector():
    """Test the smart lyrics collector"""
    print("="*60)
    print("SMART LYRICS COLLECTOR TEST")
    print("="*60)

    collector = SmartLyricsCollector()

    # Test songs (mix of songs with/without lyrics)
    test_songs = [
        {'name': 'Blinding Lights', 'artist': 'The Weeknd', 'genre': 'pop'},
        {'name': 'Bohemian Rhapsody', 'artist': 'Queen', 'genre': 'rock'},
        {'name': 'HUMBLE.', 'artist': 'Kendrick Lamar', 'genre': 'hip-hop'},
    ]

    # Collect lyrics
    with_lyrics, without_lyrics = collector.collect_lyrics_for_songs(
        test_songs,
        min_words=50
    )

    print(f"\n\n{'='*60}")
    print("RESULTS")
    print("="*60)
    print(f"\nSongs with lyrics: {len(with_lyrics)}")
    print(f"Songs without lyrics: {len(without_lyrics)}")

    if with_lyrics:
        print(f"\nSample song with lyrics:")
        sample = with_lyrics[0]
        print(f"  Name: {sample['name']}")
        print(f"  Artist: {sample['artist']}")
        print(f"  Lyrics preview: {sample['lyrics'][:200]}...")


if __name__ == '__main__':
    test_smart_lyrics_collector()
