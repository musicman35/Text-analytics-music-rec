# 🚀 Quick Start Guide

Get the Music Recommendation System running in 5 minutes!

## Prerequisites

- Python 3.9+
- Docker (for Qdrant)
- API Keys (Spotify, Genius, OpenAI, Cohere)

## Step-by-Step Setup

### 1. Run Setup Script

```bash
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Create .env file from template
- Set up data directories

### 2. Configure API Keys

Edit the `.env` file with your API keys:

```bash
nano .env
```

Add your keys:
```bash
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here
GENIUS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
COHERE_API_KEY=your_key_here
```

**Get API Keys:**
- Spotify: https://developer.spotify.com/dashboard
- Genius: https://genius.com/api-clients
- OpenAI: https://platform.openai.com/api-keys
- Cohere: https://dashboard.cohere.com/api-keys

### 3. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Leave this running in a separate terminal.

### 4. Collect Test Data (100 songs)

```bash
python collect_data.py --quick
```

This takes about 5-10 minutes and collects:
- 100 songs from Spotify (20 per genre)
- Lyrics from Genius
- Creates embeddings and populates Qdrant

### 5. Start the Application

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at http://localhost:8501

## Using the System

1. **Register**: Create a username
2. **Search**: Enter a query like "upbeat songs for working out"
3. **Rate**: Give feedback on recommendations
4. **Explore**: Check your profile and agent traces

## Commands Cheat Sheet

```bash
# Setup
./setup.sh                          # Initial setup
source venv/bin/activate            # Activate environment

# Data Collection
python collect_data.py --quick      # Quick test (100 songs)
python collect_data.py              # Full collection (5000 songs)
python collect_data.py --limit 50   # Custom limit per genre

# Run Application
streamlit run streamlit_app.py      # Web interface
python src/api/flask_app.py         # REST API

# Testing
python src/agents/retriever.py      # Test retriever
python src/agents/curator.py        # Test curator
python src/recommendation_system.py # Test full system
```

## Troubleshooting

### Qdrant not connecting
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Restart Qdrant
docker restart <container_id>
```

### API rate limits
Wait a few minutes and try again, or adjust delays in `config.py`:
```python
SPOTIFY_RATE_LIMIT_DELAY = 0.5
GENIUS_RATE_LIMIT_DELAY = 1.0
```

### Import errors
Make sure you're in the project root:
```bash
cd "Final Project"
source venv/bin/activate
```

## What's Next?

After testing with 100 songs:

1. **Collect Full Dataset**:
   ```bash
   python collect_data.py
   ```
   This takes 2-3 hours and collects 5000 songs.

2. **Explore Features**:
   - Try different queries
   - Rate songs to build your profile
   - Compare with/without reranking
   - View agent reasoning traces

3. **Run Evaluations**:
   - Check the Evaluation tab in the app
   - Compare strategies using A/B testing

4. **API Integration**:
   - Start Flask API: `python src/api/flask_app.py`
   - Test endpoints at http://localhost:5000

## Getting Help

- Check [README.md](README.md) for full documentation
- Review code comments and docstrings
- Test individual components using their `if __name__ == "__main__"` blocks

---

Happy recommending! 🎵
