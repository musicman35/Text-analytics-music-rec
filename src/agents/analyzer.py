"""
Analyzer Agent
Analyzes user listening history and generates user profile
"""

from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
import config
from src.memory.long_term import LongTermMemory, get_long_term_memory
from src.memory.short_term import ShortTermMemory
from src.database.qdrant_storage import QdrantStorage


class AnalyzerAgent:
    """Agent that analyzes user behavior and preferences"""

    def __init__(self):
        self.db = QdrantStorage()

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.AGENT_LLM_MODEL,
            temperature=config.AGENT_TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )

    def analyze_user(self, user_id: int,
                    short_term_memory: ShortTermMemory = None) -> Dict:
        """
        Analyze user and generate profile

        Args:
            user_id: User ID
            short_term_memory: Optional short-term memory

        Returns:
            Dict with user analysis
        """
        print(f"\n[AnalyzerAgent] Analyzing user {user_id}")

        # Get long-term memory (with auto-update)
        long_term = get_long_term_memory(user_id, auto_update=True)

        # Build analysis
        analysis = {
            'user_id': user_id,
            'profile_summary': long_term.get_profile_summary(),
            'genre_preferences': long_term.profile['genre_preferences'],
            'audio_feature_preferences': long_term.profile['audio_feature_preferences'],
            'liked_artists': long_term.profile['liked_artists'][:10],  # Top 10
            'disliked_artists': long_term.profile['disliked_artists'][:5],  # Top 5
            'time_patterns': long_term.profile['time_of_day_patterns'],
            'total_interactions': long_term.profile['total_interactions']
        }

        # Add short-term context if available
        if short_term_memory:
            session_summary = short_term_memory.get_session_summary()
            analysis['session_context'] = {
                'recent_queries': session_summary['recent_queries'],
                'liked_in_session': session_summary['liked_songs'],
                'disliked_in_session': session_summary['disliked_songs'],
                'temporary_preferences': session_summary['temporary_preferences']
            }

        # Generate natural language summary
        analysis['natural_language_summary'] = self._generate_summary(analysis)

        print(f"[AnalyzerAgent] Analysis complete")
        print(f"[AnalyzerAgent] Profile: {analysis['profile_summary'][:100]}...")

        return analysis

    def _generate_summary(self, analysis: Dict) -> str:
        """Generate natural language summary using LLM"""
        try:
            prompt = f"""Based on this user's music listening profile, generate a concise
            2-3 sentence summary of their music taste and preferences.

            Profile data:
            {analysis['profile_summary']}

            Genre preferences: {analysis['genre_preferences']}
            Total interactions: {analysis['total_interactions']}

            Generate a natural summary:"""

            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"[AnalyzerAgent] Error generating summary: {e}")
            return analysis['profile_summary']

    def identify_patterns(self, user_id: int) -> Dict:
        """
        Identify specific patterns in user behavior

        Returns:
            Dict with identified patterns
        """
        print(f"\n[AnalyzerAgent] Identifying patterns for user {user_id}")

        long_term = get_long_term_memory(user_id)
        interactions = self.db.get_user_interactions(user_id, limit=100)

        patterns = {
            'consistency': self._analyze_consistency(interactions),
            'diversity': self._analyze_diversity(interactions),
            'trending': self._analyze_trends(interactions),
            'mood_patterns': self._analyze_mood_patterns(long_term)
        }

        return patterns

    def _analyze_consistency(self, interactions: List[Dict]) -> Dict:
        """Analyze how consistent user preferences are"""
        if len(interactions) < 10:
            return {'score': 0.5, 'description': 'Not enough data'}

        # Look at genre consistency
        genres = [i.get('features', {}) for i in interactions if 'features' in i]

        # Simple consistency score based on variety
        unique_count = len(set([str(g) for g in genres]))
        consistency_score = 1 - (unique_count / len(genres))

        return {
            'score': consistency_score,
            'description': 'High' if consistency_score > 0.7 else 'Moderate' if consistency_score > 0.4 else 'Low'
        }

    def _analyze_diversity(self, interactions: List[Dict]) -> Dict:
        """Analyze diversity of listening habits"""
        if not interactions:
            return {'score': 0.5, 'description': 'Not enough data'}

        # Count unique artists
        artists = [i['artist'] for i in interactions]
        unique_artists = len(set(artists))
        diversity_score = unique_artists / len(artists)

        return {
            'score': diversity_score,
            'unique_artists': unique_artists,
            'total_songs': len(artists),
            'description': 'High' if diversity_score > 0.7 else 'Moderate' if diversity_score > 0.4 else 'Low'
        }

    def _analyze_trends(self, interactions: List[Dict]) -> Dict:
        """Analyze recent trends in preferences"""
        if len(interactions) < 20:
            return {'description': 'Not enough data for trend analysis'}

        # Compare recent vs older interactions
        recent = interactions[:10]
        older = interactions[10:20]

        recent_features = [i.get('features', {}) for i in recent if 'features' in i]
        older_features = [i.get('features', {}) for i in older if 'features' in i]

        if not recent_features or not older_features:
            return {'description': 'Insufficient feature data'}

        # Calculate average energy change
        recent_energy = sum(f.get('energy', 0.5) for f in recent_features) / len(recent_features)
        older_energy = sum(f.get('energy', 0.5) for f in older_features) / len(older_features)

        energy_change = recent_energy - older_energy

        trend_desc = []
        if abs(energy_change) > 0.2:
            trend_desc.append(f"{'Increasing' if energy_change > 0 else 'Decreasing'} energy preference")

        return {
            'energy_change': energy_change,
            'description': ', '.join(trend_desc) if trend_desc else 'Stable preferences'
        }

    def _analyze_mood_patterns(self, long_term: LongTermMemory) -> Dict:
        """Analyze mood patterns from audio features"""
        audio_prefs = long_term.profile['audio_feature_preferences']

        if not audio_prefs:
            return {'description': 'No mood patterns identified yet'}

        patterns = {}

        # Energy level
        if 'energy' in audio_prefs:
            energy = audio_prefs['energy']['mean']
            if energy > 0.7:
                patterns['energy_level'] = 'high'
            elif energy < 0.3:
                patterns['energy_level'] = 'low'
            else:
                patterns['energy_level'] = 'moderate'

        # Mood (valence)
        if 'valence' in audio_prefs:
            valence = audio_prefs['valence']['mean']
            if valence > 0.7:
                patterns['mood'] = 'positive'
            elif valence < 0.3:
                patterns['mood'] = 'melancholic'
            else:
                patterns['mood'] = 'neutral'

        # Danceability
        if 'danceability' in audio_prefs:
            dance = audio_prefs['danceability']['mean']
            patterns['danceability'] = 'high' if dance > 0.7 else 'low' if dance < 0.3 else 'moderate'

        return patterns

    def get_recommendation_context(self, user_id: int,
                                  short_term_memory: ShortTermMemory = None) -> str:
        """
        Get recommendation context for CuratorAgent

        Returns:
            String with user preference context
        """
        analysis = self.analyze_user(user_id, short_term_memory)

        context = f"User Profile Summary: {analysis['natural_language_summary']}\n"

        # Add genre preferences
        if analysis['genre_preferences']:
            top_genres = sorted(
                analysis['genre_preferences'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            genres_str = ", ".join([f"{g} ({w:.2f})" for g, w in top_genres])
            context += f"Top genres: {genres_str}\n"

        # Add audio feature preferences
        audio_prefs = analysis['audio_feature_preferences']
        if audio_prefs:
            feature_str = []
            for feature in ['energy', 'valence', 'danceability']:
                if feature in audio_prefs:
                    mean = audio_prefs[feature]['mean']
                    feature_str.append(f"{feature}={mean:.2f}")

            if feature_str:
                context += f"Audio preferences: {', '.join(feature_str)}\n"

        # Add session context if available
        if 'session_context' in analysis:
            session = analysis['session_context']
            if session['recent_queries']:
                context += f"Recent queries: {', '.join(session['recent_queries'][-2:])}\n"

        return context


# Convenience function
def get_analyzer_agent() -> AnalyzerAgent:
    """Get AnalyzerAgent instance"""
    return AnalyzerAgent()


# Testing
if __name__ == "__main__":
    print("Testing Analyzer Agent\n" + "="*60)

    agent = AnalyzerAgent()
    db = QdrantStorage()

    # Create test user if doesn't exist
    user = db.get_user(username="test_user")
    if not user:
        user_id = db.create_user("test_user")
        print(f"Created test user with ID: {user_id}")
    else:
        user_id = user['id']
        print(f"Using existing user ID: {user_id}")

    # Analyze user
    analysis = agent.analyze_user(user_id)

    print(f"\n{'='*60}")
    print("User Analysis:")
    print(f"{'='*60}")
    print(f"Profile Summary: {analysis['profile_summary']}")
    print(f"\nTotal Interactions: {analysis['total_interactions']}")

    if analysis['genre_preferences']:
        print(f"\nGenre Preferences:")
        for genre, weight in list(analysis['genre_preferences'].items())[:5]:
            print(f"  {genre}: {weight:.3f}")

    print(f"\n{'='*60}")
    print("Analyzer agent test complete!")
