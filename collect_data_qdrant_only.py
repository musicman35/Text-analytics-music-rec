"""
Qdrant-Only Data Collection
Collects and stores ALL data in Qdrant Cloud
No lyrics functionality - uses audio features only
"""

import argparse
import sys
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from src.data_collection.huggingface_collector import HuggingFaceCollector
from src.database.qdrant_storage import QdrantStorage


def collect_genre(
    hf_collector: HuggingFaceCollector,
    genre: str,
    target_count: int,
    max_attempts: int = 5
) -> list:
    """Collect songs for a single genre using audio features only"""
    print(f"\n{'='*60}")
    print(f"Collecting {target_count} songs for: {genre.upper()}")
    print(f"{'='*60}")

    collected_songs = []

    for attempt in range(1, max_attempts + 1):
        needed = target_count - len(collected_songs)

        if needed <= 0:
            print(f"✓ Target reached: {len(collected_songs)}/{target_count} songs")
            break

        # Fetch more songs to account for duplicates
        fetch_count = int(needed * 1.2)

        print(f"\nAttempt {attempt}/{max_attempts}: Need {needed} more songs, fetching {fetch_count}...")

        # Fetch from Hugging Face
        hf_songs = hf_collector.collect_songs(
            genres=[genre],
            songs_per_genre=fetch_count
        )

        if not hf_songs:
            print(f"⚠️  No songs available for {genre}")
            break

        # Add songs (no lyrics processing needed)
        collected_songs.extend(hf_songs)
        print(f"  Got {len(hf_songs)} songs from dataset")
        print(f"  Progress: {len(collected_songs)}/{target_count} songs")

    # Sample down if needed
    if len(collected_songs) > target_count:
        import random
        collected_songs = random.sample(collected_songs, target_count)
        print(f"✓ Sampled down to {target_count} songs")

    if len(collected_songs) < target_count:
        print(f"⚠️  Only collected {len(collected_songs)}/{target_count} songs")
    else:
        print(f"✓ Successfully collected {len(collected_songs)}/{target_count} songs")

    return collected_songs


def collect_to_qdrant(
    genres: list,
    songs_per_genre: int = 100
):
    """
    Collect dataset and store ONLY in Qdrant Cloud
    Uses audio features only - no lyrics
    """
    print("="*60)
    print("QDRANT-ONLY DATA COLLECTION (NO LYRICS)")
    print("="*60)

    print(f"\nTarget: {songs_per_genre} songs per genre")
    print(f"Genres: {', '.join(genres)}")
    print(f"Storage: Qdrant Cloud (audio features only)")

    # Initialize collectors
    hf_collector = HuggingFaceCollector()

    # Collect per-genre
    all_songs = []

    for genre in genres:
        genre_songs = collect_genre(
            hf_collector=hf_collector,
            genre=genre,
            target_count=songs_per_genre,
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
    print(f"✓ Using audio features only (no lyrics)")
    print(f"✓ Ready for deployment!")

    print("\nDistribution by Genre:")
    for genre in genres:
        count = len([s for s in all_songs if genre.lower() in s['genre'].lower()])
        print(f"  {genre}: {count} songs")

    print("\n" + "="*60)
    print("DEPLOYMENT READY")
    print("="*60)
    print("\nYour app can now be deployed:")
    print("1. Push to GitHub: git add . && git commit -m 'Data in Qdrant' && git push")
    print("2. Deploy on Streamlit Cloud")
    print("3. Add API keys to Secrets")
    print("4. Launch!")
    print("\nNo lyrics API needed - using audio features only! 🚀")
    print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Collect music data to Qdrant Cloud (audio features only)'
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
        print("\nContinuing anyway (will use configured Qdrant)...")
        print("="*60 + "\n")

        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Aborted. Please configure Qdrant Cloud first.")
            sys.exit(0)

    # Run collection
    try:
        collect_to_qdrant(
            genres=args.genres,
            songs_per_genre=songs_per_genre
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