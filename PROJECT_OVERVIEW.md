# Multi-Agent Music Recommendation System
## Academic Project Overview

**Course**: Text Analytics - Graduate Level
**Institution**: Georgia State University
**Project Type**: Solo Final Project

---

## Executive Summary

This project implements a state-of-the-art music recommendation system using multi-agent RAG (Retrieval-Augmented Generation) architecture. The system demonstrates advanced concepts in natural language processing, vector databases, agent coordination, and recommendation systems.

### Key Achievements

✅ **Multi-Agent RAG System**: Four specialized agents with distinct roles
✅ **5000+ Song Database**: Real data from Spotify and Genius APIs
✅ **Vector Search**: Semantic retrieval using Qdrant and OpenAI embeddings
✅ **Advanced Reranking**: Cohere API for optimal recommendation ordering
✅ **Dual Memory Systems**: Short-term (session) and long-term (user profile)
✅ **Deterministic Tools**: Time-of-day matching for contextual recommendations
✅ **Comprehensive Evaluation**: Multiple metrics with A/B testing framework
✅ **Production-Ready**: Full web interface and REST API

---

## Technical Implementation

### 1. Multi-Agent Architecture

#### Agent 1: RetrieverAgent
**Purpose**: Semantic search and candidate generation
**Input**: Natural language query
**Output**: 50 candidate songs
**Technology**:
- Qdrant vector database
- OpenAI text-embedding-3-small
- LangChain agent framework

**Key Features**:
- Embeds lyrics + audio feature descriptions
- Semantic similarity search
- Genre filtering support
- Query enhancement using LLM

#### Agent 2: AnalyzerAgent
**Purpose**: User behavior analysis and profiling
**Input**: User ID and interaction history
**Output**: User preference profile and summary
**Technology**:
- SQLite database queries
- Statistical analysis (NumPy)
- LangChain LLM for natural language summaries

**Key Features**:
- Genre preference calculation
- Audio feature pattern detection
- Artist preference tracking
- Time-of-day pattern analysis

#### Agent 3: CuratorAgent
**Purpose**: Multi-stage recommendation curation
**Input**: Candidates + User profile
**Output**: Top 10 final recommendations
**Technology**:
- Collaborative filtering
- Cohere reranking API
- Time-of-day matching tool
- Multi-factor scoring

**Pipeline Stages**:
1. **Collaborative Filtering**: Score based on user profile
2. **Time Matching**: Adjust for current time period
3. **Initial Ranking**: Top 30 candidates
4. **Cohere Reranking**: Semantic reordering
5. **Final Selection**: Best 10 songs

#### Agent 4: CriticAgent
**Purpose**: Quality assurance and explanation
**Input**: Final recommendations
**Output**: Evaluation metrics and explanations
**Technology**:
- Diversity calculations
- Quality scoring
- Issue detection
- Natural language generation

**Evaluation Aspects**:
- Genre and artist diversity
- Audio feature variance
- Alignment with user preferences
- Potential issues (repetition, imbalance)

### 2. RAG Pipeline Design

```
User Query
    ↓
[Semantic Search in Qdrant] ← Embedding Model
    ↓
50 Candidates
    ↓
[User Profile Analysis] ← SQLite History
    ↓
User Preferences
    ↓
[Collaborative Filtering] ← Long-term Memory
    ↓
[Time-of-Day Matching] ← Deterministic Tool
    ↓
Top 30 Scored
    ↓
[Cohere Reranking] ← Query + User Context
    ↓
Top 10 Final
    ↓
[Critique & Explain] ← Evaluation Agent
    ↓
Recommendations + Explanations
```

### 3. Memory Systems

#### Short-Term Memory (Session-based)
**Storage**: In-memory + SQLite backup
**Scope**: Current session
**Contents**:
- Recent queries (last 10)
- Current session interactions (last 20)
- Temporary preferences
- Conversation context

**Implementation**: [src/memory/short_term.py](src/memory/short_term.py)

#### Long-Term Memory (Persistent Profile)
**Storage**: SQLite database
**Scope**: Entire user history
**Contents**:
- Genre preference weights
- Audio feature preferences (mean, std, min, max)
- Liked/disliked artists
- Time-of-day patterns
- Total interaction count

**Update Strategy**: Incremental updates after N interactions
**Implementation**: [src/memory/long_term.py](src/memory/long_term.py)

### 4. Reranking Implementation

The system uses Cohere's rerank-english-v3.0 model to optimize the final recommendation order:

**Input Preparation**:
```python
documents = [
    f"Song: {song['name']} by {song['artist']}. "
    f"Genre: {song['genre']}. Mood: {features}. "
    f"Lyrics: {lyrics_preview}"
]

query = f"{user_query}. User preferences: {user_profile}"
```

**Reranking Process**:
1. Top 30 candidates from initial scoring
2. Enhanced query with user context
3. Cohere API call for semantic reranking
4. Return top 10 with relevance scores

**Benefits**:
- Considers semantic nuances beyond vector similarity
- Integrates user context into ranking
- Optimizes for query-document relevance

### 5. Deterministic Tool: Time-of-Day Matcher

**Purpose**: Context-aware recommendations based on time
**Type**: Deterministic (rule-based)
**Implementation**: [src/tools/time_of_day_matcher.py](src/tools/time_of_day_matcher.py)

**Time Periods**:

| Period | Hours | Ideal Features | Weight |
|--------|-------|----------------|--------|
| Morning | 5-12 | High energy (0.7), Positive valence (0.8) | 1.2 |
| Afternoon | 12-17 | Moderate energy (0.6), Neutral valence (0.6) | 1.0 |
| Evening | 17-22 | Lower energy (0.4), Calm valence (0.5) | 1.1 |
| Night | 22-5 | Low energy (0.3), Mellow valence (0.4) | 1.3 |

**Scoring Function**:
```python
time_match_score = 1 - |song_features - ideal_features| / 2
adjusted_score = (base_score * (2 - weight) + time_match * weight) / 2
```

---

## Data Collection

### Spotify Integration
**API**: Spotify Web API
**Method**: Search queries with genre filters
**Per Genre**: 1000 songs
**Total**: 5000 songs

**Audio Features Collected**:
- Danceability (0-1)
- Energy (0-1)
- Valence (mood, 0-1)
- Tempo (BPM)
- Acousticness (0-1)
- Instrumentalness (0-1)
- Speechiness (0-1)
- Loudness (dB)

**Implementation**: [src/data_collection/spotify_collector.py](src/data_collection/spotify_collector.py)

### Lyrics Integration
**API**: Genius API (LyricsGenius library)
**Coverage**: ~70-80% of songs
**Processing**:
- Remove [Verse], [Chorus] tags
- Clean annotations and metadata
- Normalize whitespace

**Implementation**: [src/data_collection/lyrics_collector.py](src/data_collection/lyrics_collector.py)

### Embedding Generation
**Model**: OpenAI text-embedding-3-small
**Dimension**: 1536
**Input**: Combined text description:
```
Song: {name} by {artist}
Genre: {genre}
Characteristics: {audio_feature_description}
Lyrics: {lyrics_preview}
```

**Storage**: Qdrant vector database with metadata payload

---

## Evaluation Framework

### 1. Precision@K
**Formula**: `hits@k / k`
**Implementation**: Compares recommendations with user's liked songs (rating ≥ 4)
**K values**: 5, 10

### 2. Diversity Score
**Components**:
- Genre diversity: `unique_genres / total_songs`
- Artist diversity: `unique_artists / total_songs`
- Feature diversity: `std(energy, valence) / 0.2` (normalized)

**Final Score**: Average of three components

### 3. Coverage
**Formula**: `unique_recommended_songs / catalog_size`
**Purpose**: Measures catalog exploration over time

### 4. User Satisfaction
**Formula**: `mean(normalized_ratings)`
**Scale**: 1-5 stars → 0-1 normalized

### 5. A/B Testing
**Comparisons**:
- With vs. without Cohere reranker
- With vs. without time-of-day matching
- Multi-agent vs. single-agent baseline

**Metrics**: All above metrics for both strategies

**Implementation**: [src/evaluation/metrics.py](src/evaluation/metrics.py)

---

## Database Schema

### SQLite Tables

**users**
```sql
id, username, created_at, profile_json
```

**songs**
```sql
id, spotify_id, name, artist, album, genre,
features_json, lyrics_text, created_at
```

**interactions**
```sql
id, user_id, song_id, rating, timestamp, action_type
```

**user_memory**
```sql
id, user_id, short_term_json, long_term_json, updated_at
```

**recommendations**
```sql
id, session_id, user_id, recommended_songs,
timestamp, agent_reasoning
```

### Qdrant Collection

**Collection**: `music_embeddings`
**Vectors**: 1536-dimensional embeddings
**Distance**: Cosine similarity
**Payload**: Song metadata, features, lyrics preview

---

## Web Interface Features

### Streamlit App

**Pages**:
1. **Search & Recommendations**
   - Natural language query input
   - Toggle time matching and reranking
   - Genre filter
   - Rating and feedback buttons
   - Song details with audio features

2. **User Profile**
   - Genre preference visualization
   - Audio feature preferences
   - Favorite artists
   - Recent activity

3. **Evaluation**
   - Diversity and satisfaction metrics
   - Precision@K charts
   - Recommendation statistics

4. **Agent Trace**
   - Pipeline stage visualization
   - Agent reasoning explanations
   - Time period and reranking status

5. **About**
   - System architecture overview
   - Technology stack
   - Feature descriptions

### Flask REST API

**Endpoints**:
- `POST /api/recommendations` - Get recommendations
- `POST /api/feedback` - Record user feedback
- `GET /api/users/{id}/profile` - Get user profile
- `POST /api/users` - Create user
- `GET /api/songs/{id}` - Get song details
- `POST /api/evaluation/ab-test` - Run A/B test

---

## Success Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 5000+ songs in RAG system | ✅ | SQLite + Qdrant populated |
| 4 distinct agents | ✅ | Retriever, Analyzer, Curator, Critic |
| Reranker integrated | ✅ | Cohere in CuratorAgent pipeline |
| Dual memory systems | ✅ | Short-term (session) + Long-term (profile) |
| Deterministic tool | ✅ | Time-of-day matcher |
| Evaluation metrics | ✅ | Precision@K, Diversity, Coverage, Satisfaction |
| Working demo | ✅ | Streamlit app with full functionality |
| Clear explanations | ✅ | CriticAgent + UI explanations |
| Reranking effect visible | ✅ | Agent trace shows before/after |
| Spotify playback | ⚠️ | Demo shows song info (full playback requires OAuth) |

---

## Learning Outcomes Demonstrated

1. **Multi-Agent Systems**
   - Agent specialization and coordination
   - Information flow between agents
   - Distributed decision-making

2. **RAG Architecture**
   - Vector database integration
   - Semantic search implementation
   - Context-aware generation

3. **Recommendation Systems**
   - Collaborative filtering
   - Content-based filtering
   - Hybrid approaches
   - Evaluation methodologies

4. **NLP Techniques**
   - Text embedding
   - Semantic similarity
   - Query understanding
   - Natural language explanation generation

5. **Production Engineering**
   - API integration
   - Error handling
   - Caching strategies
   - Database design
   - Web interface development

---

## Future Enhancements

1. **Spotify OAuth Integration**: Full playback functionality
2. **Real-time Collaborative Filtering**: User-user similarity
3. **Playlist Generation**: Multi-song sequence optimization
4. **Advanced Time Context**: Weather, activity detection
5. **Explainable AI**: SHAP values for feature importance
6. **Model Fine-tuning**: Custom embedding models
7. **Production Deployment**: Docker, Kubernetes, monitoring

---

## Conclusion

This project successfully demonstrates a production-ready multi-agent RAG system for music recommendation. The implementation showcases:

- **Advanced Architecture**: Multi-agent coordination with specialized roles
- **Real-World Data**: Integration with major music APIs
- **Modern Techniques**: Vector search, reranking, embeddings
- **Comprehensive Evaluation**: Multiple metrics and A/B testing
- **User-Centric Design**: Memory systems and personalization
- **Academic Rigor**: Well-documented, testable, reproducible

The system meets all project requirements and provides a solid foundation for further research and development in recommendation systems and multi-agent architectures.

---

**Project Repository**: [Link to GitHub repo]
**Documentation**: README.md, QUICKSTART.md
**Demo**: Streamlit app + Flask API
**Code Quality**: Modular, documented, testable

---

*Built for GSU Text Analytics Final Project*
