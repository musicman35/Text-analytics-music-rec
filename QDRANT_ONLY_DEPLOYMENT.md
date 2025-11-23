# Qdrant-Only Deployment Guide

**Zero local files! Perfect for Streamlit Cloud deployment.**

---

## Why Qdrant-Only?

### Problems with SQLite + Streamlit Cloud:
- ❌ Ephemeral storage (database deleted on restart)
- ❌ Large files slow down deployment
- ❌ Can't upload >100MB files to GitHub
- ❌ Complex state management

### Benefits of Qdrant-Only:
- ✅ **Persistent** - Data survives app restarts
- ✅ **Fast** - No file uploads needed
- ✅ **Scalable** - Cloud-native vector database
- ✅ **Simple** - Single source of truth
- ✅ **Free** - Qdrant Cloud free tier (1GB)

---

## Architecture

```
┌──────────────────────┐
│  Streamlit App       │
│  (Deployed)          │
└──────────┬───────────┘
           │
           │ API calls
           ▼
┌──────────────────────┐
│  Qdrant Cloud        │
│  ┌────────────────┐  │
│  │ Songs          │  │  ← All song data + vectors
│  │ (5000 songs)   │  │
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ Users          │  │  ← User profiles
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ Interactions   │  │  ← User feedback
│  └────────────────┘  │
└──────────────────────┘
```

**No SQLite. No local files. Just Qdrant Cloud.**

---

## Step 1: Set Up Qdrant Cloud

### 1.1 Create Free Account

1. Go to: https://cloud.qdrant.io
2. Sign up (GitHub/Google)
3. Create cluster:
   - **Name**: `music-recommender`
   - **Region**: Choose closest to you
   - **Plan**: FREE (1GB storage)

### 1.2 Get Credentials

After cluster is created:

1. Click your cluster
2. Copy:
   - **Cluster URL**: `your-cluster.qdrant.io`
   - **API Key**: `eyJhbGc...` (long string)

### 1.3 Update Local .env

```bash
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_API_KEY=eyJhbGc...your_actual_key
QDRANT_USE_CLOUD=true
QDRANT_PORT=6333
```

**Test connection:**
```bash
python -c "from src.database.qdrant_storage import QdrantStorage; print('✓ Connected')"
```

---

## Step 2: Collect Data to Qdrant Cloud

### 2.1 Run Collection

```bash
# Quick test (20 songs/genre = 100 total)
python collect_data_qdrant_only.py --quick

# Medium (100 songs/genre = 500 total) ⭐ RECOMMENDED
python collect_data_qdrant_only.py --medium

# Full (1000 songs/genre = 5000 total)
python collect_data_qdrant_only.py --full
```

**What happens:**
- ✅ Songs downloaded from Hugging Face
- ✅ Lyrics fetched from Genius
- ✅ Everything uploaded to Qdrant Cloud
- ✅ No local database created

### 2.2 Verify Data

```python
from src.database.qdrant_storage import QdrantStorage

storage = QdrantStorage()
print(f"Songs in Qdrant: {storage.get_song_count()}")
```

Expected: `500` (if using --medium)

---

## Step 3: Update App to Use Qdrant-Only

### 3.1 Modify Main Files

**Option A: Quick Fix (Recommended)**

Add this to the top of files that import SQLiteManager:

```python
# Replace SQLiteManager with QdrantStorage
from src.database.qdrant_storage import QdrantStorage as SQLiteManager
```

**Option B: Full Migration**

Search and replace in all files:
- `from src.database.sqlite_manager import SQLiteManager`
- → `from src.database.qdrant_storage import QdrantStorage`
- `SQLiteManager()` → `QdrantStorage()`

### 3.2 Files to Update

Update these files:
- `streamlit_app.py`
- `src/recommendation_system.py`
- `src/agents/*.py` (if they use SQLite)

### 3.3 Test Locally

```bash
streamlit run streamlit_app.py
```

Verify:
- ✅ Songs load from Qdrant
- ✅ Search works
- ✅ Recommendations work
- ✅ No SQLite errors

---

## Step 4: Deploy to Streamlit Cloud

### 4.1 Update .gitignore

Ensure `.gitignore` has:
```
.env
data/
venv/
__pycache__/
*.db
*.sqlite
```

### 4.2 Push to GitHub

```bash
git add .
git commit -m "Qdrant-only storage for deployment"
git push origin main
```

### 4.3 Deploy on Streamlit Cloud

1. **Go to:** https://streamlit.io/cloud
2. **New app** → Select your repo
3. **Main file:** `streamlit_app.py`
4. **Advanced settings** → Add secrets:

```toml
# Qdrant Cloud (REQUIRED)
QDRANT_HOST = "your-cluster.qdrant.io"
QDRANT_API_KEY = "eyJhbGc...your_actual_key"
QDRANT_USE_CLOUD = "true"
QDRANT_PORT = "6333"

# OpenAI (REQUIRED)
OPENAI_API_KEY = "sk-proj-...your_key"

# Cohere (REQUIRED)
COHERE_API_KEY = "...your_key"

# Genius (Optional - only for data collection)
GENIUS_API_KEY = "...your_key"

# Spotify (Optional - only for data collection)
SPOTIFY_CLIENT_ID = "...your_id"
SPOTIFY_CLIENT_SECRET = "...your_secret"
```

5. **Click Deploy!**

---

## Step 5: Verify Deployment

### 5.1 Check App URL

Your app will be at: `https://your-app.streamlit.app`

### 5.2 Test Features

1. **Create User** → Should work
2. **Search Songs** → Should find songs from Qdrant
3. **Get Recommendations** → Should use all agents
4. **View Profile** → Should track interactions

### 5.3 Monitor Logs

Click **"Manage app"** → **"Logs"** to see:
- ✅ Connected to Qdrant
- ✅ Songs loaded
- ✅ No database errors

---

## Data Storage Details

### What's in Qdrant?

**Songs Collection:**
```json
{
  "id": "spotify_track_id",
  "vector": [0.123, 0.456, ...],  // 1536-dim embedding
  "payload": {
    "name": "Blinding Lights",
    "artist": "The Weeknd",
    "genre": "pop",
    "lyrics": "I've been tryna call...",
    "danceability": 0.514,
    "energy": 0.730,
    "valence": 0.336,
    // ... all audio features
  }
}
```

**Users Collection:**
```json
{
  "id": "user_uuid",
  "payload": {
    "username": "john_doe",
    "created_at": "timestamp"
  }
}
```

**Interactions Collection:**
```json
{
  "id": "interaction_uuid",
  "payload": {
    "user_id": "user_uuid",
    "song_id": "spotify_track_id",
    "interaction_type": "like",
    "timestamp": "timestamp"
  }
}
```

---

## Costs

### Qdrant Cloud FREE Tier
- **Storage**: 1GB
- **Songs**: ~5,000 songs with lyrics (~200KB each)
- **Requests**: Unlimited
- **Cost**: **$0/month** ✅

### API Costs
- **OpenAI**: ~$5-10/month (embeddings + LLM)
- **Cohere**: FREE (reranking with limits)
- **Total**: **~$5-10/month**

---

## Advantages Over SQLite

| Feature | SQLite + Qdrant | Qdrant-Only |
|---------|----------------|-------------|
| **Deployment** | Complex | Simple ✅ |
| **Persistence** | Lost on restart ❌ | Persistent ✅ |
| **File Size** | Large (~100MB) | None ✅ |
| **Scalability** | Limited | Cloud-native ✅ |
| **Maintenance** | Dual systems | Single source ✅ |
| **Backup** | Manual | Automatic ✅ |

---

## Troubleshooting

### "Failed to connect to Qdrant"

**Check:**
1. Qdrant Cloud cluster is running
2. API key is correct in Secrets
3. URL format: `cluster-name.qdrant.io` (no `https://`)

**Fix:**
```toml
QDRANT_HOST = "your-cluster.qdrant.io"  # Correct
# NOT: https://your-cluster.qdrant.io   # Wrong!
```

### "No songs found"

**Reason:** Data not uploaded yet

**Fix:**
1. Run locally: `python collect_data_qdrant_only.py --medium`
2. Verify: `storage.get_song_count()` returns >0
3. Redeploy app

### "Out of memory"

**Reason:** Too many songs or large batches

**Fix:**
1. Use `--medium` instead of `--full`
2. Reduce batch size in code
3. Add caching:
```python
@st.cache_resource
def get_storage():
    return QdrantStorage()
```

---

## Migration from SQLite

If you already have SQLite data:

### Option 1: Re-collect to Qdrant

```bash
python collect_data_qdrant_only.py --medium
```

### Option 2: Migrate Existing Data

```python
from src.database.sqlite_manager import SQLiteManager
from src.database.qdrant_storage import QdrantStorage

# Export from SQLite
sqlite_db = SQLiteManager()
songs = sqlite_db.get_all_songs()

# Import to Qdrant
qdrant = QdrantStorage()
qdrant.add_songs(songs)
```

---

## Best Practices

### 1. Use Caching

```python
@st.cache_resource
def get_storage():
    """Cache Qdrant connection"""
    return QdrantStorage()

@st.cache_data(ttl=3600)
def search_songs(query):
    """Cache search results for 1 hour"""
    storage = get_storage()
    return storage.search_songs(query)
```

### 2. Batch Operations

```python
# Good: Batch upload
storage.add_songs(songs)

# Bad: One by one
for song in songs:
    storage.add_song(song)
```

### 3. Handle Errors

```python
try:
    results = storage.search_songs(query)
except Exception as e:
    st.error(f"Search failed: {e}")
    st.info("Check Qdrant Cloud connection")
```

---

## Summary

**Qdrant-Only Deployment Checklist:**

- [ ] Qdrant Cloud account created
- [ ] Cluster running and credentials copied
- [ ] `.env` updated with Qdrant Cloud config
- [ ] Data collected: `python collect_data_qdrant_only.py --medium`
- [ ] Songs verified in Qdrant: `storage.get_song_count()`
- [ ] Code updated to use `QdrantStorage`
- [ ] Tested locally: `streamlit run streamlit_app.py`
- [ ] Pushed to GitHub (no .env, no data files)
- [ ] Deployed to Streamlit Cloud
- [ ] Secrets added (Qdrant + OpenAI + Cohere)
- [ ] App tested and working

**Result:** Production-ready app with zero local files! 🚀

---

## Quick Commands

```bash
# Setup
pip install qdrant-client openai

# Collect data
python collect_data_qdrant_only.py --medium

# Verify
python -c "from src.database.qdrant_storage import QdrantStorage; print(f'Songs: {QdrantStorage().get_song_count()}')"

# Test locally
streamlit run streamlit_app.py

# Deploy
git add . && git commit -m "Qdrant-only" && git push
```

---

**With Qdrant-only storage, your app is truly cloud-native and deployment-ready!**
