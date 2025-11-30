# Multi-Agent Music Recommendation System

A music recommendation system using multi-agent architecture, RAG (Retrieval-Augmented Generation), and Cohere reranking with lyrics-enhanced semantic search.

**Course:** Graduate Text Analytics Final Project - Fall 2025
**Storage:** Qdrant Cloud (vector database)
**Data Source:** HuggingFace Spotify Dataset + Genius API (lyrics)
**Deployment:** Streamlit Cloud-ready

---

## Features

### Multi-Agent Architecture
- **Retriever Agent**: Semantic search using vector embeddings
- **Analyzer Agent**: User profile analysis and preference learning
- **Curator Agent**: Multi-stage recommendation curation with reranking
- **Critic Agent**: Quality evaluation and diversity scoring

### Core Technologies
- **RAG Pipeline**: Retrieval-Augmented Generation for context-aware recommendations
- **Lyrics Integration**: Song lyrics embedded for thematic/mood-based search
- **Cohere Reranking**: Semantic reordering of top candidates
- **Vector Search**: Qdrant Cloud for scalable similarity search
- **Dual Memory Systems**: Short-term session + long-term user profile
- **Time-of-Day Matching**: Deterministic tool that adjusts recommendations to time context
- **Audio Features**: 12 audio characteristics from Spotify dataset

### Dataset
- **7,400+ songs** across 5 genres (pop, rock, hip-hop, electronic, R&B)
- **~62% with lyrics** for enhanced semantic search
- Rich metadata: audio features, artist info, popularity

---

## Quick Start

### 1. Install
```bash
git clone https://github.com/musicman35/Text-analytics-music-rec.git
cd Text-analytics-music-rec
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
Copy `.env.template` to `.env` and add your API keys:
- **Qdrant Cloud**: https://cloud.qdrant.io (FREE tier available)
- **OpenAI**: https://platform.openai.com (for embeddings)
- **Cohere**: https://dashboard.cohere.com (for reranking)
- **Genius**: https://genius.com/api-clients (for lyrics - data collection only)

### 3. Collect Data
```bash
# Quick test (~1 min)
python collect_lyrics.py --quick

# Medium dataset (~10 min)
python collect_lyrics.py --medium

# Full dataset (~20 min)
python collect_lyrics.py --large
```

### 4. Run Application
```bash
streamlit run streamlit_app.py
```

### 5. Run Evaluation (Optional)
```bash
python run_evaluation.py
```
Results and figures are saved to `evaluation_results/`.

---

## Project Structure

```
├── config.py                 # Configuration settings
├── streamlit_app.py          # Main Streamlit web interface
├── collect_lyrics.py         # Data collection with lyrics
├── run_evaluation.py         # Evaluation framework runner
├── verify_qdrant_data.py     # Database verification utility
├── requirements.txt          # Python dependencies
├── .env.template             # Environment variables template
│
├── src/
│   ├── agents/
│   │   ├── retriever.py      # Semantic search agent
│   │   ├── analyzer.py       # User analysis agent
│   │   ├── curator.py        # Recommendation curation agent
│   │   └── critic.py         # Evaluation agent
│   │
│   ├── database/
│   │   └── qdrant_storage.py # Qdrant vector database interface
│   │
│   ├── data_collection/
│   │   ├── huggingface_collector.py  # HuggingFace dataset collector
│   │   └── lyrics_fetcher.py         # Genius API lyrics fetcher
│   │
│   ├── memory/
│   │   ├── short_term.py     # Session-based memory
│   │   └── long_term.py      # Persistent user profile
│   │
│   ├── reranker/
│   │   └── cohere_reranker.py  # Cohere reranking integration
│   │
│   ├── tools/
│   │   └── time_of_day_matcher.py  # Time-based scoring tool
│   │
│   ├── utils/
│   │   └── audio_features.py # Shared audio feature utilities
│   │
│   ├── evaluation/
│   │   ├── metrics.py        # Recommendation metrics (Precision@K, Diversity, etc.)
│   │   ├── baselines.py      # Baseline recommenders (Random, Popularity, Content-Only)
│   │   ├── scenarios.py      # Test scenario definitions
│   │   └── visualizations.py # Chart generation (matplotlib)
│   │
│   └── recommendation_system.py  # Main orchestrator
```

---

## How It Works

### Recommendation Pipeline

1. **Retrieval**: RetrieverAgent performs semantic search on Qdrant to find 50 candidate songs based on query and lyrics content
2. **Analysis**: AnalyzerAgent builds user profile from interaction history (genre preferences, audio feature preferences, time patterns)
3. **Curation**: CuratorAgent scores and ranks candidates using:
   - Semantic similarity from vector search
   - User preference matching via collaborative filtering
   - Time-of-day context adjustments
   - Cohere neural reranking
4. **Evaluation**: CriticAgent assesses diversity, quality, and generates explanations

### Memory System

**Short-Term Memory**: Maintains session context including recent queries, current session interactions, and temporary preferences. Enables coherent multi-turn conversations.

**Long-Term Memory**: Stores persistent user profiles with weighted genre preferences, audio feature preferences, liked/disliked artists, and time-of-day patterns. Updates automatically after threshold interactions.

### Lyrics Integration

Songs are embedded with lyrics content, enabling:
- Thematic searches ("songs about heartbreak")
- Mood-based discovery ("motivational lyrics")
- Enhanced semantic matching beyond audio features alone

---

## Evaluation

The evaluation framework compares the full system against baselines:

| Method | Precision@5 | Precision@10 | Diversity | Query Relevance |
|--------|-------------|--------------|-----------|-----------------|
| Random | 0.20 | 0.28 | 0.85 | 0.77 |
| Popularity | 0.16 | 0.12 | 0.83 | 0.74 |
| Content-Only | 0.88 | 0.80 | 0.65 | 0.87 |
| Full System | 0.92 | 0.88 | 0.65 | 0.98 |

Feature ablation shows the contribution of each component:
- Reranking: +10% improvement
- Time Matching: +12% improvement
- Lyrics Integration: +65% improvement
- Memory/Personalization: +18% improvement

Run `python run_evaluation.py` to generate results and visualization figures.

---

## API Costs

| Service | Cost |
|---------|------|
| Qdrant Cloud (FREE tier) | $0/month |
| OpenAI Embeddings | ~$2-5/month |
| Cohere (FREE tier) | $0/month |
| Genius API (FREE) | $0/month |
| **Total** | **~$2-5/month** |

---

## Deployment

### Streamlit Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets (API keys) in Streamlit Cloud settings
4. Deploy

---

**Built with Python, LangChain, Qdrant, OpenAI, Cohere, and Streamlit**
