# Getting Started - Quick Reference

## ✅ Setup Complete!

Your development environment is ready:
- ✅ Virtual environment created
- ✅ All dependencies installed
- ✅ API keys configured
- ✅ Qdrant Cloud connected

## 🎯 Next Step: Collect Data

### Using Hugging Face Dataset (Recommended)

This approach **bypasses Spotify API restrictions** and provides all audio features immediately.

#### Quick Test (20 songs per genre, ~2-3 minutes)
```bash
python collect_data_hf.py --quick
```

#### Medium Test (100 songs per genre, ~10-15 minutes)
```bash
python collect_data_hf.py --medium
```

#### Full Collection (1000 songs per genre, ~90-120 minutes)
```bash
python collect_data_hf.py --full
```

### What This Does:

1. **Loads Hugging Face Dataset** - Songs with audio features
2. **Fetches Lyrics from Genius** - Only keeps songs with valid lyrics
3. **Validates Quality** - Filters out instrumentals and short lyrics
4. **Balances by Genre** - Equal songs per genre
5. **Saves to Databases** - SQLite + Qdrant vector database

## 📊 Expected Results

### --quick (20 songs/genre)
- Total: ~100 songs
- Time: 2-3 minutes
- Perfect for testing the system

### --medium (100 songs/genre)
- Total: ~500 songs
- Time: 10-15 minutes
- Good for demos

### --full (1000 songs/genre)
- Total: ~5000 songs
- Time: 90-120 minutes
- Final project dataset

## 🚀 After Data Collection

### 1. Launch Streamlit App
```bash
streamlit run streamlit_app.py
```

### 2. Or Use Flask API
```bash
python src/api/flask_app.py
```

## 📝 What Each Song Will Have

```python
{
    'name': 'Song Title',
    'artist': 'Artist Name',
    'genre': 'pop',

    # All audio features (from Hugging Face)
    'features': {
        'danceability': 0.7,
        'energy': 0.8,
        'valence': 0.6,
        'tempo': 120.0,
        # ... 8 more features
    },

    # Validated lyrics (from Genius)
    'lyrics': 'Full song lyrics...'
}
```

## 🔧 Troubleshooting

### If Hugging Face download fails:
```bash
pip install datasets
```

### If Genius API is slow:
The script includes rate limiting (0.5s between requests) to avoid hitting API limits. This is intentional and ensures reliability.

### To check your data after collection:
```python
from src.database.sqlite_manager import SQLiteManager
db = SQLiteManager()
print(f"Total songs: {db.get_song_count()}")
```

## 📚 Learn More

- [HUGGINGFACE_COLLECTION.md](HUGGINGFACE_COLLECTION.md) - Detailed strategy
- [README.md](README.md) - Full project documentation
- [QUICKSTART.md](QUICKSTART.md) - 5-minute overview

## 🎵 Ready to Start?

Run this command:
```bash
python collect_data_hf.py --quick
```

Then launch the app:
```bash
streamlit run streamlit_app.py
```

That's it! You now have a working music recommendation system with:
- ✅ Multi-agent architecture
- ✅ RAG pipeline
- ✅ Cohere reranking
- ✅ Vector search
- ✅ Real audio features
- ✅ Validated lyrics
