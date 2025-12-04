"""
Qdrant-Only Storage Manager
Uses Qdrant as single source of truth for all data
No SQLite dependency - perfect for cloud deployment
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models
from openai import OpenAI
import uuid
from typing import List, Dict, Optional
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import config
from src.utils.audio_features import (
    extract_features_from_song,
    create_song_payload,
    create_song_description
)


class QdrantStorage:
    """
    Qdrant-only storage manager
    Stores songs, users, and interactions all in Qdrant
    """

    def __init__(self):
        # Initialize Qdrant client
        if config.QDRANT_USE_CLOUD and config.QDRANT_API_KEY:
            self.client = QdrantClient(
                url=config.QDRANT_HOST,
                api_key=config.QDRANT_API_KEY
            )
        else:
            # Local Qdrant instance
            self.client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT
            )

        # Initialize OpenAI for embeddings
        # Use env var directly to avoid fallback values
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key or openai_key == "your_openai_api_key":
            openai_key = config.OPENAI_API_KEY  # Fallback to config if needed
        self.openai_client = OpenAI(api_key=openai_key)

        # Collection names
        self.songs_collection = "songs"
        self.users_collection = "users"
        self.interactions_collection = "interactions"

        # Ensure collections exist
        self._ensure_collections()

    def _ensure_collections(self):
        """Create collections if they don't exist"""
        try:
            collections = {c.name for c in self.client.get_collections().collections}

            # Songs collection (with vectors)
            if self.songs_collection not in collections:
                self.client.create_collection(
                    collection_name=self.songs_collection,
                    vectors_config=VectorParams(
                        size=config.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created collection: {self.songs_collection}")

            # Users collection (no vectors needed)
            if self.users_collection not in collections:
                self.client.create_collection(
                    collection_name=self.users_collection,
                    vectors_config=VectorParams(
                        size=128,  # Dummy dimension
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created collection: {self.users_collection}")

            # Interactions collection (no vectors needed)
            if self.interactions_collection not in collections:
                self.client.create_collection(
                    collection_name=self.interactions_collection,
                    vectors_config=VectorParams(
                        size=128,  # Dummy dimension
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created collection: {self.interactions_collection}")

            # Ensure user_id field has an index for filtering
            try:
                from qdrant_client.http.models import PayloadSchemaType
                self.client.create_payload_index(
                    collection_name=self.interactions_collection,
                    field_name="user_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print(f"✓ Created index on user_id for {self.interactions_collection}")
            except Exception as idx_error:
                # Index might already exist, which is fine
                if "already exists" not in str(idx_error).lower():
                    print(f"Note: Could not create user_id index: {idx_error}")

        except Exception as e:
            print(f"Error ensuring collections: {e}")

    # ==================== SONG OPERATIONS ====================

    def add_song(self, song: Dict) -> str:
        """
        Add song to Qdrant with full metadata

        Args:
            song: Dictionary with song data (name, artist, features, etc.)

        Returns:
            Song ID (UUID)
        """
        try:
            # Generate unique ID
            song_id = song.get('spotify_id', str(uuid.uuid4()))

            # Create rich description for embedding
            description = self._create_song_description(song)

            # Generate embedding
            embedding = self._generate_embedding(description)

            if not embedding:
                raise ValueError("Failed to generate embedding")

            # Prepare payload with ALL song data
            payload = {
                'song_id': song_id,
                'name': song.get('name', ''),
                'artist': song.get('artist', ''),
                'album': song.get('album', ''),
                'genre': song.get('genre', ''),
                'popularity': song.get('popularity', 0),
                'duration_ms': song.get('duration_ms', 0),
                'explicit': song.get('explicit', False),
                # Audio features
                'danceability': song.get('features', {}).get('danceability', 0),
                'energy': song.get('features', {}).get('energy', 0),
                'valence': song.get('features', {}).get('valence', 0),
                'tempo': song.get('features', {}).get('tempo', 0),
                'loudness': song.get('features', {}).get('loudness', 0),
                'speechiness': song.get('features', {}).get('speechiness', 0),
                'acousticness': song.get('features', {}).get('acousticness', 0),
                'instrumentalness': song.get('features', {}).get('instrumentalness', 0),
                'liveness': song.get('features', {}).get('liveness', 0),
                'key': song.get('features', {}).get('key', 0),
                'mode': song.get('features', {}).get('mode', 1),
                'time_signature': song.get('features', {}).get('time_signature', 4),
                # Lyrics (if available)
                'lyrics_preview': song.get('lyrics_preview', ''),
                'has_lyrics': bool(song.get('lyrics_preview')),
            }

            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.songs_collection,
                points=[
                    PointStruct(
                        id=song_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            return song_id

        except Exception as e:
            print(f"Error adding song {song.get('name', 'Unknown')}: {e}")
            raise

    def add_songs(self, songs: List[Dict], batch_size: int = 100):
        """Add multiple songs in batches"""
        print(f"\nAdding {len(songs)} songs to Qdrant...")

        for i in tqdm(range(0, len(songs), batch_size), desc="Uploading songs"):
            batch = songs[i:i + batch_size]
            points = []

            for song in batch:
                try:
                    # Use UUID for Qdrant point ID, store spotify_id in payload
                    point_id = str(uuid.uuid4())
                    spotify_id = song.get('spotify_id', '')

                    description = self._create_song_description(song)
                    embedding = self._generate_embedding(description)

                    if not embedding:
                        continue

                    payload = {
                        'song_id': point_id,  # Internal ID for references
                        'spotify_id': spotify_id,  # Original Spotify ID
                        'name': song.get('name', ''),
                        'artist': song.get('artist', ''),
                        'album': song.get('album', ''),
                        'genre': song.get('genre', ''),
                        'popularity': song.get('popularity', 0),
                        'duration_ms': song.get('duration_ms', 0),
                        'explicit': song.get('explicit', False),
                        'danceability': song.get('features', {}).get('danceability', 0),
                        'energy': song.get('features', {}).get('energy', 0),
                        'valence': song.get('features', {}).get('valence', 0),
                        'tempo': song.get('features', {}).get('tempo', 0),
                        'loudness': song.get('features', {}).get('loudness', 0),
                        'speechiness': song.get('features', {}).get('speechiness', 0),
                        'acousticness': song.get('features', {}).get('acousticness', 0),
                        'instrumentalness': song.get('features', {}).get('instrumentalness', 0),
                        'liveness': song.get('features', {}).get('liveness', 0),
                        'key': song.get('features', {}).get('key', 0),
                        'mode': song.get('features', {}).get('mode', 1),
                        'time_signature': song.get('features', {}).get('time_signature', 4),
                        # Lyrics (if available)
                        'lyrics_preview': song.get('lyrics_preview', ''),
                        'has_lyrics': bool(song.get('lyrics_preview')),
                    }

                    points.append(
                        PointStruct(
                            id=point_id,  # Use UUID instead of spotify_id
                            vector=embedding,
                            payload=payload
                        )
                    )

                except Exception as e:
                    print(f"Error processing song: {e}")
                    continue

            # Upload batch
            if points:
                self.client.upsert(
                    collection_name=self.songs_collection,
                    points=points
                )

        print(f"✓ Added {len(songs)} songs to Qdrant")

    def search_songs(self, query: str, limit: int = 50, genre_filter: str = None) -> List[Dict]:
        """
        Search songs by semantic similarity

        Args:
            query: Search query
            limit: Number of results
            genre_filter: Optional genre filter

        Returns:
            List of song dictionaries
        """
        try:
            # Generate query embedding
            embedding = self._generate_embedding(query)

            if not embedding:
                return []

            # Build filter
            query_filter = None
            if genre_filter:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="genre",
                            match=MatchValue(value=genre_filter)
                        )
                    ]
                )

            # Search using query method
            response = self.client.query_points(
                collection_name=self.songs_collection,
                query=embedding,
                limit=limit,
                query_filter=query_filter
            )

            # Convert to song dictionaries
            songs = []
            # query_points returns a QueryResponse object with a points attribute
            if hasattr(response, 'points') and response.points:
                for result in response.points:
                    if hasattr(result, 'payload'):
                        song = result.payload.copy()
                        if hasattr(result, 'score'):
                            song['score'] = result.score

                        # Reconstruct features dict using shared utility
                        song['features'] = extract_features_from_song(song)

                        # Ensure lyrics fields are present
                        if 'lyrics_preview' not in song:
                            song['lyrics_preview'] = ''
                        if 'has_lyrics' not in song:
                            song['has_lyrics'] = bool(song.get('lyrics_preview'))

                        songs.append(song)

            return songs

        except Exception as e:
            print(f"Error searching songs: {e}")
            return []

    def get_song_by_id(self, song_id: str) -> Optional[Dict]:
        """Get song by ID"""
        try:
            result = self.client.retrieve(
                collection_name=self.songs_collection,
                ids=[song_id]
            )

            if result:
                return result[0].payload

            return None

        except Exception as e:
            print(f"Error getting song: {e}")
            return None

    def get_songs_by_genre(self, genre: str, limit: int = 100) -> List[Dict]:
        """Get songs by genre"""
        try:
            results = self.client.scroll(
                collection_name=self.songs_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="genre",
                            match=MatchValue(value=genre)
                        )
                    ]
                ),
                limit=limit
            )

            return [point.payload for point in results[0]]

        except Exception as e:
            print(f"Error getting songs by genre: {e}")
            return []

    def get_song_count(self) -> int:
        """Get total number of songs"""
        try:
            info = self.client.get_collection(self.songs_collection)
            return info.points_count
        except:
            return 0

    # ==================== USER OPERATIONS ====================

    def create_user(self, username: str) -> str:
        """Create new user"""
        user_id = str(uuid.uuid4())

        self.client.upsert(
            collection_name=self.users_collection,
            points=[
                PointStruct(
                    id=user_id,
                    vector=[0.0] * 128,  # Dummy vector
                    payload={
                        'user_id': user_id,
                        'username': username,
                        'created_at': str(uuid.uuid1().time)
                    }
                )
            ]
        )

        return user_id

    def get_user(self, user_id: str = None, username: str = None) -> Optional[Dict]:
        """Get user by ID or username"""
        try:
            if user_id:
                # Get by user_id
                result = self.client.retrieve(
                    collection_name=self.users_collection,
                    ids=[user_id]
                )

                if result:
                    return result[0].payload

            elif username:
                # Get all users and search by username (since we don't have an index)
                # This is inefficient but works for small user bases
                result, _ = self.client.scroll(
                    collection_name=self.users_collection,
                    limit=1000  # Reasonable limit for users
                )

                # Search for matching username
                for point in result:
                    if point.payload.get('username') == username:
                        user_data = point.payload
                        user_data['id'] = point.id
                        return user_data

            return None

        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    # ==================== INTERACTION OPERATIONS ====================

    def add_interaction(self, user_id: str, song_id: str, interaction_type: str,
                        rating: int = None, spotify_id: str = None):
        """Add user-song interaction

        Args:
            user_id: User identifier
            song_id: Song identifier (internal UUID)
            interaction_type: Type of interaction ('like', 'dislike', 'play', 'rate')
            rating: Optional rating value (1-5)
            spotify_id: Optional Spotify track ID for stable cross-session matching
        """
        interaction_id = str(uuid.uuid4())

        payload = {
            'interaction_id': interaction_id,
            'user_id': user_id,
            'song_id': song_id,
            'interaction_type': interaction_type,  # 'like', 'dislike', 'play', 'rate'
            'timestamp': str(uuid.uuid1().time)
        }

        # Add spotify_id if provided (for stable ID matching across DB rebuilds)
        if spotify_id:
            payload['spotify_id'] = spotify_id

        # Add rating if provided
        if rating is not None:
            payload['rating'] = rating

        self.client.upsert(
            collection_name=self.interactions_collection,
            points=[
                PointStruct(
                    id=interaction_id,
                    vector=[0.0] * 128,  # Dummy vector
                    payload=payload
                )
            ]
        )

    def get_user_interactions(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get all interactions for a user"""
        try:
            results = self.client.scroll(
                collection_name=self.interactions_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=limit
            )

            return [point.payload for point in results[0]]

        except Exception as e:
            print(f"Error getting interactions: {e}")
            return []

    def get_user_interaction_count(self, user_id: str) -> int:
        """Get total count of interactions for a user without retrieving all data"""
        try:
            result = self.client.count(
                collection_name=self.interactions_collection,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            )
            return result.count

        except Exception as e:
            print(f"Error counting interactions: {e}")
            return 0

    def save_recommendation(self, session_id: str, user_id: str,
                           recommended_songs: List[str], agent_reasoning: Dict):
        """
        Save recommendation session
        Note: Currently a stub - recommendations are not persisted
        TODO: Implement Qdrant-based recommendation history storage
        """
        pass

    # ==================== MEMORY MANAGEMENT ====================

    def get_user_memory(self, user_id: str) -> Optional[Dict]:
        """
        Get user memory (long-term and short-term)
        Note: Memory is currently stored in-memory only
        TODO: Implement Qdrant-based memory storage
        """
        return None

    def update_user_memory(self, user_id: str, long_term: Dict = None, short_term: Dict = None):
        """
        Update user memory
        Note: Memory is currently stored in-memory only
        TODO: Implement Qdrant-based memory storage
        """
        pass

    def get_song(self, song_id: str = None, spotify_id: str = None) -> Optional[Dict]:
        """
        Get a single song by ID

        Args:
            song_id: Song ID (internal UUID or spotify_id)
            spotify_id: Spotify track ID

        Returns:
            Song dictionary or None
        """
        # Use either parameter
        search_id = song_id or spotify_id
        if not search_id:
            return None

        try:
            # First try direct ID lookup (works if search_id is the point UUID)
            result = self.client.retrieve(
                collection_name=self.songs_collection,
                ids=[search_id]
            )

            if result and len(result) > 0:
                point = result[0]
                song = point.payload.copy()
                song['features'] = extract_features_from_song(song)
                return song

            # If direct lookup fails, try searching by spotify_id in payload
            # This handles cases where song_id is a spotify_id or old UUID
            scroll_result = self.client.scroll(
                collection_name=self.songs_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="spotify_id",
                            match=MatchValue(value=search_id)
                        )
                    ]
                ),
                limit=1
            )

            if scroll_result and scroll_result[0]:
                point = scroll_result[0][0]
                song = point.payload.copy()
                song['features'] = extract_features_from_song(song)
                return song

            return None

        except Exception as e:
            print(f"Error getting song: {e}")
            return None

    def get_song_count(self) -> int:
        """Get total number of songs in database"""
        try:
            result = self.client.count(collection_name=self.songs_collection)
            return result.count
        except Exception as e:
            print(f"Error getting song count: {e}")
            return 0

    # ==================== HELPER METHODS ====================

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def _create_song_description(self, song: Dict) -> str:
        """Create rich description for embedding, including lyrics if available"""
        # Use shared utility function
        return create_song_description(song, include_lyrics=True, max_lyrics_chars=300)

    def clear_all_data(self):
        """Clear all collections (use with caution!)"""
        try:
            for collection in [self.songs_collection, self.users_collection, self.interactions_collection]:
                self.client.delete_collection(collection)
                print(f"✓ Deleted collection: {collection}")

            self._ensure_collections()
            print("✓ All data cleared and collections recreated")

        except Exception as e:
            print(f"Error clearing data: {e}")


# Convenience functions
def get_storage() -> QdrantStorage:
    """Get Qdrant storage instance"""
    return QdrantStorage()
