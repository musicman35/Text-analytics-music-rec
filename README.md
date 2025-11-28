# Multi-Agent Music Recommendation System

A sophisticated music recommendation system using multi-agent architecture, RAG (Retrieval-Augmented Generation), and Cohere reranking with lyrics-enhanced semantic search.

**Built for:** Graduate Text Analytics Final Project - Fall 2025
**Storage:** Qdrant Cloud (vector database)
**Data Source:** HuggingFace Spotify Dataset + Genius API (lyrics)
**Deployment:** Streamlit Cloud-ready

---

## 🎯 Features

### Multi-Agent Architecture
- **Retriever Agent**: Semantic search using vector embeddings
- **Analyzer Agent**: User profile analysis and preference learning
- **Curator Agent**: Multi-stage recommendation curation with reranking
- **Critic Agent**: Quality evaluation and diversity scoring

### Advanced Technologies
- **RAG Pipeline**: Retrieval-Augmented Generation for context-aware recommendations
- **Lyrics Integration**: Song lyrics embedded for thematic/mood-based search
- **Cohere Reranking**: Semantic reordering of top candidates
- **Vector Search**: Qdrant Cloud for scalable similarity search
- **Dual Memory Systems**: Short-term session + long-term user profile
- **Time-of-Day Matching**: Recommendations adjusted to time context
- **Audio Features**: 12 audio characteristics from Spotify dataset

### Data
- **7,400+ songs** across 5 genres (pop, rock, hip-hop, electronic, R&B)
- **~62% with lyrics** for enhanced semantic search
- Rich metadata: audio features, artist info, popularity

---

## 🚀 Quick Start

### 1. Install
```bash
git clone https://github.com/YOUR_USERNAME/music-recommendation-system.git
cd music-recommendation-system
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
Copy `.env.template` to `.env` and add your API keys:
- **Qdrant Cloud**: https://cloud.qdrant.io (FREE tier available)
- **OpenAI**: https://platform.openai.com (for embeddings)
- **Cohere**: https://dashboard.cohere.com (for reranking)
- **Genius**: https://genius.com/api-clients (for lyrics - data collection only)

### 3. Collect Data (with Lyrics)
```bash
# Quick test (~1 min)
python collect_lyrics.py --quick

# Medium dataset (~10 min)
python collect_lyrics.py --medium

# Full dataset (~20 min)
python collect_lyrics.py --large
```

### 4. Run
```bash
streamlit run streamlit_app.py
```

---

## 📁 Project Structure

```
├── config.py                 # Configuration settings
├── streamlit_app.py          # Main Streamlit web interface
├── collect_lyrics.py         # Data collection with lyrics
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
│   │   └── time_of_day_matcher.py  # Time-based scoring
│   │
│   ├── evaluation/
│   │   └── metrics.py        # Recommendation metrics
│   │
│   └── recommendation_system.py  # Main orchestrator
```

---

## 🔧 How It Works

### Recommendation Pipeline

1. **Retrieval**: RetrieverAgent performs semantic search on Qdrant to find candidate songs based on query + lyrics content
2. **Analysis**: AnalyzerAgent builds user profile from interaction history
3. **Curation**: CuratorAgent scores candidates using:
   - Semantic similarity
   - User preference matching
   - Time-of-day context
   - Cohere reranking
4. **Evaluation**: CriticAgent assesses diversity and quality

### Lyrics Integration

Songs are embedded with lyrics content, enabling:
- Thematic searches ("songs about heartbreak")
- Mood-based discovery ("motivational lyrics")
- Enhanced semantic matching beyond audio features

---

## 💰 Costs

| Service | Cost |
|---------|------|
| Qdrant Cloud (FREE tier) | $0/month |
| OpenAI Embeddings | ~$2-5/month |
| Cohere (FREE tier) | $0/month |
| Genius API (FREE) | $0/month |
| **Total** | **~$2-5/month** |

---

## 🌐 Deploy to Streamlit Cloud

1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets (API keys) in Streamlit Cloud settings
4. Deploy!

---

**Built with Python, LangChain, Qdrant, OpenAI, Cohere, and Streamlit**
