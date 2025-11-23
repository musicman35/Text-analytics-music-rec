# Streamlit Deployment - Quick Start

**5-Minute Deployment Guide**

---

## Step 1: Prepare Data (Local)

```bash
# Collect balanced dataset
python collect_data_hf_balanced.py --medium

# Verify data
python init_data.py
```

Expected: "✓ READY FOR DEPLOYMENT"

---

## Step 2: Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Ready for deployment"

# Push
git push origin main
```

**Verify:** Repository is public at `github.com/YOUR_USERNAME/music-recommendation-system`

---

## Step 3: Deploy to Streamlit Cloud

### 3.1 Sign Up
1. Go to: https://streamlit.io/cloud
2. Click: **"Continue with GitHub"**
3. Authorize Streamlit

### 3.2 Create App
1. Click: **"New app"**
2. Fill in:
   - **Repository**: `YOUR_USERNAME/music-recommendation-system`
   - **Branch**: `main`
   - **Main file**: `streamlit_app.py`
3. Click: **"Advanced settings"**

### 3.3 Add Secrets
Paste in TOML format:

```toml
SPOTIFY_CLIENT_ID = "paste_from_your_env"
SPOTIFY_CLIENT_SECRET = "paste_from_your_env"
GENIUS_API_KEY = "paste_from_your_env"
OPENAI_API_KEY = "paste_from_your_env"
COHERE_API_KEY = "paste_from_your_env"
QDRANT_HOST = "your-cluster.qdrant.io"
QDRANT_API_KEY = "paste_from_your_env"
QDRANT_USE_CLOUD = "true"
```

**Where to get values:** Copy from your `.env` file

### 3.4 Deploy
1. Click: **"Deploy!"**
2. Wait: 3-5 minutes
3. Done! Your app is live

---

## Step 4: Test

Visit your app URL:
```
https://your-app-name.streamlit.app
```

Test:
- ✅ Create user
- ✅ Search songs
- ✅ Get recommendations
- ✅ View profile

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'datasets'"
**Fix:** Add `datasets` to `requirements.txt`, push to GitHub

### "Database file not found"
**Options:**
1. Collect data in cloud (slower)
2. Use Qdrant Cloud only (recommended)
3. Upload database (not recommended for large files)

### "Invalid API key"
**Fix:**
1. Go to App Settings (⚙️)
2. Click "Secrets"
3. Verify all keys
4. Save (app auto-restarts)

---

## Update App

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Auto-deploys in 1-2 minutes
```

---

## Costs

**Streamlit Cloud:** FREE
**OpenAI:** ~$5-10/month
**Cohere:** FREE (with limits)
**Qdrant Cloud:** FREE (<1GB)

**Total:** ~$5-10/month

---

## Alternative: Local Demo

If deployment fails:

```bash
# Run locally
streamlit run streamlit_app.py

# Record video demo
# Share GitHub repo link
```

---

## Complete Guide

For detailed instructions, see: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## Quick Commands

```bash
# Check deployment readiness
python init_data.py

# Collect data (balanced)
python collect_data_hf_balanced.py --medium

# Test locally
streamlit run streamlit_app.py

# Push to GitHub
git add . && git commit -m "Deploy" && git push
```

---

**That's it! Your app should be live in 5 minutes.**

🚀 App URL: `https://your-app-name.streamlit.app`
