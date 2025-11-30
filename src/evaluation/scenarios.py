"""
Test Scenarios for Evaluation
Defines simulated user scenarios with queries, expected behaviors, and relevance criteria
"""

from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional
import numpy as np


@dataclass
class TestScenario:
    """Represents a test scenario for evaluation"""
    name: str
    description: str
    query: str
    expected_features: Dict[str, float]  # Target audio features
    relevance_criteria: Dict[str, any]   # Criteria for judging relevance
    weight_importance: Dict[str, float] = field(default_factory=dict)  # Feature importance weights

    def is_song_relevant(self, song: Dict) -> bool:
        """Check if a song meets the relevance criteria for this scenario"""
        score = self.calculate_relevance_score(song)
        return score >= 0.5  # Threshold for relevance

    def calculate_relevance_score(self, song: Dict) -> float:
        """
        Calculate how relevant a song is to this scenario (0-1)

        Considers:
        - Audio feature matching
        - Genre matching (if specified)
        - Lyrics themes (if specified)
        """
        scores = []
        weights = []

        # Get features from song
        features = song.get('features', {})
        if not features:
            # Try flat structure
            features = {
                'energy': song.get('energy', 0.5),
                'valence': song.get('valence', 0.5),
                'danceability': song.get('danceability', 0.5),
                'acousticness': song.get('acousticness', 0.5),
                'instrumentalness': song.get('instrumentalness', 0.5),
                'tempo': song.get('tempo', 120)
            }

        # Audio feature matching
        for feature_name, target_value in self.expected_features.items():
            if feature_name in features:
                song_value = features.get(feature_name, 0.5)

                # Handle tempo differently
                if feature_name == 'tempo':
                    tolerance = self.relevance_criteria.get('tempo_tolerance', 30)
                    diff = abs(song_value - target_value)
                    similarity = max(0, 1 - (diff / tolerance))
                else:
                    tolerance = self.relevance_criteria.get('feature_tolerance', 0.3)
                    diff = abs(song_value - target_value)
                    similarity = max(0, 1 - (diff / tolerance))

                weight = self.weight_importance.get(feature_name, 1.0)
                scores.append(similarity)
                weights.append(weight)

        # Genre matching
        expected_genres = self.relevance_criteria.get('genres', [])
        if expected_genres:
            song_genre = song.get('genre', '').lower()
            genre_match = 1.0 if any(g.lower() in song_genre for g in expected_genres) else 0.3
            scores.append(genre_match)
            weights.append(self.weight_importance.get('genre', 0.5))

        # Calculate weighted average
        if scores and weights:
            return float(np.average(scores, weights=weights))

        return 0.5


# Define the 5 test scenarios
WORKOUT_SCENARIO = TestScenario(
    name="Workout User",
    description="User looking for high-energy music to exercise to",
    query="upbeat songs for working out",
    expected_features={
        'energy': 0.85,
        'danceability': 0.75,
        'valence': 0.7,
        'tempo': 130
    },
    relevance_criteria={
        'genres': ['pop', 'electronic', 'hip-hop'],
        'feature_tolerance': 0.25,
        'tempo_tolerance': 25
    },
    weight_importance={
        'energy': 2.0,
        'danceability': 1.5,
        'valence': 1.0,
        'tempo': 1.5,
        'genre': 0.5
    }
)

SAD_MUSIC_SCENARIO = TestScenario(
    name="Sad Music Seeker",
    description="User looking for melancholic, emotional music",
    query="sad songs for a rainy day",
    expected_features={
        'energy': 0.3,
        'valence': 0.2,
        'acousticness': 0.6,
        'danceability': 0.4
    },
    relevance_criteria={
        'genres': ['pop', 'rock', 'r&b', 'r-n-b'],
        'feature_tolerance': 0.25
    },
    weight_importance={
        'valence': 2.0,
        'energy': 1.5,
        'acousticness': 1.0,
        'danceability': 0.5,
        'genre': 0.3
    }
)

STUDY_SCENARIO = TestScenario(
    name="Study Session",
    description="User looking for calm, focused music for studying",
    query="chill music for studying",
    expected_features={
        'energy': 0.35,
        'valence': 0.5,
        'instrumentalness': 0.4,
        'acousticness': 0.5,
        'speechiness': 0.1
    },
    relevance_criteria={
        'genres': ['electronic', 'pop'],
        'feature_tolerance': 0.3
    },
    weight_importance={
        'energy': 2.0,
        'instrumentalness': 1.5,
        'speechiness': 1.5,
        'acousticness': 1.0,
        'valence': 0.5,
        'genre': 0.3
    }
)

PARTY_SCENARIO = TestScenario(
    name="Party Playlist",
    description="User looking for danceable party music",
    query="party bangers",
    expected_features={
        'danceability': 0.85,
        'energy': 0.8,
        'valence': 0.75,
        'tempo': 120
    },
    relevance_criteria={
        'genres': ['pop', 'hip-hop', 'electronic'],
        'feature_tolerance': 0.2,
        'tempo_tolerance': 20
    },
    weight_importance={
        'danceability': 2.0,
        'energy': 1.5,
        'valence': 1.0,
        'tempo': 1.0,
        'genre': 0.5
    }
)

THEMATIC_SCENARIO = TestScenario(
    name="Thematic/Lyrical",
    description="User looking for songs with specific lyrical themes (tests lyrics integration)",
    query="songs about heartbreak and lost love",
    expected_features={
        'valence': 0.35,
        'energy': 0.45,
        'acousticness': 0.4
    },
    relevance_criteria={
        'genres': ['pop', 'rock', 'r&b', 'r-n-b'],
        'feature_tolerance': 0.35,
        'lyrical_themes': ['love', 'heart', 'break', 'lost', 'goodbye', 'miss', 'tears']
    },
    weight_importance={
        'valence': 1.5,
        'energy': 0.8,
        'acousticness': 0.5,
        'genre': 0.3,
        'lyrics': 2.0  # High weight for lyrics matching
    }
)


# All scenarios
TEST_SCENARIOS = [
    WORKOUT_SCENARIO,
    SAD_MUSIC_SCENARIO,
    STUDY_SCENARIO,
    PARTY_SCENARIO,
    THEMATIC_SCENARIO
]


def get_all_scenarios() -> List[TestScenario]:
    """Return all test scenarios"""
    return TEST_SCENARIOS


def get_scenario_by_name(name: str) -> Optional[TestScenario]:
    """Get a specific scenario by name"""
    for scenario in TEST_SCENARIOS:
        if scenario.name.lower() == name.lower():
            return scenario
    return None


def evaluate_recommendations_for_scenario(
    scenario: TestScenario,
    recommendations: List[Dict]
) -> Dict:
    """
    Evaluate a set of recommendations against a scenario.

    Returns:
        Dict with evaluation metrics
    """
    if not recommendations:
        return {
            'scenario': scenario.name,
            'num_recommendations': 0,
            'precision_at_5': 0.0,
            'precision_at_10': 0.0,
            'avg_relevance_score': 0.0,
            'relevant_count': 0
        }

    # Calculate relevance scores for each recommendation
    relevance_scores = []
    relevant_count = 0

    for song in recommendations:
        score = scenario.calculate_relevance_score(song)
        relevance_scores.append(score)
        if score >= 0.5:
            relevant_count += 1

    # Calculate precision at different k values
    precision_at_5 = sum(1 for s in relevance_scores[:5] if s >= 0.5) / min(5, len(relevance_scores))
    precision_at_10 = sum(1 for s in relevance_scores[:10] if s >= 0.5) / min(10, len(relevance_scores))

    return {
        'scenario': scenario.name,
        'query': scenario.query,
        'num_recommendations': len(recommendations),
        'precision_at_5': precision_at_5,
        'precision_at_10': precision_at_10,
        'avg_relevance_score': float(np.mean(relevance_scores)),
        'relevance_scores': relevance_scores,
        'relevant_count': relevant_count
    }


def check_lyrics_relevance(song: Dict, themes: List[str]) -> float:
    """
    Check if song lyrics contain relevant themes.

    Args:
        song: Song dictionary with lyrics_preview
        themes: List of theme keywords to look for

    Returns:
        Relevance score (0-1) based on theme matches
    """
    lyrics = song.get('lyrics_preview', '').lower()

    if not lyrics:
        return 0.0

    # Count theme matches
    matches = sum(1 for theme in themes if theme.lower() in lyrics)

    # Normalize by number of themes
    if themes:
        return min(1.0, matches / (len(themes) * 0.3))  # 30% match = full score

    return 0.0


# Testing
if __name__ == "__main__":
    print("Test Scenarios\n" + "="*60)

    for scenario in TEST_SCENARIOS:
        print(f"\n{scenario.name}")
        print("-" * 40)
        print(f"  Query: {scenario.query}")
        print(f"  Description: {scenario.description}")
        print(f"  Expected features:")
        for feature, value in scenario.expected_features.items():
            print(f"    - {feature}: {value}")

    print(f"\n{'='*60}")

    # Test relevance scoring
    print("\nTesting relevance scoring:")

    # Create a mock song that should match workout scenario
    mock_workout_song = {
        'name': 'High Energy Track',
        'genre': 'electronic',
        'features': {
            'energy': 0.9,
            'danceability': 0.8,
            'valence': 0.75,
            'tempo': 128
        }
    }

    score = WORKOUT_SCENARIO.calculate_relevance_score(mock_workout_song)
    print(f"  Workout song relevance to Workout scenario: {score:.3f}")

    # Same song should score lower for sad music
    sad_score = SAD_MUSIC_SCENARIO.calculate_relevance_score(mock_workout_song)
    print(f"  Workout song relevance to Sad Music scenario: {sad_score:.3f}")

    print("\nScenario testing complete!")
