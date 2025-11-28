"""
Lyrics Enrichment Script
Fetches lyrics for ALL existing songs in Qdrant database

This script:
1. Reads all songs from Qdrant
2. Fetches lyrics from Genius API for songs without lyrics
3. Updates songs in Qdrant with new embeddings that include lyrics

Features:
- Resumable: saves progress and can continue from where it left off
- Batch processing: updates Qdrant in batches for efficiency
- Progress tracking: shows estimated time remaining

Note: At ~1.5 seconds per song, 11,000 songs takes ~4.5 hours
      Run with: python enrich_lyrics.py --start
"""

import argparse
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tqdm import tqdm
import time

load_dotenv()

from src.data_collection.lyrics_fetcher import LyricsFetcher
from src.database.qdrant_storage import QdrantStorage
from qdrant_client.models import PointStruct


class LyricsEnricher:
    """Enriches existing Qdrant songs with lyrics"""

    def __init__(self):
        self.storage = QdrantStorage()
        self.lyrics_fetcher = LyricsFetcher()

        # Progress tracking
        self.progress_dir = Path("data/cache")
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.progress_dir / "lyrics_enrichment_progress.json"

        # Stats
        self.stats = {
            "total_songs": 0,
            "processed": 0,
            "lyrics_found": 0,
            "lyrics_not_found": 0,
            "already_had_lyrics": 0,
            "errors": 0,
            "start_time": None,
        }

    def load_progress(self) -> set:
        """Load set of already processed song IDs"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self.stats = data.get('stats', self.stats)
                return set(data.get('processed_ids', []))
        return set()

    def save_progress(self, processed_ids: set):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats,
                'processed_ids': list(processed_ids)
            }, f)

    def get_all_songs(self) -> list:
        """Retrieve all songs from Qdrant"""
        print("Retrieving all songs from Qdrant...")

        all_songs = []
        offset = None
        batch_size = 100

        while True:
            # Scroll through all songs
            results, offset = self.storage.client.scroll(
                collection_name=self.storage.songs_collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False  # Don't need vectors for this
            )

            if not results:
                break

            for point in results:
                song = point.payload.copy()
                song['_point_id'] = point.id
                all_songs.append(song)

            print(f"  Retrieved {len(all_songs)} songs...", end='\r')

            if offset is None:
                break

        print(f"\n✓ Retrieved {len(all_songs)} songs from Qdrant")
        return all_songs

    def fetch_lyrics_for_song(self, song: dict) -> tuple:
        """
        Fetch lyrics for a single song

        Returns:
            (lyrics_preview, full_lyrics) or (None, None) if not found
        """
        name = song.get('name', '')
        artist = song.get('artist', '')

        if not name or not artist:
            return None, None

        try:
            lyrics = self.lyrics_fetcher.get_lyrics(name, artist)
            if lyrics:
                preview = lyrics[:500] + "..." if len(lyrics) > 500 else lyrics
                return preview, lyrics
        except Exception as e:
            self.stats['errors'] += 1

        return None, None

    def update_song_with_lyrics(self, song: dict, lyrics_preview: str):
        """Update a song in Qdrant with lyrics"""
        point_id = song['_point_id']

        # Create new description with lyrics
        song_with_lyrics = song.copy()
        song_with_lyrics['lyrics_preview'] = lyrics_preview

        # Reconstruct features dict for description
        song_with_lyrics['features'] = {
            'danceability': song.get('danceability', 0),
            'energy': song.get('energy', 0),
            'valence': song.get('valence', 0),
            'tempo': song.get('tempo', 0),
            'loudness': song.get('loudness', 0),
            'speechiness': song.get('speechiness', 0),
            'acousticness': song.get('acousticness', 0),
            'instrumentalness': song.get('instrumentalness', 0),
            'liveness': song.get('liveness', 0),
            'key': song.get('key', 0),
            'mode': song.get('mode', 1),
            'time_signature': song.get('time_signature', 4),
        }

        # Generate new embedding with lyrics
        description = self.storage._create_song_description(song_with_lyrics)
        embedding = self.storage._generate_embedding(description)

        if embedding:
            # Update payload
            new_payload = song.copy()
            del new_payload['_point_id']
            new_payload['lyrics_preview'] = lyrics_preview
            new_payload['has_lyrics'] = True

            # Upsert to Qdrant
            self.storage.client.upsert(
                collection_name=self.storage.songs_collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=new_payload
                    )
                ]
            )
            return True

        return False

    def estimate_remaining_time(self, processed: int, total: int) -> str:
        """Estimate remaining time based on progress"""
        if not self.stats['start_time'] or processed == 0:
            return "calculating..."

        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        rate = processed / elapsed  # songs per second

        if rate > 0:
            remaining = (total - processed) / rate
            return str(timedelta(seconds=int(remaining)))

        return "unknown"

    def enrich_all_songs(self, batch_size: int = 50, save_every: int = 100):
        """
        Main method to enrich all songs with lyrics

        Args:
            batch_size: Number of songs to process before updating Qdrant
            save_every: Save progress after this many songs
        """
        print("=" * 60)
        print("LYRICS ENRICHMENT")
        print("=" * 60)

        # Load previous progress
        processed_ids = self.load_progress()
        if processed_ids:
            print(f"\nResuming from previous progress: {len(processed_ids)} songs already processed")
            print(f"  Lyrics found: {self.stats['lyrics_found']}")
            print(f"  Not found: {self.stats['lyrics_not_found']}")

        # Get all songs
        all_songs = self.get_all_songs()
        self.stats['total_songs'] = len(all_songs)

        # Filter out already processed
        songs_to_process = [s for s in all_songs if s['_point_id'] not in processed_ids]

        # Also skip songs that already have lyrics
        songs_needing_lyrics = []
        for song in songs_to_process:
            if song.get('has_lyrics') or song.get('lyrics_preview'):
                processed_ids.add(song['_point_id'])
                self.stats['already_had_lyrics'] += 1
            else:
                songs_needing_lyrics.append(song)

        print(f"\nTotal songs: {len(all_songs)}")
        print(f"Already processed: {len(processed_ids)}")
        print(f"Already have lyrics: {self.stats['already_had_lyrics']}")
        print(f"Need lyrics: {len(songs_needing_lyrics)}")

        if not songs_needing_lyrics:
            print("\n✓ All songs have been processed!")
            return

        # Estimate time
        estimated_seconds = len(songs_needing_lyrics) * 1.5
        estimated_time = str(timedelta(seconds=int(estimated_seconds)))
        print(f"\nEstimated time: {estimated_time}")

        # Confirm
        response = input("\nStart enrichment? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

        # Start processing
        if not self.stats['start_time']:
            self.stats['start_time'] = datetime.now().isoformat()

        print(f"\nProcessing {len(songs_needing_lyrics)} songs...")
        print("Press Ctrl+C to pause (progress will be saved)\n")

        try:
            for i, song in enumerate(tqdm(songs_needing_lyrics, desc="Fetching lyrics")):
                # Fetch lyrics
                lyrics_preview, full_lyrics = self.fetch_lyrics_for_song(song)

                if lyrics_preview:
                    # Update in Qdrant
                    if self.update_song_with_lyrics(song, lyrics_preview):
                        self.stats['lyrics_found'] += 1
                else:
                    self.stats['lyrics_not_found'] += 1

                # Mark as processed
                processed_ids.add(song['_point_id'])
                self.stats['processed'] += 1

                # Save progress periodically
                if (i + 1) % save_every == 0:
                    self.save_progress(processed_ids)
                    remaining = self.estimate_remaining_time(
                        len(processed_ids),
                        self.stats['total_songs']
                    )
                    tqdm.write(f"  Progress saved. Remaining time: ~{remaining}")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted! Saving progress...")
            self.save_progress(processed_ids)
            print(f"Progress saved. Run again to continue.")
            self.print_stats()
            sys.exit(0)

        # Final save
        self.save_progress(processed_ids)
        self.print_stats()

        # Clean up progress file if complete
        if len(processed_ids) >= self.stats['total_songs']:
            print("\n✓ All songs processed! Cleaning up progress file...")
            self.progress_file.unlink()

    def print_stats(self):
        """Print final statistics"""
        print("\n" + "=" * 60)
        print("ENRICHMENT STATISTICS")
        print("=" * 60)

        total = self.stats['total_songs']
        found = self.stats['lyrics_found']
        not_found = self.stats['lyrics_not_found']
        already_had = self.stats['already_had_lyrics']
        errors = self.stats['errors']

        print(f"\nTotal songs in database: {total}")
        print(f"Lyrics found (new): {found}")
        print(f"Already had lyrics: {already_had}")
        print(f"No lyrics available: {not_found}")
        print(f"Errors: {errors}")

        total_with_lyrics = found + already_had
        if total > 0:
            coverage = total_with_lyrics / total * 100
            print(f"\nTotal lyrics coverage: {total_with_lyrics}/{total} ({coverage:.1f}%)")

    def show_status(self):
        """Show current status without processing"""
        print("=" * 60)
        print("LYRICS ENRICHMENT STATUS")
        print("=" * 60)

        # Load progress
        processed_ids = self.load_progress()

        # Get current database state
        all_songs = self.get_all_songs()

        # Count songs with/without lyrics
        with_lyrics = 0
        without_lyrics = 0

        for song in all_songs:
            if song.get('has_lyrics') or song.get('lyrics_preview'):
                with_lyrics += 1
            else:
                without_lyrics += 1

        print(f"\nDatabase status:")
        print(f"  Total songs: {len(all_songs)}")
        print(f"  With lyrics: {with_lyrics} ({with_lyrics/len(all_songs)*100:.1f}%)")
        print(f"  Without lyrics: {without_lyrics}")

        if processed_ids:
            print(f"\nProgress file found:")
            print(f"  Songs processed: {len(processed_ids)}")
            print(f"  Remaining: {len(all_songs) - len(processed_ids)}")

            remaining_time = (len(all_songs) - len(processed_ids)) * 1.5
            print(f"  Estimated time to complete: {str(timedelta(seconds=int(remaining_time)))}")


def main():
    parser = argparse.ArgumentParser(
        description='Enrich existing Qdrant songs with lyrics from Genius API'
    )

    parser.add_argument(
        '--start',
        action='store_true',
        help='Start or resume lyrics enrichment'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status without processing'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset progress and start fresh'
    )

    args = parser.parse_args()

    # Verify Genius API key
    genius_key = os.getenv("GENIUS_API_KEY", "")
    if not genius_key or genius_key == "your_genius_api_key":
        print("✗ GENIUS_API_KEY not configured!")
        print("Set it in your .env file")
        sys.exit(1)

    enricher = LyricsEnricher()

    if args.reset:
        if enricher.progress_file.exists():
            enricher.progress_file.unlink()
            print("✓ Progress reset")
        else:
            print("No progress file found")

    elif args.status:
        enricher.show_status()

    elif args.start:
        enricher.enrich_all_songs()

    else:
        print("Lyrics Enrichment Tool")
        print("=" * 40)
        print("\nUsage:")
        print("  python enrich_lyrics.py --status   # Check current status")
        print("  python enrich_lyrics.py --start    # Start/resume enrichment")
        print("  python enrich_lyrics.py --reset    # Reset progress")
        print("\nThis will fetch lyrics for all songs in your Qdrant database")
        print("and update their embeddings to include lyrical content.")


if __name__ == '__main__':
    main()
