"""
Qdrant-Only Data Collection
Collects and stores ALL data in Qdrant Cloud
Perfect for Streamlit deployment - no SQLite needed!
"""

import argparse
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from src.data_collection.huggingface_collector import HuggingFaceCollector
from src.data_collection.smart_lyrics_collector import SmartLyricsCollector
from src.database.qdrant_storage import QdrantStorage


def collect_genre_with_lyrics(
    hf_collector: HuggingFaceCollector,
    lyrics_collector: SmartLyricsCollector,
    genre: str,
    target_count: int,
    min_lyric_words: int = 50,
    max_attempts: int = 5
) -> list:
    """Collect exactly target_count songs with lyrics for a single genre"""
    print(f"\n{'='*60}")
    print(f"Collecting {target_count} songs for: {genre.upper()}")
    print(f"{'='*60}")

    songs_with_lyrics = []

    for attempt in range(1, max_attempts + 1):
        needed = target_count - len(songs_with_lyrics)

        if needed <= 0:
            print(f"✓ Target reached: {len(songs_with_lyrics)}/{target_count} songs")
            break

        oversample_factor = 1.5 + (attempt * 0.3)
        fetch_count = int(needed * oversample_factor)

        print(f"\nAttempt {attempt}/{max_attempts}: Need {needed} more songs, fetching {fetch_count}...")

        # Fetch from Hugging Face
        hf_songs = hf_collector.collect_songs(
            genres=[genre],
            songs_per_genre=fetch_count
        )

        if not hf_songs:
            print(f"⚠️  No songs available for {genre}")
            break

        # Fetch lyrics
        with_lyrics, _ = lyrics_collector.collect_lyrics_for_songs(
            songs=hf_songs,
            min_words=min_lyric_words,
            rate_limit_delay=0.5
        )

        songs_with_lyrics.extend(with_lyrics)

        success_rate = len(with_lyrics) / len(hf_songs) * 100 if hf_songs else 0
        print(f"  Got {len(with_lyrics)}/{len(hf_songs)} with lyrics ({success_rate:.1f}% success)")
        print(f"  Progress: {len(songs_with_lyrics)}/{target_count} songs")

    # Sample down if needed
    if len(songs_with_lyrics) > target_count:
        import random
        songs_with_lyrics = random.sample(songs_with_lyrics, target_count)
        print(f"✓ Sampled down to {target_count} songs")

    if len(songs_with_lyrics) < target_count:
        print(f"⚠️  Only collected {len(songs_with_lyrics)}/{target_count} songs")
    else:
        print(f"✓ Successfully collected {len(songs_with_lyrics)}/{target_count} songs")

    return songs_with_lyrics


def collect_to_qdrant(
    genres: list,
    songs_per_genre: int = 1000,
    min_lyric_words: int = 50
):
    """
    Collect balanced dataset and store ONLY in Qdrant Cloud

    No SQLite, no local files - perfect for deployment!
    """
    print("="*60)
    print("QDRANT-ONLY DATA COLLECTION")
    print("="*60)

    print(f"\nTarget: {songs_per_genre} songs per genre")
    print(f"Genres: {', '.join(genres)}")
    print(f"Storage: Qdrant Cloud ONLY (no local database)")

    # Initialize collectors
    hf_collector = HuggingFaceCollector()
    lyrics_collector = SmartLyricsCollector()

    # Collect per-genre
    all_songs = []

    for genre in genres:
        genre_songs = collect_genre_with_lyrics(
            hf_collector=hf_collector,
            lyrics_collector=lyrics_collector,
            genre=genre,
            target_count=songs_per_genre,
            min_lyric_words=min_lyric_words,
            max_attempts=5
        )

        all_songs.extend(genre_songs)

    # Save to Qdrant ONLY
    print("\n" + "="*60)
    print("SAVING TO QDRANT CLOUD")
    print("="*60)

    try:
        storage = QdrantStorage()

        # Add all songs
        storage.add_songs(all_songs)

        # Verify
        count = storage.get_song_count()
        print(f"\n✓ Verified: {count} songs in Qdrant")

    except Exception as e:
        print(f"✗ Error saving to Qdrant: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final summary
    print("\n" + "="*60)
    print("DATA COLLECTION COMPLETE")
    print("="*60)

    print(f"\n✓ Total songs: {len(all_songs)}")
    print(f"✓ All data stored in Qdrant Cloud")
    print(f"✓ No local database files")
    print(f"✓ Ready for Streamlit deployment!")

    print("\nDistribution by Genre:")
    for genre in genres:
        count = len([s for s in all_songs if genre.lower() in s['genre'].lower()])
        print(f"  {genre}: {count} songs")

    print("\n" + "="*60)
    print("DEPLOYMENT READY")
    print("="*60)
    print("\nYour app can now be deployed to Streamlit Cloud:")
    print("1. Push to GitHub: git add . && git commit -m 'Data in Qdrant' && git push")
    print("2. Deploy on Streamlit Cloud")
    print("3. Add API keys to Secrets")
    print("4. Launch!")
    print("\nNo database files to upload - everything is in Qdrant Cloud! 🚀")
    print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Collect music data to Qdrant Cloud (deployment-ready)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test: 20 songs per genre'
    )

    parser.add_argument(
        '--medium',
        action='store_true',
        help='Medium: 100 songs per genre (recommended for demo)'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Full: 1000 songs per genre'
    )

    parser.add_argument(
        '--genres',
        nargs='+',
        default=['pop', 'rock', 'hip-hop', 'electronic', 'r&b'],
        help='Genres to collect'
    )

    parser.add_argument(
        '--songs-per-genre',
        type=int,
        help='Custom number of songs per genre'
    )

    args = parser.parse_args()

    # Determine count
    if args.songs_per_genre:
        songs_per_genre = args.songs_per_genre
    elif args.quick:
        songs_per_genre = 20
    elif args.medium:
        songs_per_genre = 100
    elif args.full:
        songs_per_genre = 1000
    else:
        print("No mode specified. Using --medium (100 songs per genre)")
        print("Use --quick, --medium, or --full")
        songs_per_genre = 100

    # Verify Qdrant Cloud config
    import os
    use_cloud = os.getenv("QDRANT_USE_CLOUD", "false").lower() == "true"
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")

    if not use_cloud or qdrant_host == "localhost":
        print("\n" + "="*60)
        print("⚠️  WARNING: Qdrant Cloud not configured!")
        print("="*60)
        print("\nFor deployment, you need Qdrant Cloud:")
        print("1. Go to: https://cloud.qdrant.io")
        print("2. Create free cluster")
        print("3. Update .env:")
        print("   QDRANT_HOST=your-cluster.qdrant.io")
        print("   QDRANT_API_KEY=your_api_key")
        print("   QDRANT_USE_CLOUD=true")
        print("\nContinuing anyway (will use local Qdrant)...")
        print("="*60 + "\n")

        response = input("Continue with local Qdrant? (y/n): ")
        if response.lower() != 'y':
            print("Aborted. Please configure Qdrant Cloud first.")
            sys.exit(0)

    # Run collection
    try:
        collect_to_qdrant(
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
