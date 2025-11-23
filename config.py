"""
Configuration file for Multi-Agent Music Recommendation System
"""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# API Keys (Set these in environment variables or .env file)
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY", "your_genius_api_key")  # For data collection only

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your_anthropic_api_key")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "your_cohere_api_key")

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # For cloud deployments
QDRANT_COLLECTION_NAME = "music_embeddings"
QDRANT_USE_CLOUD = os.getenv("QDRANT_USE_CLOUD", "false").lower() == "true"

# Embedding Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536

# Data Collection Configuration
TARGET_SONGS_PER_GENRE = 1000
GENRES = ["pop", "rock", "hip-hop", "electronic", "r&b"]
TOTAL_SONGS_TARGET = 5000

# Spotify search queries per genre for diverse sampling
GENRE_SEARCH_QUERIES = {
    "pop": ["pop hits", "pop 2020s", "pop classics", "indie pop", "pop rock"],
    "rock": ["rock classics", "alternative rock", "hard rock", "indie rock", "punk rock"],
    "hip-hop": ["hip hop", "rap", "trap", "conscious hip hop", "old school hip hop"],
    "electronic": ["electronic", "edm", "house", "techno", "ambient"],
    "r&b": ["r&b", "soul", "neo soul", "contemporary r&b", "rnb"]
}

# Recommendation Configuration
RETRIEVAL_CANDIDATE_COUNT = 50  # Number of songs to retrieve from Qdrant
CURATOR_PRERANK_COUNT = 30      # Number of songs to send to reranker
FINAL_RECOMMENDATION_COUNT = 10  # Final number of recommendations

# Feature Weights for Initial Scoring
FEATURE_WEIGHTS = {
    "semantic_similarity": 0.4,   # Lyrics + audio features embedding similarity
    "audio_features": 0.3,        # Direct audio feature matching
    "user_preference": 0.2,       # User history alignment
    "time_of_day": 0.1           # Time-based adjustment
}

# Time of Day Configuration
TIME_OF_DAY_FEATURES = {
    "morning": {
        "hour_range": (5, 12),
        "ideal_features": {"energy": 0.7, "valence": 0.8},
        "weight": 1.2
    },
    "afternoon": {
        "hour_range": (12, 17),
        "ideal_features": {"energy": 0.6, "valence": 0.6},
        "weight": 1.0
    },
    "evening": {
        "hour_range": (17, 22),
        "ideal_features": {"energy": 0.4, "valence": 0.5},
        "weight": 1.1
    },
    "night": {
        "hour_range": (22, 5),
        "ideal_features": {"energy": 0.3, "valence": 0.4},
        "weight": 1.3
    }
}

# Audio Features Configuration
AUDIO_FEATURES = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "speechiness",
    "loudness"
]

# Cohere Reranker Configuration
COHERE_RERANK_MODEL = "rerank-english-v3.0"
COHERE_RERANK_TOP_N = 10

# Memory Configuration
SHORT_TERM_MEMORY_WINDOW = 20  # Last N interactions
LONG_TERM_MEMORY_UPDATE_THRESHOLD = 5  # Update profile after N interactions

# Agent Configuration
AGENT_LLM_MODEL = "gpt-4"  # or "claude-3-5-sonnet-20241022"
AGENT_TEMPERATURE = 0.7

# Agent Prompts
RETRIEVER_AGENT_PROMPT = """
You are a music retrieval specialist. Your task is to understand user queries
and retrieve the most semantically relevant songs from the vector database.
Consider both lyrical content and audio features when matching user requests.
Always retrieve {candidate_count} candidates for further processing.
"""

ANALYZER_AGENT_PROMPT = """
You are a user behavior analyst. Analyze the user's listening history and
identify patterns in their music preferences. Consider:
- Genre preferences and weights
- Audio feature preferences (energy, valence, danceability, etc.)
- Artist preferences
- Time-of-day listening patterns
Generate a comprehensive user profile summary.
"""

CURATOR_AGENT_PROMPT = """
You are a music curator. You receive candidate songs and user preferences.
Your job is to:
1. Apply collaborative filtering logic
2. Integrate time-of-day preferences
3. Score candidates based on multiple factors
4. Use reranking to optimize the final selection
5. Return the top {final_count} recommendations
"""

CRITIC_AGENT_PROMPT = """
You are a recommendation critic. Evaluate the quality of recommendations by:
1. Analyzing diversity (genre, artist, audio features)
2. Checking alignment with user preferences
3. Identifying potential issues (too similar, poor variety)
4. Generating clear explanations for each recommendation
Provide constructive feedback for system improvement.
"""

# Evaluation Configuration
EVALUATION_METRICS = [
    "precision_at_k",
    "diversity_score",
    "coverage",
    "user_satisfaction"
]

PRECISION_K_VALUES = [5, 10]

# Flask Configuration
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Streamlit Configuration
STREAMLIT_PORT = 8501

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Cache Configuration
ENABLE_CACHING = True
CACHE_EXPIRY_HOURS = 24

# Rate Limiting (for API calls)
SPOTIFY_RATE_LIMIT_DELAY = 0.1  # seconds
GENIUS_RATE_LIMIT_DELAY = 0.5   # seconds
OPENAI_RATE_LIMIT_DELAY = 0.05  # seconds
