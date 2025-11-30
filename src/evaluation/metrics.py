"""
Evaluation Metrics for Music Recommendation System
Includes: Precision@K, Diversity, Coverage, User Satisfaction, Query Relevance
"""

import numpy as np
from typing import List, Dict, Set, Optional
from collections import Counter, defaultdict
from sklearn.metrics import ndcg_score
import config
from src.database.qdrant_storage import QdrantStorage
from src.utils.audio_features import extract_features_from_song


class RecommendationMetrics:
    """Evaluation metrics for recommendation system"""

    def __init__(self):
        self.db = QdrantStorage()

    def precision_at_k(self, recommended: List[int], relevant: List[int], k: int) -> float:
        """
        Calculate Precision@K

        Args:
            recommended: List of recommended song IDs
            relevant: List of relevant (liked) song IDs
            k: Number of recommendations to consider

        Returns:
            Precision@K score (0-1)
        """
        if k == 0 or not recommended:
            return 0.0

        recommended_k = set(recommended[:k])
        relevant_set = set(relevant)

        hits = len(recommended_k.intersection(relevant_set))
        precision = hits / k

        return precision

    def calculate_diversity_score(self, recommendations: List[Dict]) -> float:
        """
        Calculate diversity score based on:
        - Genre diversity
        - Artist diversity
        - Audio feature diversity

        Returns:
            Diversity score (0-1)
        """
        if not recommendations:
            return 0.0

        scores = []

        # Genre diversity
        genres = [song.get('genre', 'unknown') for song in recommendations]
        unique_genres = len(set(genres))
        genre_diversity = unique_genres / len(genres) if genres else 0
        scores.append(genre_diversity)

        # Artist diversity
        artists = [song.get('artist', 'unknown') for song in recommendations]
        unique_artists = len(set(artists))
        artist_diversity = unique_artists / len(artists) if artists else 0
        scores.append(artist_diversity)

        # Audio feature diversity (standard deviation of energy and valence)
        energies = []
        valences = []

        for song in recommendations:
            features = song.get('features', {})
            if features:
                energies.append(features.get('energy', 0.5))
                valences.append(features.get('valence', 0.5))

        if energies and valences:
            energy_std = np.std(energies)
            valence_std = np.std(valences)

            # Normalize: std of 0.2 or more is considered diverse
            energy_diversity = min(1.0, energy_std / 0.2)
            valence_diversity = min(1.0, valence_std / 0.2)

            scores.append((energy_diversity + valence_diversity) / 2)

        overall_diversity = np.mean(scores) if scores else 0.0

        return float(overall_diversity)

    def calculate_coverage(self, all_recommendations: List[List[int]],
                          catalog_size: int) -> float:
        """
        Calculate catalog coverage

        Args:
            all_recommendations: List of recommendation lists (song IDs)
            catalog_size: Total number of songs in catalog

        Returns:
            Coverage score (0-1)
        """
        if catalog_size == 0:
            return 0.0

        # Get all unique recommended songs
        all_recommended = set()
        for rec_list in all_recommendations:
            all_recommended.update(rec_list)

        coverage = len(all_recommended) / catalog_size

        return float(coverage)

    def calculate_user_satisfaction(self, user_id: int,
                                   recommended_songs: List[int]) -> float:
        """
        Calculate user satisfaction based on ratings

        Args:
            user_id: User ID
            recommended_songs: List of recommended song IDs

        Returns:
            Satisfaction score (0-1)
        """
        interactions = self.db.get_user_interactions(user_id)

        if not interactions:
            return 0.5  # Neutral for no data

        # Get ratings for recommended songs
        ratings = []
        interaction_dict = {i['song_id']: i for i in interactions}

        for song_id in recommended_songs:
            if song_id in interaction_dict:
                rating = interaction_dict[song_id].get('rating')
                if rating:
                    # Normalize rating to 0-1 (assuming 1-5 scale)
                    normalized = (rating - 1) / 4
                    ratings.append(normalized)

        if not ratings:
            return 0.5  # Neutral if no ratings

        satisfaction = np.mean(ratings)

        return float(satisfaction)

    def calculate_ndcg(self, recommended: List[int], relevant_scores: Dict[int, float],
                      k: int = 10) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain (NDCG@K)

        Args:
            recommended: List of recommended song IDs
            relevant_scores: Dict mapping song_id to relevance score (0-1)
            k: Number of recommendations to consider

        Returns:
            NDCG@K score
        """
        if k == 0 or not recommended:
            return 0.0

        recommended_k = recommended[:k]

        # Get relevance scores for recommended items
        y_true = []
        y_score = []

        for song_id in recommended_k:
            score = relevant_scores.get(song_id, 0.0)
            y_true.append(score)
            y_score.append(1.0)  # Ranking is based on recommendation order

        if not y_true or sum(y_true) == 0:
            return 0.0

        try:
            ndcg = ndcg_score([y_true], [y_score])
            return float(ndcg)
        except:
            return 0.0

    def calculate_query_relevance(self, recommendations: List[Dict],
                                  target_features: Dict[str, float],
                                  feature_weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate how well recommendations match target audio features.

        This metric measures whether recommendations align with the
        expected characteristics for a given query type.

        Args:
            recommendations: List of recommended song dictionaries
            target_features: Dict of target feature values (e.g., {'energy': 0.8, 'valence': 0.7})
            feature_weights: Optional weights for each feature (defaults to equal weights)

        Returns:
            Query relevance score (0-1)
        """
        if not recommendations or not target_features:
            return 0.0

        if feature_weights is None:
            feature_weights = {f: 1.0 for f in target_features.keys()}

        song_scores = []

        for song in recommendations:
            features = extract_features_from_song(song)
            feature_scores = []
            weights = []

            for feature_name, target_value in target_features.items():
                if feature_name in features:
                    song_value = features[feature_name]

                    # Calculate similarity based on feature type
                    if feature_name == 'tempo':
                        # Tempo: larger range, use relative difference
                        diff = abs(song_value - target_value) / max(target_value, 1)
                        similarity = max(0, 1 - diff)
                    else:
                        # 0-1 scaled features: use absolute difference
                        diff = abs(song_value - target_value)
                        similarity = max(0, 1 - diff)

                    feature_scores.append(similarity)
                    weights.append(feature_weights.get(feature_name, 1.0))

            if feature_scores:
                song_score = np.average(feature_scores, weights=weights)
                song_scores.append(song_score)

        return float(np.mean(song_scores)) if song_scores else 0.0

    def calculate_lyrics_relevance(self, recommendations: List[Dict],
                                   themes: List[str]) -> float:
        """
        Calculate how well recommendation lyrics match expected themes.

        Args:
            recommendations: List of recommended song dictionaries
            themes: List of theme keywords to look for

        Returns:
            Lyrics relevance score (0-1)
        """
        if not recommendations or not themes:
            return 0.0

        songs_with_lyrics = 0
        theme_scores = []

        for song in recommendations:
            lyrics = (song.get('lyrics_preview') or '').lower()

            if lyrics:
                songs_with_lyrics += 1
                # Count theme matches
                matches = sum(1 for theme in themes if theme.lower() in lyrics)
                # Score: proportion of themes found (with bonus for multiple matches)
                score = min(1.0, matches / max(len(themes) * 0.3, 1))
                theme_scores.append(score)

        if not theme_scores:
            return 0.0

        # Factor in lyrics coverage
        coverage_bonus = songs_with_lyrics / len(recommendations)

        return float(np.mean(theme_scores) * (0.7 + 0.3 * coverage_bonus))

    def evaluate_recommendations(self, user_id: int, recommended: List[Dict],
                                k_values: List[int] = None) -> Dict:
        """
        Comprehensive evaluation of recommendations

        Returns:
            Dict with all metrics
        """
        if k_values is None:
            k_values = config.PRECISION_K_VALUES

        # Get user's liked songs
        interactions = self.db.get_user_interactions(user_id)
        liked_songs = [i['song_id'] for i in interactions
                      if i.get('rating') and i['rating'] >= 4]

        recommended_ids = [song.get('song_id', song.get('spotify_id', '')) for song in recommended]

        metrics = {
            'user_id': user_id,
            'num_recommendations': len(recommended),
            'precision_at_k': {},
            'diversity_score': self.calculate_diversity_score(recommended),
            'user_satisfaction': self.calculate_user_satisfaction(user_id, recommended_ids)
        }

        # Calculate precision@k for different k values
        for k in k_values:
            metrics['precision_at_k'][f'p@{k}'] = self.precision_at_k(
                recommended_ids, liked_songs, k
            )

        return metrics


class ABTesting:
    """A/B testing framework for comparing recommendation strategies"""

    def __init__(self):
        self.db = QdrantStorage()

    def compare_strategies(self, user_id: int, strategy_a_recs: List[Dict],
                          strategy_b_recs: List[Dict],
                          strategy_a_name: str = "Strategy A",
                          strategy_b_name: str = "Strategy B") -> Dict:
        """
        Compare two recommendation strategies

        Returns:
            Dict with comparison results
        """
        metrics = RecommendationMetrics()

        eval_a = metrics.evaluate_recommendations(user_id, strategy_a_recs)
        eval_b = metrics.evaluate_recommendations(user_id, strategy_b_recs)

        comparison = {
            'user_id': user_id,
            'strategies': {
                strategy_a_name: eval_a,
                strategy_b_name: eval_b
            },
            'winner': {},
            'summary': {}
        }

        # Compare diversity
        if eval_a['diversity_score'] > eval_b['diversity_score']:
            comparison['winner']['diversity'] = strategy_a_name
        else:
            comparison['winner']['diversity'] = strategy_b_name

        # Compare satisfaction
        if eval_a['user_satisfaction'] > eval_b['user_satisfaction']:
            comparison['winner']['satisfaction'] = strategy_a_name
        else:
            comparison['winner']['satisfaction'] = strategy_b_name

        # Summary
        comparison['summary'] = {
            'diversity_diff': eval_a['diversity_score'] - eval_b['diversity_score'],
            'satisfaction_diff': eval_a['user_satisfaction'] - eval_b['user_satisfaction']
        }

        return comparison

    def test_with_without_reranker(self, user_id: int, query: str,
                                   candidates: List[Dict]) -> Dict:
        """
        Test recommendations with and without reranker

        Args:
            user_id: User ID
            query: User query
            candidates: Candidate songs

        Returns:
            Comparison results
        """
        from src.agents.curator import CuratorAgent
        from src.agents.analyzer import AnalyzerAgent

        curator = CuratorAgent()
        analyzer = AnalyzerAgent()

        # Get user analysis
        user_analysis = analyzer.analyze_user(user_id)

        # Without reranker
        result_without = curator.curate_recommendations(
            candidates, query, user_analysis, user_id,
            enable_reranking=False
        )

        # With reranker
        result_with = curator.curate_recommendations(
            candidates, query, user_analysis, user_id,
            enable_reranking=True
        )

        # Compare
        comparison = self.compare_strategies(
            user_id,
            result_without['recommendations'],
            result_with['recommendations'],
            "Without Reranker",
            "With Reranker"
        )

        return comparison

    def test_with_without_time_matching(self, user_id: int, query: str,
                                       candidates: List[Dict]) -> Dict:
        """
        Test recommendations with and without time-of-day matching

        Returns:
            Comparison results
        """
        from src.agents.curator import CuratorAgent
        from src.agents.analyzer import AnalyzerAgent

        curator = CuratorAgent()
        analyzer = AnalyzerAgent()

        user_analysis = analyzer.analyze_user(user_id)

        # Without time matching
        result_without = curator.curate_recommendations(
            candidates, query, user_analysis, user_id,
            enable_time_matching=False
        )

        # With time matching
        result_with = curator.curate_recommendations(
            candidates, query, user_analysis, user_id,
            enable_time_matching=True
        )

        comparison = self.compare_strategies(
            user_id,
            result_without['recommendations'],
            result_with['recommendations'],
            "Without Time Matching",
            "With Time Matching"
        )

        return comparison


# Convenience functions
def get_metrics() -> RecommendationMetrics:
    """Get RecommendationMetrics instance"""
    return RecommendationMetrics()


def get_ab_testing() -> ABTesting:
    """Get ABTesting instance"""
    return ABTesting()


# Testing
if __name__ == "__main__":
    print("Testing Evaluation Metrics\n" + "="*60)

    metrics = RecommendationMetrics()

    # Test precision@k
    recommended = [1, 2, 3, 4, 5]
    relevant = [2, 4, 6, 8]

    print("\nPrecision@K Test:")
    for k in [3, 5, 10]:
        p_at_k = metrics.precision_at_k(recommended, relevant, k)
        print(f"  Precision@{k}: {p_at_k:.3f}")

    # Test diversity
    sample_recommendations = [
        {'genre': 'pop', 'artist': 'Artist A', 'features': {'energy': 0.8, 'valence': 0.9}},
        {'genre': 'rock', 'artist': 'Artist B', 'features': {'energy': 0.7, 'valence': 0.6}},
        {'genre': 'pop', 'artist': 'Artist C', 'features': {'energy': 0.6, 'valence': 0.8}},
    ]

    diversity = metrics.calculate_diversity_score(sample_recommendations)
    print(f"\nDiversity Score: {diversity:.3f}")

    # Test coverage
    all_recs = [[1, 2, 3], [2, 3, 4], [5, 6, 7]]
    catalog_size = 100

    coverage = metrics.calculate_coverage(all_recs, catalog_size)
    print(f"Coverage: {coverage:.3f}")

    print(f"\n{'='*60}")
    print("Metrics test complete!")
