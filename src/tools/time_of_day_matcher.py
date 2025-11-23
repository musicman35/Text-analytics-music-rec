"""
Time of Day Matcher Tool
Deterministic tool that adjusts music recommendations based on time of day
"""

from datetime import datetime
from typing import Dict, Tuple
import config


class TimeOfDayMatcher:
    """Matches songs to appropriate time of day based on audio features"""

    def __init__(self):
        self.time_config = config.TIME_OF_DAY_FEATURES

    def get_current_hour(self) -> int:
        """Get current hour (0-23)"""
        return datetime.now().hour

    def get_time_period(self, hour: int = None) -> str:
        """Get time period (morning, afternoon, evening, night) for given hour"""
        if hour is None:
            hour = self.get_current_hour()

        for period, settings in self.time_config.items():
            start, end = settings['hour_range']

            # Handle night period (crosses midnight)
            if start > end:
                if hour >= start or hour < end:
                    return period
            else:
                if start <= hour < end:
                    return period

        return "afternoon"  # Default

    def get_ideal_features(self, hour: int = None) -> Dict:
        """Get ideal audio features for given hour"""
        period = self.get_time_period(hour)
        return self.time_config[period]['ideal_features']

    def get_time_weight(self, hour: int = None) -> float:
        """Get importance weight for time-based matching"""
        period = self.get_time_period(hour)
        return self.time_config[period]['weight']

    def calculate_time_match_score(self, song_features: Dict, hour: int = None) -> float:
        """
        Calculate how well a song matches the current time of day
        Returns score between 0 and 1
        """
        ideal_features = self.get_ideal_features(hour)

        # Calculate distance for each relevant feature
        energy_diff = abs(song_features.get('energy', 0.5) - ideal_features['energy'])
        valence_diff = abs(song_features.get('valence', 0.5) - ideal_features['valence'])

        # Average difference (lower is better)
        avg_diff = (energy_diff + valence_diff) / 2

        # Convert to similarity score (higher is better)
        similarity = 1 - avg_diff

        return max(0, min(1, similarity))

    def adjust_score_for_time(self, base_score: float, song_features: Dict,
                             hour: int = None) -> float:
        """
        Adjust a recommendation score based on time of day match

        Args:
            base_score: Original recommendation score (0-1)
            song_features: Song's audio features
            hour: Hour of day (0-23), defaults to current hour

        Returns:
            Adjusted score incorporating time-of-day match
        """
        time_match_score = self.calculate_time_match_score(song_features, hour)
        time_weight = self.get_time_weight(hour)

        # Weighted combination
        # Higher time_weight means time matching is more important
        adjusted_score = (base_score * (2 - time_weight) + time_match_score * time_weight) / 2

        return adjusted_score

    def boost_songs_by_time(self, songs: list, hour: int = None) -> list:
        """
        Boost/adjust scores for songs based on time of day

        Args:
            songs: List of song dicts with 'features' and 'score' keys
            hour: Hour of day, defaults to current hour

        Returns:
            List of songs with adjusted scores, sorted by new score
        """
        period = self.get_time_period(hour)
        print(f"Time period: {period} (hour: {hour or self.get_current_hour()})")

        adjusted_songs = []
        for song in songs:
            song_copy = song.copy()

            # Get base score (default to 0.5 if not present)
            base_score = song.get('score', 0.5)

            # Adjust score
            new_score = self.adjust_score_for_time(
                base_score,
                song['features'],
                hour
            )

            song_copy['original_score'] = base_score
            song_copy['time_adjusted_score'] = new_score
            song_copy['score'] = new_score
            song_copy['time_period'] = period

            adjusted_songs.append(song_copy)

        # Sort by adjusted score
        adjusted_songs.sort(key=lambda x: x['score'], reverse=True)

        return adjusted_songs

    def get_time_context(self, hour: int = None) -> Dict:
        """Get complete time context information"""
        if hour is None:
            hour = self.get_current_hour()

        period = self.get_time_period(hour)
        ideal_features = self.get_ideal_features(hour)
        weight = self.get_time_weight(hour)

        return {
            'hour': hour,
            'period': period,
            'ideal_energy': ideal_features['energy'],
            'ideal_valence': ideal_features['valence'],
            'weight': weight,
            'description': self.get_period_description(period)
        }

    def get_period_description(self, period: str) -> str:
        """Get human-readable description of time period preferences"""
        descriptions = {
            'morning': "Morning time: Prefer uplifting, energetic songs to start the day",
            'afternoon': "Afternoon: Balanced energy, good for focus and productivity",
            'evening': "Evening: Relaxed vibes, winding down from the day",
            'night': "Night time: Calm, low-energy music for relaxation or sleep"
        }
        return descriptions.get(period, "")

    def explain_time_adjustment(self, song: Dict, hour: int = None) -> str:
        """Generate explanation for why a song was boosted/penalized by time"""
        period = self.get_time_period(hour)
        ideal = self.get_ideal_features(hour)
        features = song['features']

        energy_match = "high" if abs(features['energy'] - ideal['energy']) < 0.2 else "low"
        valence_match = "good" if abs(features['valence'] - ideal['valence']) < 0.2 else "poor"

        explanation = f"For {period} listening, this song has {energy_match} energy match "
        explanation += f"and {valence_match} mood match with ideal preferences."

        return explanation


# Convenience function
def get_time_matcher() -> TimeOfDayMatcher:
    """Get TimeOfDayMatcher instance"""
    return TimeOfDayMatcher()


# Testing
if __name__ == "__main__":
    matcher = TimeOfDayMatcher()

    # Test at different times
    test_hours = [8, 14, 19, 2]  # Morning, afternoon, evening, night

    print("Time of Day Matcher Test\n" + "="*60)

    for hour in test_hours:
        context = matcher.get_time_context(hour)
        print(f"\nHour {hour}:00 - {context['period'].upper()}")
        print(f"  {context['description']}")
        print(f"  Ideal: Energy={context['ideal_energy']}, Valence={context['ideal_valence']}")
        print(f"  Weight: {context['weight']}")

    # Test with sample songs
    print("\n" + "="*60)
    print("Sample Song Matching:\n")

    sample_songs = [
        {
            'name': 'High Energy Dance',
            'features': {'energy': 0.9, 'valence': 0.8},
            'score': 0.8
        },
        {
            'name': 'Calm Acoustic',
            'features': {'energy': 0.2, 'valence': 0.4},
            'score': 0.8
        }
    ]

    for hour in [8, 22]:  # Morning and night
        print(f"\nTesting at hour {hour} ({matcher.get_time_period(hour)}):")
        adjusted = matcher.boost_songs_by_time(sample_songs.copy(), hour)

        for song in adjusted:
            print(f"  {song['name']}: {song['original_score']:.3f} → {song['score']:.3f}")
