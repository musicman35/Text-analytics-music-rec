"""
Curator Agent
Curates final recommendations using scoring, time-matching, and reranking
"""

from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
import numpy as np
from datetime import datetime
import config
from src.tools.time_of_day_matcher import TimeOfDayMatcher
from src.reranker.cohere_reranker import CohereReranker
from src.memory.long_term import get_long_term_memory


class CuratorAgent:
    """Agent that curates and ranks recommendations"""

    def __init__(self):
        self.time_matcher = TimeOfDayMatcher()
        self.reranker = CohereReranker()
        self.final_count = config.FINAL_RECOMMENDATION_COUNT
        self.prerank_count = config.CURATOR_PRERANK_COUNT

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.AGENT_LLM_MODEL,
            temperature=config.AGENT_TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )

    def curate_recommendations(self, candidates: List[Dict], user_query: str,
                              user_analysis: Dict, user_id: int,
                              enable_time_matching: bool = True,
                              enable_reranking: bool = True) -> Dict:
        """
        Curate final recommendations through multi-step process

        Steps:
        1. Apply collaborative filtering logic
        2. Integrate time-of-day matching
        3. Score candidates
        4. Rerank top candidates using Cohere
        5. Select final recommendations

        Returns:
            Dict with recommendations and reasoning
        """
        print(f"\n[CuratorAgent] Curating recommendations from {len(candidates)} candidates")

        # Step 1: Apply collaborative filtering (user profile matching)
        scored_candidates = self._apply_collaborative_filtering(
            candidates, user_id, user_analysis
        )

        # Step 2: Apply time-of-day adjustments
        if enable_time_matching:
            scored_candidates = self._apply_time_matching(scored_candidates)

        # Step 3: Get top candidates for reranking
        top_candidates = sorted(
            scored_candidates,
            key=lambda x: x['score'],
            reverse=True
        )[:self.prerank_count]

        print(f"[CuratorAgent] Selected top {len(top_candidates)} for reranking")

        # Step 4: Rerank using Cohere
        if enable_reranking and len(top_candidates) > 0:
            user_profile_summary = user_analysis.get('natural_language_summary', '')
            reranked = self.reranker.rerank(
                top_candidates,
                user_query,
                user_profile_summary,
                top_n=self.final_count
            )
            final_recommendations = reranked
        else:
            # Without reranking, just take top N
            final_recommendations = top_candidates[:self.final_count]

        # Generate reasoning
        reasoning = self._generate_reasoning(
            final_recommendations,
            user_query,
            user_analysis,
            enable_time_matching,
            enable_reranking
        )

        print(f"[CuratorAgent] Final recommendations: {len(final_recommendations)}")

        return {
            'recommendations': final_recommendations,
            'reasoning': reasoning,
            'metadata': {
                'total_candidates': len(candidates),
                'prerank_count': len(top_candidates),
                'final_count': len(final_recommendations),
                'time_matching_enabled': enable_time_matching,
                'reranking_enabled': enable_reranking,
                'time_period': self.time_matcher.get_time_period() if enable_time_matching else None
            }
        }

    def _apply_collaborative_filtering(self, candidates: List[Dict],
                                       user_id: int, user_analysis: Dict) -> List[Dict]:
        """
        Apply collaborative filtering based on user profile

        Scoring factors:
        - Semantic similarity (from retrieval)
        - User profile match
        - Genre preference
        - Artist preference
        """
        print(f"[CuratorAgent] Applying collaborative filtering")

        long_term = get_long_term_memory(user_id, auto_update=False)

        scored = []
        for candidate in candidates:
            song = candidate.copy()

            # Base score from semantic search
            semantic_score = song.get('score', 0.5)

            # User profile match score
            profile_score = long_term.calculate_song_match_score(
                song['features'],
                song.get('genre'),
                song.get('artist')
            )

            # Genre preference score
            genre_score = long_term.get_genre_preference(song.get('genre', ''))

            # Combined score using feature weights
            weights = config.FEATURE_WEIGHTS
            combined_score = (
                semantic_score * weights['semantic_similarity'] +
                profile_score * weights['user_preference'] +
                genre_score * weights['audio_features']
            )

            song['semantic_score'] = semantic_score
            song['profile_score'] = profile_score
            song['genre_score'] = genre_score
            song['score'] = combined_score

            scored.append(song)

        return scored

    def _apply_time_matching(self, candidates: List[Dict]) -> List[Dict]:
        """Apply time-of-day adjustments to scores"""
        print(f"[CuratorAgent] Applying time-of-day matching")

        time_context = self.time_matcher.get_time_context()
        print(f"[CuratorAgent] Current time: {time_context['hour']}:00 ({time_context['period']})")

        adjusted = self.time_matcher.boost_songs_by_time(candidates)

        return adjusted

    def _generate_reasoning(self, recommendations: List[Dict], query: str,
                          user_analysis: Dict, time_matching: bool,
                          reranking: bool) -> Dict:
        """Generate reasoning for recommendations"""
        reasoning = {
            'query': query,
            'user_profile': user_analysis.get('profile_summary', 'New user'),
            'steps': []
        }

        # Step descriptions
        reasoning['steps'].append({
            'step': 'Semantic Retrieval',
            'description': f'Retrieved candidates based on query relevance'
        })

        reasoning['steps'].append({
            'step': 'Collaborative Filtering',
            'description': 'Scored candidates based on user profile and preferences'
        })

        if time_matching:
            time_context = self.time_matcher.get_time_context()
            reasoning['steps'].append({
                'step': 'Time-of-Day Matching',
                'description': f'Adjusted for {time_context["period"]} listening ({time_context["description"]})'
            })

        if reranking:
            reasoning['steps'].append({
                'step': 'Cohere Reranking',
                'description': 'Optimized ordering using semantic reranking'
            })

        # Per-song reasoning
        song_reasoning = []
        for i, song in enumerate(recommendations, 1):
            reasons = []

            # Semantic match
            if song.get('semantic_score', 0) > 0.7:
                reasons.append("High semantic match to query")

            # Profile match
            if song.get('profile_score', 0) > 0.7:
                reasons.append("Matches your taste profile")

            # Genre
            if song.get('genre_score', 0) > 0.6:
                reasons.append(f"You enjoy {song.get('genre', 'this')} music")

            # Time match
            if time_matching and song.get('time_adjusted_score'):
                orig_score = song.get('original_score', 0)
                new_score = song.get('time_adjusted_score', 0)
                if new_score > orig_score:
                    reasons.append(f"Good for {song.get('time_period', 'current')} listening")

            # Reranking
            if reranking and song.get('rerank_score'):
                reasons.append(f"Relevance score: {song['rerank_score']:.2f}")

            song_reasoning.append({
                'position': i,
                'song': f"{song['name']} by {song['artist']}",
                'reasons': reasons if reasons else ['Matches your query']
            })

        reasoning['song_explanations'] = song_reasoning

        return reasoning

    def explain_recommendation(self, song: Dict, position: int) -> str:
        """Generate natural language explanation for a single recommendation"""
        explanation = f"#{position}: {song['name']} by {song['artist']}\n"

        reasons = []

        if song.get('semantic_score', 0) > 0.7:
            reasons.append("- Highly relevant to your search")

        if song.get('profile_score', 0) > 0.7:
            reasons.append("- Matches your listening preferences")

        if song.get('genre'):
            reasons.append(f"- {song['genre'].capitalize()} genre")

        if song.get('rerank_score'):
            reasons.append(f"- Relevance score: {song['rerank_score']:.2f}")

        if reasons:
            explanation += "\n".join(reasons)

        return explanation


# Convenience function
def get_curator_agent() -> CuratorAgent:
    """Get CuratorAgent instance"""
    return CuratorAgent()


# Testing
if __name__ == "__main__":
    print("Testing Curator Agent\n" + "="*60)

    # Sample candidates (mimicking RetrieverAgent output)
    sample_candidates = [
        {
            'id': 1,
            'name': 'Song A',
            'artist': 'Artist 1',
            'genre': 'pop',
            'score': 0.85,
            'features': {
                'energy': 0.8,
                'valence': 0.9,
                'danceability': 0.75,
                'acousticness': 0.1,
                'instrumentalness': 0.0,
                'speechiness': 0.05,
                'tempo': 120,
                'loudness': -5
            }
        },
        {
            'id': 2,
            'name': 'Song B',
            'artist': 'Artist 2',
            'genre': 'pop',
            'score': 0.80,
            'features': {
                'energy': 0.7,
                'valence': 0.8,
                'danceability': 0.70,
                'acousticness': 0.2,
                'instrumentalness': 0.0,
                'speechiness': 0.06,
                'tempo': 115,
                'loudness': -6
            }
        }
    ]

    # Sample user analysis
    sample_analysis = {
        'profile_summary': 'User enjoys upbeat pop music with high energy',
        'natural_language_summary': 'This user prefers energetic, positive pop songs',
        'genre_preferences': {'pop': 0.8, 'rock': 0.2},
        'audio_feature_preferences': {
            'energy': {'mean': 0.75},
            'valence': {'mean': 0.8}
        }
    }

    curator = CuratorAgent()

    result = curator.curate_recommendations(
        candidates=sample_candidates,
        user_query="upbeat songs for working out",
        user_analysis=sample_analysis,
        user_id=1,
        enable_time_matching=True,
        enable_reranking=False  # Disable for testing without Cohere
    )

    print(f"\n{'='*60}")
    print("Curation Results:")
    print(f"{'='*60}")
    print(f"Final recommendations: {len(result['recommendations'])}")
    print(f"\nReasoning steps:")
    for step in result['reasoning']['steps']:
        print(f"  - {step['step']}: {step['description']}")

    print(f"\n{'='*60}")
    print("Curator agent test complete!")
