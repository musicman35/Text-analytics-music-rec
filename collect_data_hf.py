"""
Data Collection using Hugging Face Dataset + Genius Lyrics
Strategy: Use HF for songs with audio features, then filter by lyrics availability
"""

import argparse
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from src.data_collection.huggingface_collector import HuggingFaceCollector
from src.data_collection.smart_lyrics_collector import SmartLyricsCollector
from src.database.sqlite_manager import SQLiteManager
from src.database.qdrant_manager import QdrantManager


def collect_songs_with_lyrics(
    genres: list,
    songs_per_genre: int = 1000,
    min_lyric_words: int = 50,
    target_with_lyrics: int = None
):
    """
    Collect songs from Hugging Face and filter by lyrics availability

    Strategy:
    1. Load songs from Hugging Face (has audio features)
    2. Attempt to fetch lyrics from Genius
    3. Only keep songs with valid lyrics
    4. Continue until we have enough songs with lyrics per genre

    Args:
        genres: List of genres to collect
        songs_per_genre: Target number of songs WITH lyrics per genre
        min_lyric_words: Minimum words for valid lyrics
        target_with_lyrics: Total target (if None, uses songs_per_genre * len(genres))
    """
    print("="*60)
    print("HUGGING FACE + GENIUS DATA COLLECTION")
    print("="*60)

    if target_with_lyrics is None:
        target_with_lyrics = songs_per_genre * len(genres)

    print(f"\nTarget: {songs_per_genre} songs with lyrics per genre")
    print(f"Total target: {target_with_lyrics} songs")
    print(f"Genres: {', '.join(genres)}")
    print(f"Lyrics validation: Minimum {min_lyric_words} words")

    # Initialize collectors
    print("\n" + "="*60)
    print("STEP 1: Loading Hugging Face Dataset")
    print("="*60)

    hf_collector = HuggingFaceCollector()

    # Strategy: Collect MORE songs than needed (assume ~60% will have lyrics)
    # If we want 1000 songs with lyrics, collect ~1700 songs from HF
    oversample_factor = 1.7
    songs_to_fetch = int(songs_per_genre * oversample_factor)

    print(f"\nFetching {songs_to_fetch} songs per genre from Hugging Face")
    print("(Oversampling to account for lyrics availability)")

    songs = hf_collector.collect_songs(
        genres=genres,
        songs_per_genre=songs_to_fetch
    )

    print(f"\n✓ Loaded {len(songs)} songs from Hugging Face")

    # Collect lyrics
    print("\n" + "="*60)
    print("STEP 2: Fetching and Validating Lyrics from Genius")
    print("="*60)

    lyrics_collector = SmartLyricsCollector()

    songs_with_lyrics, songs_without_lyrics = lyrics_collector.collect_lyrics_for_songs(
        songs=songs,
        min_words=min_lyric_words,
        rate_limit_delay=0.5  # Be nice to Genius API
    )

    print(f"\n✓ Successfully collected lyrics for {len(songs_with_lyrics)} songs")
    print(f"✗ Failed to get lyrics for {len(songs_without_lyrics)} songs")

    # Check if we have enough
    if len(songs_with_lyrics) < target_with_lyrics:
        print(f"\n⚠️  Warning: Only got {len(songs_with_lyrics)}/{target_with_lyrics} songs with lyrics")
        print("Consider:")
        print("  1. Increasing oversample_factor")
        print("  2. Lowering min_lyric_words threshold")
        print("  3. Adding more genres")

    # Balance by genre
    print("\n" + "="*60)
    print("STEP 3: Balancing Songs by Genre")
    print("="*60)

    balanced_songs = balance_songs_by_genre(
        songs_with_lyrics,
        genres,
        songs_per_genre
    )

    print(f"\n✓ Final dataset: {len(balanced_songs)} songs")

    # Save to databases
    print("\n" + "="*60)
    print("STEP 4: Saving to Databases")
    print("="*60)

    save_to_databases(balanced_songs)

    # Summary
    print("\n" + "="*60)
    print("DATA COLLECTION COMPLETE")
    print("="*60)

    print(f"\n✓ Total songs collected: {len(balanced_songs)}")
    print(f"✓ All songs have audio features from Hugging Face")
    print(f"✓ All songs have validated lyrics from Genius")
    print("\nBreakdown by genre:")
    for genre in genres:
        count = len([s for s in balanced_songs if s['genre'].lower() == genre.lower()])
        print(f"  {genre}: {count} songs")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("\n1. Run the Streamlit app:")
    print("   streamlit run streamlit_app.py")
    print("\n2. Or use the Flask API:")
    print("   python src/api/flask_app.py")
    print("="*60)


def balance_songs_by_genre(songs: list, genres: list, songs_per_genre: int) -> list:
    """
    Balance the dataset to have equal songs per genre

    Args:
        songs: List of songs with lyrics
        genres: Target genres
        songs_per_genre: Target count per genre

    Returns:
        Balanced list of songs
    """
    import random

    balanced = []

    for genre in genres:
        # Get all songs for this genre
        genre_songs = [s for s in songs if genre.lower() in s['genre'].lower()]

        # Sample or take all
        if len(genre_songs) >= songs_per_genre:
            sampled = random.sample(genre_songs, songs_per_genre)
        else:
            sampled = genre_songs
            print(f"  ⚠️  {genre}: Only {len(genre_songs)}/{songs_per_genre} songs available")

        balanced.extend(sampled)
        print(f"  {genre}: {len(sampled)} songs")

    return balanced


def save_to_databases(songs: list):
    """Save songs to SQLite and Qdrant"""

    # Initialize database managers
    db = SQLiteManager()
    qdrant = QdrantManager()

    print("\nSaving to SQLite...")
    saved_count = 0

    for song in songs:
        try:
            song_id = db.add_song(
                spotify_id=song.get('spotify_id', ''),
                name=song['name'],
                artist=song['artist'],
                features=song['features'],
                album=song.get('album', ''),
                genre=song['genre'],
                lyrics=song.get('lyrics', ''),
            )
            saved_count += 1
        except Exception as e:
            print(f"  ✗ Error saving {song['name']}: {e}")

    print(f"✓ Saved {saved_count} songs to SQLite")

    # Save to Qdrant
    print("\nSaving to Qdrant (vector database)...")

    try:
        qdrant.add_songs(songs)
        print(f"✓ Saved {len(songs)} songs to Qdrant")
    except Exception as e:
        print(f"✗ Error saving to Qdrant: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Collect music data from Hugging Face + Genius')

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test with 20 songs per genre'
    )

    parser.add_argument(
        '--medium',
        action='store_true',
        help='Medium test with 100 songs per genre'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Full collection with 1000 songs per genre'
    )

    parser.add_argument(
        '--genres',
        nargs='+',
        default=['pop', 'rock', 'hip-hop', 'electronic', 'r&b'],
        help='Genres to collect (default: pop rock hip-hop electronic r&b)'
    )

    args = parser.parse_args()

    # Determine songs per genre
    if args.quick:
        songs_per_genre = 20
    elif args.medium:
        songs_per_genre = 100
    elif args.full:
        songs_per_genre = 1000
    else:
        # Default to medium
        print("No mode specified. Using --medium (100 songs per genre)")
        print("Use --quick, --medium, or --full")
        songs_per_genre = 100

    # Run collection
    try:
        collect_songs_with_lyrics(
            genres=args.genres,
            songs_per_genre=songs_per_genre,
            min_lyric_words=50
        )
    except KeyboardInterrupt:
        print("\n\n✗ Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error during collection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
