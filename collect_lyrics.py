"""
Lyrics Collection Script
Collects songs WITH lyrics from Genius API and stores in Qdrant

This script:
1. Collects songs from HuggingFace dataset
2. Fetches lyrics from Genius API for each song
3. Stores songs with lyrics in Qdrant for semantic search

Note: Lyrics fetching is rate-limited (~1-2 songs/second)
      For 500 songs, expect ~10-15 minutes
"""

import argparse
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from src.data_collection.huggingface_collector import HuggingFaceCollector
from src.database.qdrant_storage import QdrantStorage


def estimate_time(song_count: int) -> str:
    """Estimate time for lyrics collection"""
    # ~1.5 seconds per song on average (API call + rate limit)
    seconds = song_count * 1.5
    if seconds < 60:
        return f"~{int(seconds)} seconds"
    elif seconds < 3600:
        return f"~{int(seconds/60)} minutes"
    else:
        return f"~{seconds/3600:.1f} hours"


def save_progress(songs: list, progress_file: Path):
    """Save progress to a file for resuming"""
    with open(progress_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'count': len(songs),
            'songs': songs
        }, f)
    print(f"  Progress saved to {progress_file}")


def load_progress(progress_file: Path) -> list:
    """Load progress from file"""
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            data = json.load(f)
            print(f"  Loaded {data['count']} songs from {progress_file}")
            return data['songs']
    return []


def collect_with_lyrics(
    genres: list,
    songs_per_genre: int = 100,
    save_progress_every: int = 50,
    resume: bool = True,
    skip_confirm: bool = False,
    append_mode: bool = False
):
    """
    Collect songs WITH lyrics and store in Qdrant

    Args:
        genres: List of genres to collect
        songs_per_genre: Number of songs per genre
        save_progress_every: Save progress after this many songs
        resume: Whether to resume from previous progress
    """
    print("=" * 60)
    print("LYRICS COLLECTION")
    print("=" * 60)

    total_songs = len(genres) * songs_per_genre
    print(f"\nTarget: {songs_per_genre} songs per genre")
    print(f"Genres: {', '.join(genres)}")
    print(f"Total songs: {total_songs}")
    print(f"Estimated time: {estimate_time(total_songs)}")
    print()

    # Progress file
    progress_dir = Path("data/cache")
    progress_dir.mkdir(parents=True, exist_ok=True)
    progress_file = progress_dir / "lyrics_collection_progress.json"

    # Check for existing progress
    all_songs = []
    if resume and progress_file.exists():
        all_songs = load_progress(progress_file)
        if all_songs:
            print(f"\nResuming from {len(all_songs)} previously collected songs")
            # Calculate what we still need
            collected_genres = set(s.get('genre', '').lower() for s in all_songs)
            print(f"Already have songs from: {collected_genres}")

    # Initialize collector WITH lyrics
    print("\nInitializing collectors...")
    try:
        hf_collector = HuggingFaceCollector(fetch_lyrics=True)
    except Exception as e:
        print(f"\n✗ Error initializing lyrics fetcher: {e}")
        print("\nMake sure you have:")
        print("1. Installed lyricsgenius: pip install lyricsgenius")
        print("2. Set GENIUS_API_KEY in your .env file")
        print("   Get a free key at: https://genius.com/api-clients")
        sys.exit(1)

    # Collect songs per genre
    for genre in genres:
        # Check if we already have enough for this genre
        existing_count = len([s for s in all_songs if genre.lower() in s.get('genre', '').lower()])
        if existing_count >= songs_per_genre:
            print(f"\n✓ Already have {existing_count} songs for {genre}, skipping...")
            continue

        needed = songs_per_genre - existing_count
        print(f"\n{'=' * 60}")
        print(f"Collecting {needed} songs for: {genre.upper()}")
        print(f"{'=' * 60}")
        print(f"Estimated time: {estimate_time(needed)}")

        try:
            genre_songs = hf_collector.collect_songs(
                genres=[genre],
                songs_per_genre=needed
            )

            all_songs.extend(genre_songs)

            # Save progress
            save_progress(all_songs, progress_file)

            # Stats for this genre
            with_lyrics = len([s for s in genre_songs if s.get('lyrics_preview')])
            print(f"\n✓ {genre}: {len(genre_songs)} songs collected, {with_lyrics} with lyrics")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted! Saving progress...")
            save_progress(all_songs, progress_file)
            print(f"Progress saved. Run again with --resume to continue.")
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ Error collecting {genre}: {e}")
            save_progress(all_songs, progress_file)
            continue

    # Summary of lyrics coverage
    print("\n" + "=" * 60)
    print("LYRICS COVERAGE SUMMARY")
    print("=" * 60)

    total = len(all_songs)
    with_lyrics = len([s for s in all_songs if s.get('lyrics_preview')])
    print(f"\nTotal songs: {total}")
    print(f"With lyrics: {with_lyrics} ({with_lyrics/total*100:.1f}%)")
    print(f"Without lyrics: {total - with_lyrics}")

    print("\nBy genre:")
    for genre in genres:
        genre_songs = [s for s in all_songs if genre.lower() in s.get('genre', '').lower()]
        genre_with_lyrics = len([s for s in genre_songs if s.get('lyrics_preview')])
        print(f"  {genre}: {genre_with_lyrics}/{len(genre_songs)} with lyrics")

    # Store in Qdrant
    print("\n" + "=" * 60)
    print("SAVING TO QDRANT")
    print("=" * 60)

    try:
        storage = QdrantStorage()

        # Clear existing data if starting fresh (unless append mode)
        existing_count = storage.get_song_count()
        if existing_count > 0:
            print(f"\nExisting songs in Qdrant: {existing_count}")
            if append_mode:
                print("✓ Append mode: keeping existing data")
            elif skip_confirm:
                storage.clear_all_data()
                print("✓ Cleared existing data (--yes flag)")
            else:
                response = input("Clear existing data and replace? (y/n): ")
                if response.lower() == 'y':
                    storage.clear_all_data()
                    print("✓ Cleared existing data")

        # Add all songs (including lyrics in embeddings)
        print(f"\nUploading {len(all_songs)} songs to Qdrant...")
        storage.add_songs(all_songs)

        # Verify
        final_count = storage.get_song_count()
        print(f"\n✓ Verified: {final_count} songs in Qdrant")

    except Exception as e:
        print(f"\n✗ Error saving to Qdrant: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Clean up progress file
    if progress_file.exists():
        progress_file.unlink()
        print("✓ Cleaned up progress file")

    # Final summary
    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print("=" * 60)
    print(f"\n✓ {total} songs collected")
    print(f"✓ {with_lyrics} songs with lyrics ({with_lyrics/total*100:.1f}%)")
    print(f"✓ Lyrics embedded in Qdrant for semantic search")
    print("\nYour recommendation system can now:")
    print("  - Search by lyrical themes ('songs about heartbreak')")
    print("  - Match mood based on lyrics + audio features")
    print("  - Provide richer, more relevant recommendations")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Collect music data WITH lyrics to Qdrant'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test: 10 songs per genre (~1 min)'
    )

    parser.add_argument(
        '--small',
        action='store_true',
        help='Small: 50 songs per genre (~5 min)'
    )

    parser.add_argument(
        '--medium',
        action='store_true',
        help='Medium: 100 songs per genre (~10 min)'
    )

    parser.add_argument(
        '--large',
        action='store_true',
        help='Large: 200 songs per genre (~20 min)'
    )

    parser.add_argument(
        '--genres',
        nargs='+',
        default=['pop', 'rock', 'hip-hop', 'r&b', 'electronic'],
        help='Genres to collect (default: pop rock hip-hop r&b electronic)'
    )

    parser.add_argument(
        '--songs-per-genre',
        type=int,
        help='Custom number of songs per genre'
    )

    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Start fresh, ignore previous progress'
    )

    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Skip confirmation prompts'
    )

    parser.add_argument(
        '--append',
        action='store_true',
        help='Append to existing data instead of clearing'
    )

    args = parser.parse_args()

    # Determine count
    if args.songs_per_genre:
        songs_per_genre = args.songs_per_genre
    elif args.quick:
        songs_per_genre = 10
    elif args.small:
        songs_per_genre = 50
    elif args.medium:
        songs_per_genre = 100
    elif args.large:
        songs_per_genre = 200
    else:
        print("No mode specified. Use --quick, --small, --medium, or --large")
        print("Example: python collect_lyrics.py --medium")
        print("\nEstimated times:")
        print("  --quick  (10/genre):  ~1 minute")
        print("  --small  (50/genre):  ~5 minutes")
        print("  --medium (100/genre): ~10 minutes")
        print("  --large  (200/genre): ~20 minutes")
        sys.exit(0)

    # Verify Genius API key
    genius_key = os.getenv("GENIUS_API_KEY", "")
    if not genius_key or genius_key == "your_genius_api_key":
        print("\n" + "=" * 60)
        print("✗ GENIUS_API_KEY not configured!")
        print("=" * 60)
        print("\nTo use lyrics collection:")
        print("1. Go to: https://genius.com/api-clients")
        print("2. Create a free account and generate an API token")
        print("3. Add to your .env file:")
        print("   GENIUS_API_KEY=your_token_here")
        sys.exit(1)

    print(f"\n✓ Genius API key configured")

    # Verify Qdrant config
    use_cloud = os.getenv("QDRANT_USE_CLOUD", "false").lower() == "true"
    if use_cloud:
        print(f"✓ Using Qdrant Cloud")
    else:
        print(f"✓ Using local Qdrant")

    # Confirmation
    total = len(args.genres) * songs_per_genre
    print(f"\nWill collect {total} songs ({songs_per_genre} per genre)")
    print(f"Estimated time: {estimate_time(total)}")

    if not args.yes:
        response = input("\nProceed? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    else:
        print("\nStarting collection (--yes flag provided)...")

    # Run collection
    try:
        collect_with_lyrics(
            genres=args.genres,
            songs_per_genre=songs_per_genre,
            resume=not args.no_resume,
            skip_confirm=args.yes,
            append_mode=args.append
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
