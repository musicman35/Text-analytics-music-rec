# Multi-Agent Music Recommendation System

A sophisticated music recommendation system using multi-agent architecture, RAG (Retrieval-Augmented Generation), and Cohere reranking.

**Built for:** Graduate Text Analytics Final Project  
**Storage:** Qdrant Cloud (vector database)  
**Data Source:** Hugging Face + Genius API  
**Deployment:** Streamlit Cloud-ready

---

## 🎯 Features

### Multi-Agent Architecture
- **Retriever Agent**: Semantic search using vector embeddings
- **Analyzer Agent**: User profile analysis and preference learning
- **Curator Agent**: Multi-stage recommendation curation with reranking
- **Critic Agent**: Quality evaluation and diversity scoring

### Advanced Technologies
- ✅ **RAG Pipeline**: Retrieval-Augmented Generation for context-aware recommendations
- ✅ **Cohere Reranking**: Semantic reordering of top candidates
- ✅ **Vector Search**: Qdrant Cloud for scalable similarity search
- ✅ **Dual Memory Systems**: Short-term session + long-term user profile
- ✅ **Audio Features**: 12 audio characteristics from Spotify dataset

### Cloud-Native Design
- ✅ **Qdrant-Only Storage**: No local databases
- ✅ **Persistent Data**: Survives app restarts
- ✅ **Scalable**: Cloud-native vector database

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
- Qdrant Cloud: https://cloud.qdrant.io (FREE)
- OpenAI: https://platform.openai.com
- Cohere: https://dashboard.cohere.com
- Genius: https://genius.com/api-clients

### 3. Collect Data
```bash
python collect_data_qdrant_only.py --medium  # 500 songs
```

### 4. Run
```bash
streamlit run streamlit_app.py
```

---

## 🌐 Deploy to Streamlit Cloud

**3-Step Deployment:**
1. Setup Qdrant Cloud (https://cloud.qdrant.io)
2. Collect data: `python collect_data_qdrant_only.py --medium`
3. Deploy to Streamlit Cloud with API keys

**Full guide:** [QDRANT_ONLY_DEPLOYMENT.md](QDRANT_ONLY_DEPLOYMENT.md)

---

## 💰 Costs

| Service | Cost |
|---------|------|
| Qdrant Cloud (FREE tier) | $0/month |
| OpenAI | ~$5-10/month |
| Cohere (FREE tier) | $0/month |
| **Total** | **~$5-10/month** |

---

## 📖 Documentation

- [Quickstart](QUICKSTART.md)
- [Deployment Guide](QDRANT_ONLY_DEPLOYMENT.md)
- [Deployment Summary](QDRANT_DEPLOYMENT_SUMMARY.md)
- [Project Overview](PROJECT_OVERVIEW.md)

---

**Built with ❤️ for Text Analytics Fall 2025**
