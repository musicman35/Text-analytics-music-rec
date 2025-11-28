"""
Audio Feature Utilities
Centralized functions for handling audio feature extraction and description
"""

from typing import Dict, List, Optional
import config


# Standard audio feature names used throughout the system
AUDIO_FEATURE_NAMES = [
    'danceability', 'energy', 'valence', 'tempo', 'loudness',
    'speechiness', 'acousticness', 'instrumentalness', 'liveness',
    'key', 'mode', 'time_signature'
]


def extract_features_from_song(song: Dict) -> Dict:
    """
    Extract audio features from a song dictionary.

    Handles both nested 'features' dict and flat structure.

    Args:
        song: Song dictionary (may have 'features' dict or flat fields)

    Returns:
        Dictionary with audio feature values
    """
    # Try nested features dict first
    features = song.get('features', {})

    if features:
        return {
            'danceability': features.get('danceability', 0.5),
            'energy': features.get('energy', 0.5),
            'valence': features.get('valence', 0.5),
            'tempo': features.get('tempo', 120.0),
            'loudness': features.get('loudness', -10.0),
            'speechiness': features.get('speechiness', 0.05),
            'acousticness': features.get('acousticness', 0.5),
            'instrumentalness': features.get('instrumentalness', 0.0),
            'liveness': features.get('liveness', 0.1),
            'key': features.get('key', 0),
            'mode': features.get('mode', 1),
            'time_signature': features.get('time_signature', 4),
        }

    # Fall back to flat structure
    return {
        'danceability': song.get('danceability', 0.5),
        'energy': song.get('energy', 0.5),
        'valence': song.get('valence', 0.5),
        'tempo': song.get('tempo', 120.0),
        'loudness': song.get('loudness', -10.0),
        'speechiness': song.get('speechiness', 0.05),
        'acousticness': song.get('acousticness', 0.5),
        'instrumentalness': song.get('instrumentalness', 0.0),
        'liveness': song.get('liveness', 0.1),
        'key': song.get('key', 0),
        'mode': song.get('mode', 1),
        'time_signature': song.get('time_signature', 4),
    }


def describe_audio_features(features: Dict) -> List[str]:
    """
    Generate human-readable descriptions of audio features.

    Args:
        features: Dictionary of audio feature values

    Returns:
        List of descriptive strings (e.g., ["high energy", "danceable"])
    """
    descriptions = []

    # Energy level
    energy = features.get('energy', 0.5)
    if energy > 0.7:
        descriptions.append("high energy")
    elif energy < 0.3:
        descriptions.append("low energy")
    else:
        descriptions.append("moderate energy")

    # Mood (valence)
    valence = features.get('valence', 0.5)
    if valence > 0.7:
        descriptions.append("positive/happy")
    elif valence < 0.3:
        descriptions.append("sad/melancholic")
    else:
        descriptions.append("neutral mood")

    # Danceability
    if features.get('danceability', 0) > 0.7:
        descriptions.append("very danceable")

    # Acousticness
    if features.get('acousticness', 0) > 0.7:
        descriptions.append("acoustic")

    # Instrumentalness
    if features.get('instrumentalness', 0) > 0.5:
        descriptions.append("mostly instrumental")

    return descriptions


def get_mood_category(features: Dict) -> str:
    """
    Categorize the mood based on energy and valence.

    Args:
        features: Dictionary of audio feature values

    Returns:
        Mood category string
    """
    energy = features.get('energy', 0.5)
    valence = features.get('valence', 0.5)

    if energy > 0.6 and valence > 0.6:
        return "energetic_happy"
    elif energy > 0.6 and valence <= 0.4:
        return "energetic_intense"
    elif energy <= 0.4 and valence > 0.6:
        return "calm_happy"
    elif energy <= 0.4 and valence <= 0.4:
        return "calm_sad"
    else:
        return "moderate"


def create_song_payload(song: Dict) -> Dict:
    """
    Create a standardized payload for storing a song.

    Args:
        song: Raw song dictionary with metadata and features

    Returns:
        Flattened payload dictionary for storage
    """
    features = song.get('features', {})

    return {
        # Identifiers
        'song_id': song.get('song_id', song.get('spotify_id', '')),
        'spotify_id': song.get('spotify_id', ''),

        # Basic metadata
        'name': song.get('name', ''),
        'artist': song.get('artist', ''),
        'album': song.get('album', ''),
        'genre': song.get('genre', ''),
        'popularity': song.get('popularity', 0),
        'duration_ms': song.get('duration_ms', 0),
        'explicit': song.get('explicit', False),

        # Audio features (flattened)
        'danceability': features.get('danceability', song.get('danceability', 0)),
        'energy': features.get('energy', song.get('energy', 0)),
        'valence': features.get('valence', song.get('valence', 0)),
        'tempo': features.get('tempo', song.get('tempo', 0)),
        'loudness': features.get('loudness', song.get('loudness', 0)),
        'speechiness': features.get('speechiness', song.get('speechiness', 0)),
        'acousticness': features.get('acousticness', song.get('acousticness', 0)),
        'instrumentalness': features.get('instrumentalness', song.get('instrumentalness', 0)),
        'liveness': features.get('liveness', song.get('liveness', 0)),
        'key': features.get('key', song.get('key', 0)),
        'mode': features.get('mode', song.get('mode', 1)),
        'time_signature': features.get('time_signature', song.get('time_signature', 4)),

        # Lyrics
        'lyrics_preview': song.get('lyrics_preview', ''),
        'has_lyrics': bool(song.get('lyrics_preview')),
    }


def create_song_description(song: Dict, include_lyrics: bool = True, max_lyrics_chars: int = 300) -> str:
    """
    Create a rich text description of a song for embedding.

    Args:
        song: Song dictionary with metadata and features
        include_lyrics: Whether to include lyrics preview
        max_lyrics_chars: Maximum characters of lyrics to include

    Returns:
        Text description suitable for embedding
    """
    features = extract_features_from_song(song)

    parts = [
        f"Song: {song.get('name', '')} by {song.get('artist', '')}",
        f"Genre: {song.get('genre', 'unknown')}",
    ]

    # Add feature descriptions
    feature_desc = describe_audio_features(features)
    # Filter out the always-present ones for cleaner description
    notable_features = [f for f in feature_desc if f not in ['moderate energy', 'neutral mood']]
    if notable_features:
        parts.append(f"Characteristics: {', '.join(notable_features)}")

    # Add lyrics if available
    if include_lyrics:
        lyrics_preview = song.get('lyrics_preview', '')
        if lyrics_preview:
            truncated = lyrics_preview[:max_lyrics_chars] if len(lyrics_preview) > max_lyrics_chars else lyrics_preview
            parts.append(f"Lyrics excerpt: {truncated}")

    return '. '.join(parts)
