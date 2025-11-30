"""
Baseline Recommenders for Evaluation
Implements simple baselines to compare against the full recommendation system
"""

import random
from typing import List, Dict, Optional
import numpy as np
from src.database.qdrant_storage import QdrantStorage
from src.utils.audio_features import extract_features_from_song


class RandomBaseline:
    """Returns random songs from the catalog"""

    def __init__(self):
        self.db = QdrantStorage()
        self.name = "Random"

    def recommend(self, query: str, n: int = 10, **kwargs) -> List[Dict]:
        """
        Return n random songs from the catalog.

        Args:
            query: User query (ignored for random baseline)
            n: Number of recommendations to return

        Returns:
            List of random song dictionaries
        """
        # Get all songs from catalog by doing a broad search
        all_songs = self.db.search_songs(
            query="music song",  # Generic query to get songs
            limit=500  # Get a large sample
        )

        if len(all_songs) <= n:
            return all_songs

        # Randomly sample n songs
        selected = random.sample(all_songs, n)

        # Add baseline metadata
        for song in selected:
            song['baseline'] = 'random'
            song['score'] = random.random()  # Random score

        return selected


class PopularityBaseline:
    """Returns most popular songs (by popularity score)"""

    def __init__(self):
        self.db = QdrantStorage()
        self.name = "Popularity"

    def recommend(self, query: str, n: int = 10, **kwargs) -> List[Dict]:
        """
        Return top n most popular songs.

        Args:
            query: User query (ignored for popularity baseline)
            n: Number of recommendations to return

        Returns:
            List of most popular song dictionaries
        """
        # Get songs with a broad search
        all_songs = self.db.search_songs(
            query="music song",
            limit=500
        )

        # Sort by popularity score (descending)
        sorted_songs = sorted(
            all_songs,
            key=lambda x: x.get('popularity', 0),
            reverse=True
        )

        # Take top n
        selected = sorted_songs[:n]

        # Add baseline metadata
        for i, song in enumerate(selected):
            song['baseline'] = 'popularity'
            song['score'] = song.get('popularity', 0) / 100.0  # Normalize to 0-1
            song['rank'] = i + 1

        return selected


class ContentOnlyBaseline:
    """Pure audio feature matching without reranking or memory"""

    def __init__(self):
        self.db = QdrantStorage()
        self.name = "Content-Only"

    def recommend(self, query: str, n: int = 10,
                  target_features: Optional[Dict] = None, **kwargs) -> List[Dict]:
        """
        Return songs based on semantic similarity only (no reranking).

        Args:
            query: User query
            n: Number of recommendations to return
            target_features: Optional target audio features to match

        Returns:
            List of content-matched song dictionaries
        """
        # Do a direct semantic search without any post-processing
        candidates = self.db.search_songs(
            query=query,
            limit=n * 3  # Get more to allow feature filtering
        )

        if not candidates:
            return []

        # If target features provided, re-score based on feature similarity
        if target_features:
            scored_candidates = []
            for song in candidates:
                features = extract_features_from_song(song)
                feature_score = self._calculate_feature_similarity(features, target_features)
                song['feature_score'] = feature_score
                # Combine semantic score with feature score
                semantic_score = song.get('score', 0.5)
                song['combined_score'] = 0.6 * semantic_score + 0.4 * feature_score
                scored_candidates.append(song)

            # Re-sort by combined score
            scored_candidates.sort(key=lambda x: x['combined_score'], reverse=True)
            selected = scored_candidates[:n]
        else:
            # Just use semantic similarity
            selected = candidates[:n]

        # Add baseline metadata
        for song in selected:
            song['baseline'] = 'content_only'

        return selected

    def _calculate_feature_similarity(self, song_features: Dict,
                                      target_features: Dict) -> float:
        """Calculate similarity between song features and target features"""
        if not song_features or not target_features:
            return 0.5

        similarities = []

        for feature_name, target_value in target_features.items():
            if feature_name in song_features:
                song_value = song_features[feature_name]

                # Handle tempo differently (larger range)
                if feature_name == 'tempo':
                    # Normalize tempo difference (typical range 60-180)
                    diff = abs(song_value - target_value) / 120.0
                    similarity = max(0, 1 - diff)
                else:
                    # For 0-1 features
                    diff = abs(song_value - target_value)
                    similarity = 1 - diff

                similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.5


class GenreBaseline:
    """Returns songs from a specific genre"""

    def __init__(self):
        self.db = QdrantStorage()
        self.name = "Genre-Based"

    def recommend(self, query: str, n: int = 10,
                  target_genre: Optional[str] = None, **kwargs) -> List[Dict]:
        """
        Return songs from a specific genre.

        Args:
            query: User query
            n: Number of recommendations to return
            target_genre: Genre to filter by

        Returns:
            List of genre-matched song dictionaries
        """
        # Search with genre filter if provided
        if target_genre:
            candidates = self.db.search_songs(
                query=query,
                limit=n * 2,
                genre_filter=target_genre
            )
        else:
            candidates = self.db.search_songs(
                query=query,
                limit=n * 2
            )

        selected = candidates[:n]

        # Add baseline metadata
        for song in selected:
            song['baseline'] = 'genre_based'

        return selected


def get_all_baselines() -> List:
    """Return instances of all baseline recommenders"""
    return [
        RandomBaseline(),
        PopularityBaseline(),
        ContentOnlyBaseline()
    ]


def get_baseline_by_name(name: str):
    """Get a specific baseline by name"""
    baselines = {
        'random': RandomBaseline,
        'popularity': PopularityBaseline,
        'content_only': ContentOnlyBaseline,
        'genre': GenreBaseline
    }

    baseline_class = baselines.get(name.lower())
    if baseline_class:
        return baseline_class()

    raise ValueError(f"Unknown baseline: {name}. Available: {list(baselines.keys())}")


# Testing
if __name__ == "__main__":
    print("Testing Baseline Recommenders\n" + "="*60)

    # Test each baseline
    baselines = get_all_baselines()
    test_query = "upbeat songs for working out"

    for baseline in baselines:
        print(f"\n{baseline.name} Baseline:")
        print("-" * 40)

        recommendations = baseline.recommend(test_query, n=5)

        for i, song in enumerate(recommendations, 1):
            print(f"  {i}. {song.get('name', 'Unknown')} by {song.get('artist', 'Unknown')}")
            print(f"     Genre: {song.get('genre', 'N/A')}, Popularity: {song.get('popularity', 'N/A')}")

    print(f"\n{'='*60}")
    print("Baseline testing complete!")
