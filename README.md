# 🎵 Multi-Agent Music Recommendation System

A sophisticated music recommendation system built with multi-agent RAG architecture, memory systems, and advanced evaluation capabilities. This project demonstrates state-of-the-art recommendation techniques using vector databases, reranking, and intelligent agents.

**Graduate Text Analytics Final Project - Georgia State University**

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Evaluation](#evaluation)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)

---

## ✨ Features

### Core Capabilities

- **Multi-Agent RAG System**: Four specialized agents working together
- **Semantic Search**: Vector-based song retrieval using Qdrant
- **Cohere Reranking**: Optimized recommendation ordering
- **Time-of-Day Matching**: Contextual recommendations based on time
- **Dual Memory Systems**: Short-term (session) and long-term (profile)
- **Comprehensive Evaluation**: Precision@K, Diversity, Coverage, User Satisfaction
- **A/B Testing Framework**: Compare recommendation strategies
- **Interactive Web Interface**: Streamlit-based UI with rich visualizations

### Data

- **5000+ songs** across 5 genres (Pop, Rock, Hip-Hop, Electronic, R&B)
- **Audio Features**: Danceability, energy, valence, tempo, acousticness, etc.
- **Lyrics**: Integrated from Genius API
- **Real-time Feedback**: User ratings and interactions

---

## 🏗️ Architecture

### Multi-Agent Pipeline

```
User Query → RetrieverAgent → AnalyzerAgent → CuratorAgent → CriticAgent → Recommendations
                   ↓               ↓              ↓              ↓
                Qdrant         Long-term      Reranking      Evaluation
              (50 songs)       Memory        (Top 10)        Metrics
```

### The Four Agents

1. **RetrieverAgent**
   - Performs semantic search on Qdrant vector database
   - Returns 50 candidate songs based on natural language query
   - Uses OpenAI embeddings for lyrics + audio features

2. **AnalyzerAgent**
   - Analyzes user listening history from SQLite
   - Identifies genre, artist, and audio feature preferences
   - Generates user taste profile and preference summary

3. **CuratorAgent**
   - Applies collaborative filtering based on user profile
   - Integrates time-of-day matching (morning/afternoon/evening/night)
   - Scores and ranks candidates
   - **Reranks top 30 using Cohere** for optimal ordering
   - Selects final 10 recommendations

4. **CriticAgent**
   - Evaluates recommendation quality and diversity
   - Generates explanations for each recommendation
   - Identifies potential issues (repetition, imbalance)
   - Provides feedback for system improvement

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Agents** | LangChain, OpenAI GPT-4 |
| **Vector DB** | Qdrant |
| **Reranking** | Cohere API |
| **Embeddings** | OpenAI text-embedding-3-small |
| **Database** | SQLite |
| **Web UI** | Streamlit |
| **API** | Flask |
| **Data Sources** | Spotify API, Genius API |

---

## 🚀 Installation

### Prerequisites

- Python 3.9+
- Qdrant (local or cloud)
- API Keys (see [Configuration](#configuration))

### Step 1: Clone and Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys

```bash
# Copy template
cp .env.template .env

# Edit .env with your API keys
nano .env
```

Required API keys:
- **Spotify**: https://developer.spotify.com/dashboard
- **Genius**: https://genius.com/api-clients
- **OpenAI**: https://platform.openai.com/api-keys
- **Cohere**: https://dashboard.cohere.com/api-keys

### Step 3: Install Qdrant

**Option A: Docker (Recommended)**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Option B: Qdrant Cloud**
```bash
# Update .env with your Qdrant Cloud credentials
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_API_KEY=your_api_key
QDRANT_USE_CLOUD=true
```

---

## ⚙️ Configuration

### Environment Variables

Edit [.env](./.env) file:

```bash
# Spotify API
SPOTIFY_CLIENT_ID=your_id
SPOTIFY_CLIENT_SECRET=your_secret

# Genius API
GENIUS_API_KEY=your_key

# OpenAI API
OPENAI_API_KEY=your_key

# Cohere API
COHERE_API_KEY=your_key

# Qdrant (local)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### System Configuration

Edit [config.py](./config.py) to customize:

- Target songs per genre
- Retrieval candidate count (default: 50)
- Final recommendation count (default: 10)
- Time-of-day thresholds
- Feature weights
- Agent prompts

---

## 🎯 Usage

### Quick Start (100 songs for testing)

```bash
# Collect test data (100 songs)
python collect_data.py --quick

# Start Streamlit app
streamlit run streamlit_app.py
```

### Full Data Collection (5000 songs)

```bash
# Collect all data
python collect_data.py --step all

# Or run steps individually:
python collect_data.py --step spotify   # 1. Spotify data
python collect_data.py --step lyrics    # 2. Lyrics
python collect_data.py --step qdrant    # 3. Vector DB
```

**Data Collection Options:**

```bash
# Use fresh data (no cache)
python collect_data.py --no-cache

# Limit songs per genre
python collect_data.py --limit 200

# Run specific step
python collect_data.py --step qdrant
```

### Running the Application

**Option 1: Streamlit Web Interface (Recommended)**

```bash
streamlit run streamlit_app.py
```

Features:
- User registration/login
- Natural language search
- Interactive recommendations
- User profile visualization
- Agent pipeline trace
- Evaluation metrics

**Option 2: Flask API**

```bash
python src/api/flask_app.py
```

API will be available at `http://localhost:5000`

### Using the System

1. **Register/Login**
   - Create username or login to existing account

2. **Get Recommendations**
   - Enter natural language query: "upbeat songs for working out"
   - Toggle time-of-day matching and reranking
   - Optionally filter by genre

3. **Provide Feedback**
   - Rate songs (1-5 stars)
   - Like/dislike songs
   - System learns from your preferences

4. **View Your Profile**
   - See genre preferences
   - View favorite artists
   - Check listening history

5. **Explore Agent Trace**
   - See how each agent contributed
   - View pipeline reasoning
   - Understand recommendation logic

---

## 📁 Project Structure

```
music-recommender/
├── data/
│   ├── music.db              # SQLite database
│   └── cache/                # Cached API responses
├── src/
│   ├── agents/
│   │   ├── retriever.py      # Semantic search agent
│   │   ├── analyzer.py       # User analysis agent
│   │   ├── curator.py        # Curation + reranking agent
│   │   └── critic.py         # Evaluation agent
│   ├── memory/
│   │   ├── short_term.py     # Session memory
│   │   └── long_term.py      # User profile memory
│   ├── tools/
│   │   └── time_of_day_matcher.py  # Deterministic tool
│   ├── data_collection/
│   │   ├── spotify_collector.py    # Spotify API
│   │   └── lyrics_collector.py     # Genius API
│   ├── reranker/
│   │   └── cohere_reranker.py      # Cohere integration
│   ├── evaluation/
│   │   └── metrics.py        # Evaluation metrics
│   ├── database/
│   │   ├── qdrant_manager.py # Vector DB manager
│   │   └── sqlite_manager.py # SQLite manager
│   ├── api/
│   │   └── flask_app.py      # REST API
│   └── recommendation_system.py  # Main orchestrator
├── streamlit_app.py          # Web interface
├── collect_data.py           # Data collection script
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── .env.template             # Environment template
└── README.md                 # This file
```

---

## 📊 Evaluation

### Implemented Metrics

1. **Precision@K**
   - Measures accuracy at different K values (5, 10)
   - Based on user ratings (4-5 stars = relevant)

2. **Diversity Score**
   - Genre diversity
   - Artist diversity
   - Audio feature diversity (energy, valence variance)

3. **Coverage**
   - Percentage of catalog recommended over time
   - Measures exploration vs exploitation

4. **User Satisfaction**
   - Average rating of recommended songs
   - Normalized to 0-1 scale

### A/B Testing

Compare strategies:

```python
from src.evaluation.metrics import get_ab_testing

ab = get_ab_testing()

# Test with/without reranker
result = ab.test_with_without_reranker(user_id, query, candidates)

# Test with/without time matching
result = ab.test_with_without_time_matching(user_id, query, candidates)
```

### Running Evaluations

```python
from src.evaluation.metrics import get_metrics

metrics = get_metrics()

# Evaluate recommendations
evaluation = metrics.evaluate_recommendations(
    user_id=1,
    recommended=recommendation_list
)

print(f"Diversity: {evaluation['diversity_score']:.2f}")
print(f"Precision@5: {evaluation['precision_at_k']['p@5']:.2f}")
```

---

## 🔌 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### Get Recommendations
```bash
POST /api/recommendations
Content-Type: application/json

{
  "user_id": 1,
  "query": "upbeat songs for working out",
  "enable_time_matching": true,
  "enable_reranking": true,
  "genre_filter": "pop"  # optional
}
```

#### Record Feedback
```bash
POST /api/feedback
Content-Type: application/json

{
  "user_id": 1,
  "song_id": 123,
  "rating": 5,
  "action_type": "like"
}
```

#### Get User Profile
```bash
GET /api/users/{user_id}/profile
```

#### Create User
```bash
POST /api/users
Content-Type: application/json

{
  "username": "john_doe"
}
```

Full API documentation available at `/api/docs` (coming soon).

---

## 🧪 Testing

### Test Individual Components

```bash
# Test Spotify collector
python src/data_collection/spotify_collector.py

# Test Lyrics collector
python src/data_collection/lyrics_collector.py

# Test Qdrant manager
python src/database/qdrant_manager.py

# Test agents
python src/agents/retriever.py
python src/agents/curator.py

# Test time matcher
python src/tools/time_of_day_matcher.py

# Test reranker
python src/reranker/cohere_reranker.py

# Test full system
python src/recommendation_system.py
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=src tests/
```

---

## 📈 Performance Tips

1. **Use Caching**
   - API responses are cached by default
   - Set `ENABLE_CACHING=true` in config

2. **Batch Processing**
   - Embeddings are batched (50 songs at a time)
   - Adjust batch size in config if needed

3. **Local Qdrant**
   - Use local Docker instance for faster retrieval
   - Cloud Qdrant for production

4. **Rate Limiting**
   - Delays configured for each API
   - Adjust in config if you have higher rate limits

---

## 🎓 Academic Context

This project demonstrates:

- ✅ Multi-agent RAG architecture
- ✅ Vector database integration (Qdrant)
- ✅ Semantic search with embeddings
- ✅ Reranking optimization (Cohere)
- ✅ Deterministic tools (time-of-day matching)
- ✅ Dual memory systems (short-term + long-term)
- ✅ Comprehensive evaluation metrics
- ✅ A/B testing framework
- ✅ Real-world data integration (Spotify, Genius)
- ✅ Production-ready architecture

**Key Learning Outcomes:**
- Agent coordination and orchestration
- RAG pipeline design
- Vector similarity search
- User modeling and personalization
- Recommendation system evaluation
- API integration and data collection

---

## 🛠️ Troubleshooting

### Common Issues

**Qdrant Connection Error**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Restart Qdrant
docker restart <qdrant_container>
```

**API Rate Limits**
```bash
# Increase delays in config.py
SPOTIFY_RATE_LIMIT_DELAY = 0.5
GENIUS_RATE_LIMIT_DELAY = 1.0
```

**Out of Memory**
```bash
# Reduce batch size in config.py
# Or collect fewer songs
python collect_data.py --limit 100
```

**Import Errors**
```bash
# Make sure you're in the project root
cd "Final Project"

# Activate virtual environment
source venv/bin/activate
```

---

## 📝 License

This project is for academic purposes only.

---

## 🙏 Acknowledgments

- **Spotify** for music data API
- **Genius** for lyrics API
- **OpenAI** for embeddings and LLM
- **Cohere** for reranking capabilities
- **Qdrant** for vector database
- **LangChain** for agent framework
- **GSU Text Analytics Course** for project guidance

---

## 📧 Contact

For questions or issues, please open an issue on GitHub or contact the project maintainer.

---

**Built with ❤️ for Georgia State University Text Analytics Final Project**
