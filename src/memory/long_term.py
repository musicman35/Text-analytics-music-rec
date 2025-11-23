"""
Long-term Memory System
Manages persistent user profile and preferences
"""

from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from collections import Counter, defaultdict
import config
from src.database.qdrant_storage import QdrantStorage


class LongTermMemory:
    """Manages long-term user profile and preferences"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = QdrantStorage()
        self.update_threshold = config.LONG_TERM_MEMORY_UPDATE_THRESHOLD

        # Profile data
        self.profile = {
            'genre_preferences': {},
            'audio_feature_preferences': {},
            'liked_artists': [],
            'disliked_artists': [],
            'time_of_day_patterns': {},
            'total_interactions': 0,
            'last_updated': None
        }

        self.load_from_database()

    def load_from_database(self):
        """Load long-term memory from database"""
        memory = self.db.get_user_memory(self.user_id)

        if memory and memory.get('long_term'):
            self.profile = memory['long_term']

    def save_to_database(self):
        """Save long-term memory to database"""
        self.profile['last_updated'] = datetime.now().isoformat()

        self.db.update_user_memory(
            self.user_id,
            long_term=self.profile
        )

    def update_from_interactions(self, force: bool = False):
        """Update profile based on user interactions"""
        # Get all user interactions
        all_interactions = self.db.get_user_interactions(self.user_id)

        if not all_interactions:
            return

        # Only update if we have enough new interactions (unless forced)
        if not force and self.profile['total_interactions'] > 0:
            new_interactions = len(all_interactions) - self.profile['total_interactions']
            if new_interactions < self.update_threshold:
                return

        print(f"Updating long-term memory for user {self.user_id}...")

        # Extract liked songs (rating >= 4 or positive actions)
        liked_songs = [i for i in all_interactions
                      if (i.get('rating') and i['rating'] >= 4) or
                         i['action_type'] in ['like', 'play', 'save']]

        # Extract disliked songs
        disliked_songs = [i for i in all_interactions
                         if (i.get('rating') and i['rating'] <= 2) or
                            i['action_type'] == 'dislike']

        # Update genre preferences
        self._update_genre_preferences(liked_songs, disliked_songs)

        # Update audio feature preferences
        self._update_audio_feature_preferences(liked_songs)

        # Update artist preferences
        self._update_artist_preferences(liked_songs, disliked_songs)

        # Update time patterns
        self._update_time_patterns(liked_songs)

        # Update metadata
        self.profile['total_interactions'] = len(all_interactions)

        # Save to database
        self.save_to_database()

        print(f"Profile updated. Total interactions: {len(all_interactions)}")

    def _update_genre_preferences(self, liked_songs: List[Dict], disliked_songs: List[Dict]):
        """Update genre preference weights"""
        genre_scores = defaultdict(float)

        # Positive weight for liked songs
        for song in liked_songs:
            song_data = self.db.get_song(song_id=song['song_id'])
            if song_data and song_data.get('genre'):
                genre = song_data['genre']
                genre_scores[genre] += 1.0

        # Negative weight for disliked songs
        for song in disliked_songs:
            song_data = self.db.get_song(song_id=song['song_id'])
            if song_data and song_data.get('genre'):
                genre = song_data['genre']
                genre_scores[genre] -= 0.5

        # Normalize scores
        if genre_scores:
            total = sum(max(0, score) for score in genre_scores.values())
            if total > 0:
                self.profile['genre_preferences'] = {
                    genre: max(0, score) / total
                    for genre, score in genre_scores.items()
                }

    def _update_audio_feature_preferences(self, liked_songs: List[Dict]):
        """Calculate average preferred audio features"""
        if not liked_songs:
            return

        feature_values = defaultdict(list)

        for song in liked_songs:
            features = song.get('features', {})
            for feature_name in config.AUDIO_FEATURES:
                if feature_name in features:
                    feature_values[feature_name].append(features[feature_name])

        # Calculate averages and standard deviations
        audio_prefs = {}
        for feature_name, values in feature_values.items():
            if values:
                audio_prefs[feature_name] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values))
                }

        self.profile['audio_feature_preferences'] = audio_prefs

    def _update_artist_preferences(self, liked_songs: List[Dict], disliked_songs: List[Dict]):
        """Update liked and disliked artists"""
        liked_artists = [song['artist'] for song in liked_songs]
        disliked_artists = [song['artist'] for song in disliked_songs]

        # Count occurrences
        liked_counter = Counter(liked_artists)
        disliked_counter = Counter(disliked_artists)

        # Top liked artists (at least 2 likes)
        self.profile['liked_artists'] = [
            artist for artist, count in liked_counter.most_common(50)
            if count >= 2
        ]

        # Disliked artists (at least 2 dislikes)
        self.profile['disliked_artists'] = [
            artist for artist, count in disliked_counter.most_common(20)
            if count >= 2
        ]

    def _update_time_patterns(self, liked_songs: List[Dict]):
        """Analyze time-of-day listening patterns"""
        from src.tools.time_of_day_matcher import TimeOfDayMatcher

        matcher = TimeOfDayMatcher()
        time_patterns = defaultdict(list)

        for song in liked_songs:
            timestamp_str = song.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    hour = timestamp.hour
                    period = matcher.get_time_period(hour)

                    features = song.get('features', {})
                    if features:
                        time_patterns[period].append(features)
                except:
                    pass

        # Calculate average features per time period
        patterns = {}
        for period, feature_list in time_patterns.items():
            if feature_list:
                avg_features = {}
                for feature_name in ['energy', 'valence', 'danceability']:
                    values = [f.get(feature_name, 0.5) for f in feature_list]
                    avg_features[feature_name] = float(np.mean(values))

                patterns[period] = {
                    'avg_features': avg_features,
                    'count': len(feature_list)
                }

        self.profile['time_of_day_patterns'] = patterns

    def get_genre_preference(self, genre: str) -> float:
        """Get preference weight for a specific genre"""
        return self.profile['genre_preferences'].get(genre, 0.5)

    def get_preferred_feature_range(self, feature_name: str) -> tuple:
        """Get preferred range for an audio feature"""
        prefs = self.profile['audio_feature_preferences'].get(feature_name)

        if prefs:
            # Return mean +/- std as preferred range
            mean = prefs['mean']
            std = prefs['std']
            return (max(0, mean - std), min(1, mean + std))

        return (0, 1)  # Default: accept all

    def is_artist_liked(self, artist: str) -> bool:
        """Check if artist is in liked list"""
        return artist in self.profile['liked_artists']

    def is_artist_disliked(self, artist: str) -> bool:
        """Check if artist is in disliked list"""
        return artist in self.profile['disliked_artists']

    def get_profile_summary(self) -> str:
        """Generate human-readable profile summary"""
        summary_parts = []

        # Genre preferences
        if self.profile['genre_preferences']:
            top_genres = sorted(
                self.profile['genre_preferences'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            genres_str = ", ".join([f"{g} ({w:.2f})" for g, w in top_genres])
            summary_parts.append(f"Preferred genres: {genres_str}")

        # Audio features
        audio_prefs = self.profile['audio_feature_preferences']
        if audio_prefs:
            feature_desc = []
            if 'energy' in audio_prefs:
                energy = audio_prefs['energy']['mean']
                if energy > 0.7:
                    feature_desc.append("high energy")
                elif energy < 0.3:
                    feature_desc.append("low energy")

            if 'valence' in audio_prefs:
                valence = audio_prefs['valence']['mean']
                if valence > 0.7:
                    feature_desc.append("positive mood")
                elif valence < 0.3:
                    feature_desc.append("melancholic mood")

            if 'danceability' in audio_prefs:
                dance = audio_prefs['danceability']['mean']
                if dance > 0.7:
                    feature_desc.append("danceable")

            if feature_desc:
                summary_parts.append(f"Prefers: {', '.join(feature_desc)}")

        # Artists
        if self.profile['liked_artists']:
            top_artists = self.profile['liked_artists'][:5]
            summary_parts.append(f"Favorite artists: {', '.join(top_artists)}")

        # Total interactions
        summary_parts.append(f"Based on {self.profile['total_interactions']} interactions")

        return ". ".join(summary_parts) if summary_parts else "New user with no preferences yet"

    def get_full_profile(self) -> Dict:
        """Get complete profile data"""
        return self.profile.copy()

    def calculate_song_match_score(self, song_features: Dict, song_genre: str = None,
                                   song_artist: str = None) -> float:
        """Calculate how well a song matches user profile (0-1)"""
        scores = []

        # Genre match
        if song_genre and self.profile['genre_preferences']:
            genre_score = self.get_genre_preference(song_genre)
            scores.append(genre_score)

        # Audio feature match
        if self.profile['audio_feature_preferences']:
            feature_scores = []
            for feature_name, value in song_features.items():
                if feature_name in self.profile['audio_feature_preferences']:
                    prefs = self.profile['audio_feature_preferences'][feature_name]
                    mean = prefs['mean']
                    std = prefs['std']

                    # Calculate normalized distance
                    if std > 0:
                        distance = abs(value - mean) / (2 * std)
                        feature_score = max(0, 1 - distance)
                    else:
                        feature_score = 1.0 if value == mean else 0.5

                    feature_scores.append(feature_score)

            if feature_scores:
                scores.append(np.mean(feature_scores))

        # Artist preference
        if song_artist:
            if self.is_artist_liked(song_artist):
                scores.append(1.0)
            elif self.is_artist_disliked(song_artist):
                scores.append(0.0)

        # Return average score
        return float(np.mean(scores)) if scores else 0.5


# Convenience function
def get_long_term_memory(user_id: int, auto_update: bool = True) -> LongTermMemory:
    """Get LongTermMemory instance"""
    memory = LongTermMemory(user_id)
    if auto_update:
        memory.update_from_interactions()
    return memory
