"""
Critic Agent
Evaluates recommendations and provides explanations and feedback
"""

from typing import List, Dict
from langchain_openai import ChatOpenAI
from collections import Counter
import numpy as np
import config


class CriticAgent:
    """Agent that evaluates and critiques recommendations"""

    def __init__(self):
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.AGENT_LLM_MODEL,
            temperature=config.AGENT_TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )

    def evaluate_recommendations(self, recommendations: List[Dict],
                                user_query: str, user_analysis: Dict) -> Dict:
        """
        Evaluate the quality of recommendations

        Returns:
            Dict with evaluation results and feedback
        """
        print(f"\n[CriticAgent] Evaluating {len(recommendations)} recommendations")

        evaluation = {
            'diversity_score': self._evaluate_diversity(recommendations),
            'quality_score': self._evaluate_quality(recommendations),
            'issues': self._identify_issues(recommendations, user_analysis),
            'explanations': self._generate_explanations(recommendations, user_query, user_analysis),
            'feedback': None
        }

        # Generate overall feedback
        evaluation['feedback'] = self._generate_feedback(evaluation, user_query)

        print(f"[CriticAgent] Diversity score: {evaluation['diversity_score']:.2f}")
        print(f"[CriticAgent] Quality score: {evaluation['quality_score']:.2f}")
        print(f"[CriticAgent] Issues found: {len(evaluation['issues'])}")

        return evaluation

    def _evaluate_diversity(self, recommendations: List[Dict]) -> float:
        """
        Evaluate diversity of recommendations

        Checks:
        - Genre variety
        - Artist variety
        - Audio feature variety
        """
        if not recommendations:
            return 0.0

        scores = []

        # Genre diversity
        genres = [song.get('genre', 'unknown') for song in recommendations]
        unique_genres = len(set(genres))
        genre_diversity = unique_genres / len(genres)
        scores.append(genre_diversity)

        # Artist diversity
        artists = [song.get('artist', 'unknown') for song in recommendations]
        unique_artists = len(set(artists))
        artist_diversity = unique_artists / len(artists)
        scores.append(artist_diversity)

        # Audio feature diversity (energy variance)
        energies = [song.get('energy', 0.5) for song in recommendations]
        if energies:
            energy_std = np.std(energies)
            # Normalize: std of 0.2 or more is considered diverse
            energy_diversity = min(1.0, energy_std / 0.2)
            scores.append(energy_diversity)

        overall_diversity = np.mean(scores)

        return float(overall_diversity)

    def _evaluate_quality(self, recommendations: List[Dict]) -> float:
        """
        Evaluate quality based on scores

        Higher retrieval scores and rerank scores indicate better quality
        """
        if not recommendations:
            return 0.0

        quality_scores = []

        for song in recommendations:
            # Use rerank score if available, otherwise use base score
            score = song.get('rerank_score', song.get('score', 0.5))
            quality_scores.append(score)

        # Average quality
        avg_quality = np.mean(quality_scores)

        # Penalty for low variance (all same quality)
        variance_bonus = min(0.2, np.std(quality_scores))

        overall_quality = avg_quality + variance_bonus

        return float(min(1.0, overall_quality))

    def _identify_issues(self, recommendations: List[Dict], user_analysis: Dict) -> List[Dict]:
        """Identify potential issues with recommendations"""
        issues = []

        if not recommendations:
            issues.append({
                'type': 'no_recommendations',
                'severity': 'critical',
                'description': 'No recommendations were generated'
            })
            return issues

        # Check for artist repetition
        artists = [song.get('artist') for song in recommendations]
        artist_counts = Counter(artists)
        for artist, count in artist_counts.items():
            if count > 3:
                issues.append({
                    'type': 'artist_repetition',
                    'severity': 'medium',
                    'description': f'{artist} appears {count} times (over-represented)'
                })

        # Check for genre imbalance
        genres = [song.get('genre') for song in recommendations]
        genre_counts = Counter(genres)
        if len(genre_counts) == 1 and len(recommendations) > 5:
            issues.append({
                'type': 'genre_imbalance',
                'severity': 'low',
                'description': 'All recommendations are from the same genre'
            })

        # Check for similarity (too many similar energy levels)
        energies = [song.get('energy', 0.5) for song in recommendations]
        if energies:
            energy_std = np.std(energies)
            if energy_std < 0.1:
                issues.append({
                    'type': 'low_variety',
                    'severity': 'low',
                    'description': 'Songs have very similar energy levels'
                })

        # Check for misalignment with user preferences
        if user_analysis.get('genre_preferences'):
            top_user_genres = set(list(user_analysis['genre_preferences'].keys())[:3])
            rec_genres = set(genres)

            if not top_user_genres.intersection(rec_genres):
                issues.append({
                    'type': 'genre_mismatch',
                    'severity': 'medium',
                    'description': 'Recommendations don\'t match user\'s preferred genres'
                })

        return issues

    def _generate_explanations(self, recommendations: List[Dict],
                               user_query: str, user_analysis: Dict) -> List[Dict]:
        """Generate explanations for each recommendation"""
        explanations = []

        for i, song in enumerate(recommendations, 1):
            explanation = {
                'position': i,
                'song_name': song['name'],
                'artist': song['artist'],
                'reasons': []
            }

            # Query relevance
            semantic_score = song.get('semantic_score', song.get('score', 0))
            if semantic_score > 0.7:
                explanation['reasons'].append(
                    f"Highly relevant to your query: '{user_query}'"
                )

            # Genre match
            if song.get('genre') and user_analysis.get('genre_preferences'):
                user_genres = user_analysis['genre_preferences']
                if song['genre'] in user_genres and user_genres[song['genre']] > 0.5:
                    explanation['reasons'].append(
                        f"Matches your preference for {song['genre']} music"
                    )

            # Audio features
            energy = song.get('energy', 0.5)
            valence = song.get('valence', 0.5)

            if energy is not None or valence is not None:

                if energy > 0.7:
                    explanation['reasons'].append("High-energy track")
                elif energy < 0.3:
                    explanation['reasons'].append("Calm, low-energy track")

                if valence > 0.7:
                    explanation['reasons'].append("Positive, uplifting mood")
                elif valence < 0.3:
                    explanation['reasons'].append("Melancholic mood")

            # Time matching
            if song.get('time_period'):
                explanation['reasons'].append(
                    f"Suited for {song['time_period']} listening"
                )

            # Reranking score
            if song.get('rerank_score'):
                explanation['reasons'].append(
                    f"Relevance score: {song['rerank_score']:.2f}"
                )

            # Default if no specific reasons
            if not explanation['reasons']:
                explanation['reasons'].append("Matches your query")

            explanations.append(explanation)

        return explanations

    def _generate_feedback(self, evaluation: Dict, user_query: str) -> str:
        """Generate overall feedback on recommendations"""
        feedback_parts = []

        # Overall assessment
        diversity = evaluation['diversity_score']
        quality = evaluation['quality_score']

        if quality > 0.8 and diversity > 0.7:
            feedback_parts.append("Excellent recommendations with high quality and diversity.")
        elif quality > 0.6 and diversity > 0.5:
            feedback_parts.append("Good recommendations overall.")
        else:
            feedback_parts.append("Recommendations could be improved.")

        # Diversity feedback
        if diversity < 0.5:
            feedback_parts.append("Consider adding more variety in genres and artists.")
        elif diversity > 0.8:
            feedback_parts.append("Great variety across different genres and styles.")

        # Quality feedback
        if quality < 0.6:
            feedback_parts.append("Some recommendations may not be highly relevant to the query.")

        # Issues feedback
        issues = evaluation['issues']
        critical_issues = [i for i in issues if i['severity'] == 'critical']
        medium_issues = [i for i in issues if i['severity'] == 'medium']

        if critical_issues:
            feedback_parts.append(f"Critical issues: {len(critical_issues)} found.")

        if medium_issues:
            for issue in medium_issues[:2]:  # Mention top 2
                feedback_parts.append(issue['description'])

        return " ".join(feedback_parts)

    def generate_user_facing_explanation(self, song: Dict, position: int) -> str:
        """Generate user-friendly explanation for a single song"""
        lines = [f"**{position}. {song['name']}** by {song['artist']}"]

        # Genre and mood
        genre = song.get('genre', 'Unknown')

        mood_desc = []
        if song.get('energy', 0.5) > 0.7:
            mood_desc.append("energetic")
        if song.get('valence', 0.5) > 0.7:
            mood_desc.append("uplifting")
        elif song.get('valence', 0.5) < 0.3:
            mood_desc.append("melancholic")
        if song.get('danceability', 0.5) > 0.7:
            mood_desc.append("danceable")

        desc = f"{genre.capitalize()}"
        if mood_desc:
            desc += f" · {', '.join(mood_desc)}"

        lines.append(desc)

        # Why recommended
        reasons = []
        if song.get('semantic_score', 0) > 0.7:
            reasons.append("Matches your search")
        if song.get('profile_score', 0) > 0.7:
            reasons.append("Fits your taste")
        if song.get('rerank_score'):
            reasons.append(f"Relevance: {song['rerank_score']:.0%}")

        if reasons:
            lines.append("_" + " · ".join(reasons) + "_")

        return "\n".join(lines)


# Convenience function
def get_critic_agent() -> CriticAgent:
    """Get CriticAgent instance"""
    return CriticAgent()


# Testing
if __name__ == "__main__":
    print("Testing Critic Agent\n" + "="*60)

    # Sample recommendations
    sample_recommendations = [
        {
            'name': 'Song A',
            'artist': 'Artist 1',
            'genre': 'pop',
            'score': 0.85,
            'semantic_score': 0.85,
            'rerank_score': 0.90,
            'features': {'energy': 0.8, 'valence': 0.9, 'danceability': 0.75}
        },
        {
            'name': 'Song B',
            'artist': 'Artist 2',
            'genre': 'rock',
            'score': 0.80,
            'semantic_score': 0.80,
            'rerank_score': 0.85,
            'features': {'energy': 0.7, 'valence': 0.7, 'danceability': 0.60}
        },
        {
            'name': 'Song C',
            'artist': 'Artist 1',
            'genre': 'pop',
            'score': 0.75,
            'semantic_score': 0.75,
            'features': {'energy': 0.65, 'valence': 0.8, 'danceability': 0.70}
        }
    ]

    sample_user_analysis = {
        'profile_summary': 'User enjoys pop and rock music',
        'genre_preferences': {'pop': 0.7, 'rock': 0.3}
    }

    critic = CriticAgent()

    evaluation = critic.evaluate_recommendations(
        sample_recommendations,
        "upbeat songs for working out",
        sample_user_analysis
    )

    print(f"\n{'='*60}")
    print("Evaluation Results:")
    print(f"{'='*60}")
    print(f"Diversity Score: {evaluation['diversity_score']:.2f}")
    print(f"Quality Score: {evaluation['quality_score']:.2f}")
    print(f"\nOverall Feedback:")
    print(evaluation['feedback'])

    print(f"\n{'='*60}")
    print("Explanations:")
    for exp in evaluation['explanations']:
        print(f"\n{exp['position']}. {exp['song_name']} by {exp['artist']}")
        for reason in exp['reasons']:
            print(f"   - {reason}")

    if evaluation['issues']:
        print(f"\n{'='*60}")
        print("Issues Found:")
        for issue in evaluation['issues']:
            print(f"  [{issue['severity'].upper()}] {issue['description']}")

    print(f"\n{'='*60}")
    print("Critic agent test complete!")
