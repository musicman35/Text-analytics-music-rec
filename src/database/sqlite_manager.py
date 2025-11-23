"""
SQLite Database Manager for Music Recommendation System
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import config


class SQLiteManager:
    """Manages all SQLite database operations"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def initialize_database(self):
        """Create all necessary tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                profile_json TEXT DEFAULT '{}'
            )
        """)

        # Songs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spotify_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                artist TEXT NOT NULL,
                album TEXT,
                genre TEXT,
                features_json TEXT NOT NULL,
                lyrics_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                rating INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (song_id) REFERENCES songs (id)
            )
        """)

        # User memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                short_term_json TEXT DEFAULT '{}',
                long_term_json TEXT DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                recommended_songs TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                agent_reasoning TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_interactions_user_id
            ON interactions(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_interactions_song_id
            ON interactions(song_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_songs_spotify_id
            ON songs(spotify_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommendations_session_id
            ON recommendations(session_id)
        """)

        conn.commit()
        print(f"Database initialized at {self.db_path}")

    # ========== User Operations ==========

    def create_user(self, username: str, profile: Dict = None) -> int:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        profile_json = json.dumps(profile or {})

        try:
            cursor.execute(
                "INSERT INTO users (username, profile_json) VALUES (?, ?)",
                (username, profile_json)
            )
            conn.commit()
            user_id = cursor.lastrowid

            # Initialize user memory
            cursor.execute(
                "INSERT INTO user_memory (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()

            return user_id
        except sqlite3.IntegrityError:
            # User already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cursor.fetchone()[0]

    def get_user(self, user_id: int = None, username: str = None) -> Optional[Dict]:
        """Get user by ID or username"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        elif username:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        else:
            return None

        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "username": row["username"],
                "created_at": row["created_at"],
                "profile": json.loads(row["profile_json"])
            }
        return None

    def update_user_profile(self, user_id: int, profile: Dict):
        """Update user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        profile_json = json.dumps(profile)
        cursor.execute(
            "UPDATE users SET profile_json = ? WHERE id = ?",
            (profile_json, user_id)
        )
        conn.commit()

    # ========== Song Operations ==========

    def add_song(self, spotify_id: str, name: str, artist: str,
                 features: Dict, album: str = None, genre: str = None,
                 lyrics: str = None) -> int:
        """Add a song to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        features_json = json.dumps(features)

        try:
            cursor.execute("""
                INSERT INTO songs (spotify_id, name, artist, album, genre, features_json, lyrics_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (spotify_id, name, artist, album, genre, features_json, lyrics))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Song already exists, update it
            cursor.execute("""
                UPDATE songs
                SET name = ?, artist = ?, album = ?, genre = ?, features_json = ?, lyrics_text = ?
                WHERE spotify_id = ?
            """, (name, artist, album, genre, features_json, lyrics, spotify_id))
            conn.commit()

            cursor.execute("SELECT id FROM songs WHERE spotify_id = ?", (spotify_id,))
            return cursor.fetchone()[0]

    def get_song(self, song_id: int = None, spotify_id: str = None) -> Optional[Dict]:
        """Get song by ID or Spotify ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if song_id:
            cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
        elif spotify_id:
            cursor.execute("SELECT * FROM songs WHERE spotify_id = ?", (spotify_id,))
        else:
            return None

        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "spotify_id": row["spotify_id"],
                "name": row["name"],
                "artist": row["artist"],
                "album": row["album"],
                "genre": row["genre"],
                "features": json.loads(row["features_json"]),
                "lyrics": row["lyrics_text"],
                "created_at": row["created_at"]
            }
        return None

    def get_all_songs(self, limit: int = None) -> List[Dict]:
        """Get all songs from database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM songs ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "spotify_id": row["spotify_id"],
            "name": row["name"],
            "artist": row["artist"],
            "album": row["album"],
            "genre": row["genre"],
            "features": json.loads(row["features_json"]),
            "lyrics": row["lyrics_text"]
        } for row in rows]

    def get_songs_count(self) -> int:
        """Get total number of songs in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM songs")
        return cursor.fetchone()[0]

    # ========== Interaction Operations ==========

    def add_interaction(self, user_id: int, song_id: int,
                       action_type: str, rating: int = None):
        """Record user interaction with a song"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO interactions (user_id, song_id, rating, action_type)
            VALUES (?, ?, ?, ?)
        """, (user_id, song_id, rating, action_type))
        conn.commit()

    def get_user_interactions(self, user_id: int, limit: int = None) -> List[Dict]:
        """Get user's interaction history"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT i.*, s.spotify_id, s.name, s.artist, s.features_json
            FROM interactions i
            JOIN songs s ON i.song_id = s.id
            WHERE i.user_id = ?
            ORDER BY i.timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "song_id": row["song_id"],
            "spotify_id": row["spotify_id"],
            "song_name": row["name"],
            "artist": row["artist"],
            "rating": row["rating"],
            "action_type": row["action_type"],
            "timestamp": row["timestamp"],
            "features": json.loads(row["features_json"])
        } for row in rows]

    # ========== Memory Operations ==========

    def get_user_memory(self, user_id: int) -> Dict:
        """Get user's memory (short-term and long-term)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_memory WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            return {
                "short_term": json.loads(row["short_term_json"]),
                "long_term": json.loads(row["long_term_json"]),
                "updated_at": row["updated_at"]
            }
        return {"short_term": {}, "long_term": {}}

    def update_user_memory(self, user_id: int, short_term: Dict = None,
                          long_term: Dict = None):
        """Update user memory"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if short_term is not None:
            updates.append("short_term_json = ?")
            params.append(json.dumps(short_term))

        if long_term is not None:
            updates.append("long_term_json = ?")
            params.append(json.dumps(long_term))

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        query = f"UPDATE user_memory SET {', '.join(updates)} WHERE user_id = ?"
        cursor.execute(query, params)
        conn.commit()

    # ========== Recommendation Operations ==========

    def save_recommendation(self, session_id: str, user_id: int,
                           recommended_songs: List[int], agent_reasoning: Dict = None):
        """Save a recommendation session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        songs_json = json.dumps(recommended_songs)
        reasoning_json = json.dumps(agent_reasoning or {})

        cursor.execute("""
            INSERT INTO recommendations (session_id, user_id, recommended_songs, agent_reasoning)
            VALUES (?, ?, ?, ?)
        """, (session_id, user_id, songs_json, reasoning_json))
        conn.commit()

    def get_recommendations(self, user_id: int = None, session_id: str = None) -> List[Dict]:
        """Get recommendation history"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if session_id:
            cursor.execute(
                "SELECT * FROM recommendations WHERE session_id = ?",
                (session_id,)
            )
        elif user_id:
            cursor.execute(
                "SELECT * FROM recommendations WHERE user_id = ? ORDER BY timestamp DESC",
                (user_id,)
            )
        else:
            return []

        rows = cursor.fetchall()

        return [{
            "id": row["id"],
            "session_id": row["session_id"],
            "user_id": row["user_id"],
            "recommended_songs": json.loads(row["recommended_songs"]),
            "timestamp": row["timestamp"],
            "agent_reasoning": json.loads(row["agent_reasoning"])
        } for row in rows]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None


# Convenience function
def get_db() -> SQLiteManager:
    """Get database manager instance"""
    return SQLiteManager()
