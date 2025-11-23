"""
Data Collection Runner Script
Orchestrates the complete data collection and setup process
"""

import argparse
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.data_collection.spotify_collector import SpotifyCollector
from src.data_collection.lyrics_collector import LyricsCollector
from src.database.qdrant_manager import QdrantManager
from src.database.sqlite_manager import SQLiteManager


def setup_database():
    """Initialize SQLite database"""
    print("\n" + "="*80)
    print("STEP 1: Setting up SQLite Database")
    print("="*80)

    db = SQLiteManager()
    print("✓ Database initialized")


def collect_spotify_data(use_cache=True, limit_per_genre=None):
    """Collect songs from Spotify"""
    print("\n" + "="*80)
    print("STEP 2: Collecting Spotify Data")
    print("="*80)

    collector = SpotifyCollector()

    # Override limit if specified
    if limit_per_genre:
        import config
        config.TARGET_SONGS_PER_GENRE = limit_per_genre

    songs = collector.run_collection(use_cache=use_cache, save_to_db=True)

    print(f"\n✓ Collected {len(songs)} songs from Spotify")
    return songs


def collect_lyrics_data(use_cache=True):
    """Collect lyrics from Genius"""
    print("\n" + "="*80)
    print("STEP 3: Collecting Lyrics Data")
    print("="*80)

    collector = LyricsCollector()
    songs = collector.run_collection(use_cache=use_cache, save_to_db=True)

    lyrics_count = sum(1 for s in songs if s.get('lyrics'))
    print(f"\n✓ Collected lyrics for {lyrics_count}/{len(songs)} songs")

    return songs


def setup_qdrant(limit=None):
    """Setup Qdrant vector database"""
    print("\n" + "="*80)
    print("STEP 4: Setting up Qdrant Vector Database")
    print("="*80)

    manager = QdrantManager()

    # Create collection
    manager.create_collection(delete_existing=True)
    print("✓ Created Qdrant collection")

    # Populate from database
    manager.populate_from_database(limit=limit)
    print("✓ Populated Qdrant with embeddings")

    # Show info
    info = manager.get_collection_info()
    print(f"\nCollection Info: {info}")


def main():
    parser = argparse.ArgumentParser(
        description="Data Collection Runner for Music Recommendation System"
    )

    parser.add_argument(
        '--step',
        choices=['all', 'db', 'spotify', 'lyrics', 'qdrant'],
        default='all',
        help='Which step to run (default: all)'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching (fetch fresh data)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of songs per genre (for testing)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test mode (100 songs total)'
    )

    args = parser.parse_args()

    use_cache = not args.no_cache
    limit_per_genre = args.limit

    # Quick mode: 20 songs per genre = 100 total
    if args.quick:
        limit_per_genre = 20
        print("\n🚀 QUICK MODE: Collecting 100 songs for testing\n")

    print("\n" + "="*80)
    print("MUSIC RECOMMENDATION SYSTEM - DATA COLLECTION")
    print("="*80)

    try:
        if args.step in ['all', 'db']:
            setup_database()

        if args.step in ['all', 'spotify']:
            collect_spotify_data(use_cache=use_cache, limit_per_genre=limit_per_genre)

        if args.step in ['all', 'lyrics']:
            collect_lyrics_data(use_cache=use_cache)

        if args.step in ['all', 'qdrant']:
            setup_qdrant(limit=None)

        print("\n" + "="*80)
        print("✓ DATA COLLECTION COMPLETE!")
        print("="*80)

        # Show summary
        db = SQLiteManager()
        total_songs = db.get_songs_count()

        print(f"\nDatabase Summary:")
        print(f"  Total songs: {total_songs}")

        print("\nNext steps:")
        print("  1. Start the Streamlit app: streamlit run streamlit_app.py")
        print("  2. Or start the Flask API: python src/api/flask_app.py")
        print("  3. Create a user and start getting recommendations!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Error during collection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
