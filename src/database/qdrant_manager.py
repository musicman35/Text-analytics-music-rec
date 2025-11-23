"""
Qdrant Vector Database Manager
Handles all vector database operations for music embeddings
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models
from openai import OpenAI
import numpy as np
from typing import List, Dict, Optional
from tqdm import tqdm
import config
from src.database.sqlite_manager import SQLiteManager


class QdrantManager:
    """Manages Qdrant vector database operations"""

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
        self.collection_name = config.QDRANT_COLLECTION_NAME
        self.db = SQLiteManager()

    def create_collection(self, delete_existing: bool = False):
        """Create or recreate the collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)

            if collection_exists:
                if delete_existing:
                    print(f"Deleting existing collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    print(f"Collection '{self.collection_name}' already exists")
                    return

            # Create new collection
            print(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=config.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            print("Collection created successfully")

        except Exception as e:
            print(f"Error creating collection: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def create_song_description(self, song: Dict) -> str:
        """Create a rich text description for embedding"""
        features = song.get('features', {})

        # Create description from audio features
        feature_descriptions = []

        if features.get('energy', 0) > 0.7:
            feature_descriptions.append("high energy")
        elif features.get('energy', 0) < 0.3:
            feature_descriptions.append("low energy")

        if features.get('valence', 0) > 0.7:
            feature_descriptions.append("positive mood")
        elif features.get('valence', 0) < 0.3:
            feature_descriptions.append("melancholic mood")

        if features.get('danceability', 0) > 0.7:
            feature_descriptions.append("danceable")

        if features.get('acousticness', 0) > 0.7:
            feature_descriptions.append("acoustic")

        if features.get('instrumentalness', 0) > 0.5:
            feature_descriptions.append("instrumental")

        if features.get('speechiness', 0) > 0.33:
            feature_descriptions.append("spoken word")

        # Tempo description
        tempo = features.get('tempo', 120)
        if tempo > 140:
            feature_descriptions.append("fast tempo")
        elif tempo < 80:
            feature_descriptions.append("slow tempo")

        features_text = ", ".join(feature_descriptions) if feature_descriptions else "moderate characteristics"

        # Create full description
        description = f"Song: {song['name']} by {song['artist']}. "
        description += f"Genre: {song.get('genre', 'unknown')}. "
        description += f"Musical characteristics: {features_text}. "

        # Add lyrics preview if available
        lyrics = song.get('lyrics', '')
        if lyrics:
            # Take first 500 characters of lyrics
            lyrics_preview = lyrics[:500].replace('\n', ' ')
            description += f"Lyrical content: {lyrics_preview}"

        return description

    def embed_song(self, song: Dict) -> Optional[Dict]:
        """Create embedding for a single song"""
        try:
            description = self.create_song_description(song)
            embedding = self.generate_embedding(description)

            if embedding:
                return {
                    'id': song['id'],
                    'embedding': embedding,
                    'payload': {
                        'spotify_id': song['spotify_id'],
                        'name': song['name'],
                        'artist': song['artist'],
                        'album': song.get('album'),
                        'genre': song.get('genre'),
                        'features': song['features'],
                        'lyrics_preview': song.get('lyrics', '')[:200] if song.get('lyrics') else '',
                        'description': description
                    }
                }
        except Exception as e:
            print(f"Error embedding song {song.get('name')}: {e}")

        return None

    def batch_embed_songs(self, songs: List[Dict], batch_size: int = 50) -> List[Dict]:
        """Embed multiple songs in batches"""
        print(f"\nEmbedding {len(songs)} songs...")

        embedded_songs = []

        for i in tqdm(range(0, len(songs), batch_size), desc="Embedding batches"):
            batch = songs[i:i+batch_size]

            for song in batch:
                embedded = self.embed_song(song)
                if embedded:
                    embedded_songs.append(embedded)

        print(f"Successfully embedded {len(embedded_songs)}/{len(songs)} songs")
        return embedded_songs

    def upload_songs(self, embedded_songs: List[Dict], batch_size: int = 100):
        """Upload embedded songs to Qdrant"""
        print(f"\nUploading {len(embedded_songs)} songs to Qdrant...")

        for i in tqdm(range(0, len(embedded_songs), batch_size), desc="Uploading batches"):
            batch = embedded_songs[i:i+batch_size]

            points = [
                PointStruct(
                    id=song['id'],
                    vector=song['embedding'],
                    payload=song['payload']
                )
                for song in batch
            ]

            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
            except Exception as e:
                print(f"Error uploading batch {i}: {e}")

        print("Upload complete")

    def search(self, query: str, limit: int = 50, genre_filter: str = None) -> List[Dict]:
        """Search for similar songs using natural language query"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)

            if not query_embedding:
                return []

            # Build filter if genre specified
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

            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter
            )

            # Format results
            songs = []
            for result in results:
                song = {
                    'id': result.id,
                    'score': result.score,
                    'spotify_id': result.payload['spotify_id'],
                    'name': result.payload['name'],
                    'artist': result.payload['artist'],
                    'album': result.payload['album'],
                    'genre': result.payload['genre'],
                    'features': result.payload['features'],
                    'lyrics_preview': result.payload['lyrics_preview'],
                    'description': result.payload['description']
                }
                songs.append(song)

            return songs

        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': info.config.params.vectors.size,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}

    def populate_from_database(self, limit: int = None):
        """Populate Qdrant from SQLite database"""
        print("\nPopulating Qdrant from database...")

        # Get all songs from database
        songs = self.db.get_all_songs(limit=limit)

        if not songs:
            print("No songs found in database")
            return

        # Create collection if it doesn't exist
        self.create_collection(delete_existing=False)

        # Embed and upload songs
        embedded_songs = self.batch_embed_songs(songs)
        self.upload_songs(embedded_songs)

        # Show collection info
        info = self.get_collection_info()
        print(f"\nCollection info: {info}")


def main():
    """Run Qdrant setup as standalone script"""
    print("Initializing Qdrant vector database...")

    manager = QdrantManager()

    # Create collection
    manager.create_collection(delete_existing=True)

    # Populate from database
    manager.populate_from_database()

    print("\nQdrant setup complete!")


if __name__ == "__main__":
    main()
