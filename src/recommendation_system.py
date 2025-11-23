"""
Main Recommendation System Orchestrator
Coordinates all agents and components
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime
from src.agents.retriever import RetrieverAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.curator import CuratorAgent
from src.agents.critic import CriticAgent
from src.memory.short_term import get_short_term_memory, ShortTermMemory
from src.memory.long_term import get_long_term_memory
from src.database.sqlite_manager import SQLiteManager


class MusicRecommendationSystem:
    """Main orchestrator for multi-agent recommendation system"""

    def __init__(self):
        # Initialize agents
        self.retriever = RetrieverAgent()
        self.analyzer = AnalyzerAgent()
        self.curator = CuratorAgent()
        self.critic = CriticAgent()

        # Initialize database
        self.db = SQLiteManager()

    def get_recommendations(self, user_id: int, query: str,
                           session_id: str = None,
                           genre_filter: str = None,
                           enable_time_matching: bool = True,
                           enable_reranking: bool = True) -> Dict:
        """
        Get music recommendations through multi-agent pipeline

        Args:
            user_id: User ID
            query: Natural language query
            session_id: Optional session ID
            genre_filter: Optional genre filter
            enable_time_matching: Enable time-of-day matching
            enable_reranking: Enable Cohere reranking

        Returns:
            Dict with recommendations and full pipeline trace
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())

        print(f"\n{'='*80}")
        print(f"RECOMMENDATION PIPELINE - Session: {session_id}")
        print(f"{'='*80}")
        print(f"User: {user_id} | Query: '{query}'")

        # Initialize short-term memory for session
        short_term = get_short_term_memory(user_id, session_id)
        short_term.add_query(query)

        pipeline_trace = {
            'session_id': session_id,
            'user_id': user_id,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'stages': {}
        }

        # Stage 1: Retrieval
        print(f"\n{'='*80}")
        print("STAGE 1: RETRIEVAL")
        print(f"{'='*80}")

        retrieval_result = self.retriever.retrieve_with_expansion(
            query,
            use_enhancement=False,
            genre_filter=genre_filter
        )

        candidates = retrieval_result['candidates']
        pipeline_trace['stages']['retrieval'] = {
            'agent': 'RetrieverAgent',
            'candidates_count': len(candidates),
            'metadata': retrieval_result['metadata']
        }

        print(f"Retrieved {len(candidates)} candidates")

        if not candidates:
            return {
                'recommendations': [],
                'message': 'No songs found matching your query',
                'pipeline_trace': pipeline_trace
            }

        # Stage 2: Analysis
        print(f"\n{'='*80}")
        print("STAGE 2: USER ANALYSIS")
        print(f"{'='*80}")

        user_analysis = self.analyzer.analyze_user(user_id, short_term)
        pipeline_trace['stages']['analysis'] = {
            'agent': 'AnalyzerAgent',
            'profile_summary': user_analysis['profile_summary'],
            'total_interactions': user_analysis['total_interactions']
        }

        print(f"User profile: {user_analysis['profile_summary'][:100]}...")

        # Stage 3: Curation
        print(f"\n{'='*80}")
        print("STAGE 3: CURATION")
        print(f"{'='*80}")

        curation_result = self.curator.curate_recommendations(
            candidates,
            query,
            user_analysis,
            user_id,
            enable_time_matching=enable_time_matching,
            enable_reranking=enable_reranking
        )

        recommendations = curation_result['recommendations']
        pipeline_trace['stages']['curation'] = {
            'agent': 'CuratorAgent',
            'final_count': len(recommendations),
            'metadata': curation_result['metadata'],
            'reasoning': curation_result['reasoning']
        }

        print(f"Curated {len(recommendations)} final recommendations")

        # Stage 4: Critique
        print(f"\n{'='*80}")
        print("STAGE 4: EVALUATION")
        print(f"{'='*80}")

        evaluation = self.critic.evaluate_recommendations(
            recommendations,
            query,
            user_analysis
        )

        pipeline_trace['stages']['critique'] = {
            'agent': 'CriticAgent',
            'diversity_score': evaluation['diversity_score'],
            'quality_score': evaluation['quality_score'],
            'issues_count': len(evaluation['issues']),
            'feedback': evaluation['feedback']
        }

        print(f"Evaluation: Diversity={evaluation['diversity_score']:.2f}, Quality={evaluation['quality_score']:.2f}")

        # Save recommendation session
        recommended_song_ids = [song['id'] for song in recommendations]
        self.db.save_recommendation(
            session_id=session_id,
            user_id=user_id,
            recommended_songs=recommended_song_ids,
            agent_reasoning=curation_result['reasoning']
        )

        # Save to short-term memory
        short_term.save_to_database()

        print(f"\n{'='*80}")
        print("PIPELINE COMPLETE")
        print(f"{'='*80}\n")

        return {
            'success': True,
            'recommendations': recommendations,
            'evaluation': evaluation,
            'pipeline_trace': pipeline_trace,
            'session_id': session_id
        }

    def record_feedback(self, user_id: int, song_id: int,
                       rating: int = None, action_type: str = 'view',
                       session_id: str = None):
        """
        Record user feedback on a recommendation

        Args:
            user_id: User ID
            song_id: Song ID
            rating: Optional rating (1-5)
            action_type: Type of action (like, dislike, play, save, skip, view)
            session_id: Optional session ID
        """
        # Record interaction in database
        self.db.add_interaction(user_id, song_id, action_type, rating)

        # Update short-term memory if session active
        if session_id:
            short_term = get_short_term_memory(user_id, session_id)
            short_term.add_interaction(song_id, action_type, rating)
            short_term.save_to_database()

        # Update long-term memory periodically
        long_term = get_long_term_memory(user_id, auto_update=True)

        print(f"Recorded feedback: User {user_id}, Song {song_id}, Action: {action_type}, Rating: {rating}")

    def get_user_profile(self, user_id: int) -> Dict:
        """Get user profile summary"""
        long_term = get_long_term_memory(user_id, auto_update=True)
        return long_term.get_full_profile()

    def get_session_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recommendation history"""
        return self.db.get_recommendations(user_id=user_id)[:limit]


# Convenience function
def get_recommendation_system() -> MusicRecommendationSystem:
    """Get MusicRecommendationSystem instance"""
    return MusicRecommendationSystem()


# Testing
if __name__ == "__main__":
    print("Testing Music Recommendation System\n" + "="*80)

    system = MusicRecommendationSystem()
    db = SQLiteManager()

    # Create or get test user
    user = db.get_user(username="test_user")
    if not user:
        user_id = db.create_user("test_user")
        print(f"Created test user with ID: {user_id}")
    else:
        user_id = user['id']
        print(f"Using existing user ID: {user_id}")

    # Test recommendation
    print("\nTesting recommendation pipeline...")

    try:
        result = system.get_recommendations(
            user_id=user_id,
            query="upbeat songs for working out",
            enable_time_matching=True,
            enable_reranking=False  # Disable for testing without Cohere
        )

        if result['success']:
            print(f"\n{'='*80}")
            print("RECOMMENDATION RESULTS")
            print(f"{'='*80}")

            print(f"\nFound {len(result['recommendations'])} recommendations")

            print("\nTop 5:")
            for i, song in enumerate(result['recommendations'][:5], 1):
                print(f"{i}. {song['name']} by {song['artist']}")
                print(f"   Genre: {song['genre']}, Score: {song.get('score', 0):.3f}")

            print(f"\nDiversity Score: {result['evaluation']['diversity_score']:.2f}")
            print(f"Quality Score: {result['evaluation']['quality_score']:.2f}")

            print(f"\n{result['evaluation']['feedback']}")

        else:
            print("Recommendation failed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*80}")
    print("System test complete!")
