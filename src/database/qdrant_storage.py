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
import config


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
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

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

        except Exception as e:
            print(f"Error ensuring collections: {e}")

    # ==================== SONG OPERATIONS ====================

    def add_song(self, song: Dict) -> str:
        """
        Add song to Qdrant with full metadata

        Args:
            song: Dictionary with song data (name, artist, features, lyrics, etc.)

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
                'lyrics': song.get('lyrics', ''),
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
                    song_id = song.get('spotify_id', str(uuid.uuid4()))
                    description = self._create_song_description(song)
                    embedding = self._generate_embedding(description)

                    if not embedding:
                        continue

                    payload = {
                        'song_id': song_id,
                        'name': song.get('name', ''),
                        'artist': song.get('artist', ''),
                        'album': song.get('album', ''),
                        'genre': song.get('genre', ''),
                        'lyrics': song.get('lyrics', ''),
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
                    }

                    points.append(
                        PointStruct(
                            id=song_id,
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

            # Search
            results = self.client.search(
                collection_name=self.songs_collection,
                query_vector=embedding,
                limit=limit,
                query_filter=query_filter
            )

            # Convert to song dictionaries
            songs = []
            for result in results:
                song = result.payload.copy()
                song['score'] = result.score
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

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            result = self.client.retrieve(
                collection_name=self.users_collection,
                ids=[user_id]
            )

            if result:
                return result[0].payload

            return None

        except:
            return None

    # ==================== INTERACTION OPERATIONS ====================

    def add_interaction(self, user_id: str, song_id: str, interaction_type: str):
        """Add user-song interaction"""
        interaction_id = str(uuid.uuid4())

        self.client.upsert(
            collection_name=self.interactions_collection,
            points=[
                PointStruct(
                    id=interaction_id,
                    vector=[0.0] * 128,  # Dummy vector
                    payload={
                        'interaction_id': interaction_id,
                        'user_id': user_id,
                        'song_id': song_id,
                        'interaction_type': interaction_type,  # 'like', 'dislike', 'play'
                        'timestamp': str(uuid.uuid1().time)
                    }
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
        """Create rich description for embedding"""
        features = song.get('features', {})

        # Build description
        parts = [
            f"Song: {song.get('name', '')} by {song.get('artist', '')}",
            f"Genre: {song.get('genre', 'unknown')}",
        ]

        # Audio features
        feature_desc = []
        if features.get('energy', 0) > 0.7:
            feature_desc.append("high energy")
        if features.get('valence', 0) > 0.7:
            feature_desc.append("positive mood")
        if features.get('danceability', 0) > 0.7:
            feature_desc.append("danceable")
        if features.get('acousticness', 0) > 0.7:
            feature_desc.append("acoustic")

        if feature_desc:
            parts.append(f"Characteristics: {', '.join(feature_desc)}")

        # Lyrics preview
        lyrics = song.get('lyrics', '')
        if lyrics:
            lyrics_preview = ' '.join(lyrics.split()[:100])
            parts.append(f"Lyrics: {lyrics_preview}")

        return '. '.join(parts)

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
