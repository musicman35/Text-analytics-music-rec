"""
Short-term Memory System
Manages current session context and recent interactions
"""

from typing import List, Dict, Optional
from datetime import datetime
import config
from src.database.qdrant_storage import QdrantStorage


class ShortTermMemory:
    """Manages short-term memory for current session"""

    def __init__(self, user_id: int, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.db = QdrantStorage()
        self.window_size = config.SHORT_TERM_MEMORY_WINDOW

        # In-memory storage for current session
        self.current_queries = []
        self.recent_interactions = []
        self.conversation_context = []
        self.temporary_preferences = {}

    def add_query(self, query: str):
        """Add user query to short-term memory"""
        self.current_queries.append({
            'query': query,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only recent queries
        if len(self.current_queries) > 10:
            self.current_queries = self.current_queries[-10:]

    def add_interaction(self, song_id: int, action_type: str, rating: int = None):
        """Add interaction to short-term memory"""
        interaction = {
            'song_id': song_id,
            'action_type': action_type,
            'rating': rating,
            'timestamp': datetime.now().isoformat()
        }

        self.recent_interactions.append(interaction)

        # Keep only recent interactions (within window)
        if len(self.recent_interactions) > self.window_size:
            self.recent_interactions = self.recent_interactions[-self.window_size:]

        # Also save to database
        self.db.add_interaction(self.user_id, song_id, action_type, rating)

    def add_conversation_turn(self, role: str, content: str):
        """Add conversation turn to context"""
        self.conversation_context.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

        # Keep conversation manageable
        if len(self.conversation_context) > 20:
            self.conversation_context = self.conversation_context[-20:]

    def update_temporary_preference(self, key: str, value):
        """Update temporary preference for current session"""
        self.temporary_preferences[key] = value

    def get_recent_interactions(self, limit: int = None) -> List[Dict]:
        """Get recent interactions from this session"""
        interactions = self.recent_interactions.copy()

        if limit:
            interactions = interactions[-limit:]

        return interactions

    def get_recent_queries(self, limit: int = 5) -> List[str]:
        """Get recent queries from this session"""
        queries = [q['query'] for q in self.current_queries[-limit:]]
        return queries

    def get_conversation_context(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation turns"""
        return self.conversation_context[-limit:]

    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'queries_count': len(self.current_queries),
            'interactions_count': len(self.recent_interactions),
            'recent_queries': self.get_recent_queries(3),
            'temporary_preferences': self.temporary_preferences,
            'liked_songs': [i['song_id'] for i in self.recent_interactions
                          if i.get('rating') and i['rating'] >= 4],
            'disliked_songs': [i['song_id'] for i in self.recent_interactions
                             if i.get('rating') and i['rating'] <= 2]
        }

    def save_to_database(self):
        """Save short-term memory to database"""
        memory_data = {
            'session_id': self.session_id,
            'current_queries': self.current_queries,
            'recent_interactions': self.recent_interactions,
            'conversation_context': self.conversation_context,
            'temporary_preferences': self.temporary_preferences,
            'timestamp': datetime.now().isoformat()
        }

        # Get existing memory
        existing_memory = self.db.get_user_memory(self.user_id)

        # Update short-term memory
        self.db.update_user_memory(
            self.user_id,
            short_term=memory_data
        )

    def load_from_database(self):
        """Load short-term memory from database"""
        memory = self.db.get_user_memory(self.user_id)

        if memory and memory.get('short_term'):
            short_term = memory['short_term']
            self.current_queries = short_term.get('current_queries', [])
            self.recent_interactions = short_term.get('recent_interactions', [])
            self.conversation_context = short_term.get('conversation_context', [])
            self.temporary_preferences = short_term.get('temporary_preferences', {})

    def get_contextual_preferences(self) -> Dict:
        """Extract contextual preferences from recent behavior"""
        preferences = {}

        # Analyze recent interactions
        if self.recent_interactions:
            liked_interactions = [i for i in self.recent_interactions
                                if i.get('rating') and i['rating'] >= 4]

            if liked_interactions:
                preferences['recently_liked_count'] = len(liked_interactions)

        # Recent query patterns
        if self.current_queries:
            recent_query_text = ' '.join([q['query'] for q in self.current_queries[-3:]])
            preferences['recent_query_context'] = recent_query_text

        # Temporary preferences
        preferences.update(self.temporary_preferences)

        return preferences

    def clear(self):
        """Clear short-term memory (new session)"""
        self.current_queries = []
        self.recent_interactions = []
        self.conversation_context = []
        self.temporary_preferences = {}


# Convenience function
def get_short_term_memory(user_id: int, session_id: str) -> ShortTermMemory:
    """Get ShortTermMemory instance"""
    memory = ShortTermMemory(user_id, session_id)
    memory.load_from_database()
    return memory
