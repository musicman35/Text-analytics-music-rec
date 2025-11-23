# GitHub Repository Setup Guide

## ✅ Git Repository Initialized

Your local Git repository has been initialized and the initial commit has been made!

**Commit Summary:**
- 35 files committed
- 6,681 lines of code
- All core components, documentation, and scripts included

---

## 🔗 Connect to GitHub

### Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and log in
2. Click the **"+"** icon in the top right
3. Select **"New repository"**
4. Configure your repository:
   - **Repository name**: `music-recommendation-system` (or your choice)
   - **Description**: Multi-Agent RAG Music Recommendation System with Cohere Reranking
   - **Visibility**:
     - ✅ **Public** (recommended for portfolio/academic work)
     - Or **Private** (if you prefer)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

5. Click **"Create repository"**

### Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Navigate to your project
cd "/Users/kennethstallworth/Documents/Fall 2025 GSU/Text Analytics/Projects/Final Project"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/music-recommendation-system.git

# Verify remote was added
git remote -v

# Push to GitHub
git push -u origin main
```

### Step 3: Verify Upload

After pushing, refresh your GitHub repository page. You should see:
- All 35 files
- README.md displayed on the main page
- Your commit message

---

## 📝 For Streamlit Deployment (Optional)

If you want to deploy the Streamlit app to Streamlit Community Cloud:

### Prerequisites:
1. Your GitHub repository must be **public**
2. You need a Streamlit Community Cloud account (free)

### Steps:

1. **Go to Streamlit Community Cloud**
   - Visit: https://streamlit.io/cloud
   - Sign in with GitHub

2. **Deploy App**
   - Click "New app"
   - Select your repository: `YOUR_USERNAME/music-recommendation-system`
   - Main file path: `streamlit_app.py`
   - Click "Deploy"

3. **Configure Secrets**
   - Go to your app settings
   - Add "Secrets" section
   - Copy contents of your `.env` file (the actual values, not the template)
   - Format as TOML:

```toml
SPOTIFY_CLIENT_ID = "your_actual_client_id"
SPOTIFY_CLIENT_SECRET = "your_actual_client_secret"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

GENIUS_API_KEY = "your_actual_genius_key"

OPENAI_API_KEY = "your_actual_openai_key"
COHERE_API_KEY = "your_actual_cohere_key"

QDRANT_HOST = "your_qdrant_cloud_url"
QDRANT_API_KEY = "your_qdrant_api_key"
QDRANT_USE_CLOUD = "true"
QDRANT_PORT = "6333"
```

4. **Important Notes for Deployment:**
   - Streamlit Cloud has limited resources
   - Data collection should be done locally first
   - Upload your `data/music.db` file after collecting songs
   - Qdrant Cloud is required (local Qdrant won't work on Streamlit Cloud)

---

## 🔒 Security Reminder

**NEVER commit your `.env` file to GitHub!**

The `.gitignore` file already excludes:
- `.env`
- `data/` directory (contains your database)
- `venv/` (virtual environment)
- `__pycache__/` (Python cache)

This ensures your API keys and data stay private.

---

## 📊 Repository Statistics

Your repository includes:
- **27 Python files** (~5,100+ lines of code)
- **4 Specialized AI Agents**
- **Complete RAG Pipeline**
- **Web Interface** (Streamlit + Flask)
- **Comprehensive Documentation**
- **Data Collection Scripts**
- **Evaluation Framework**

---

## 🎯 Next Steps

1. ✅ Create GitHub repository
2. ✅ Push code to GitHub
3. 🔄 Collect music data: `python collect_data.py --quick`
4. 🚀 Run the app: `streamlit run streamlit_app.py`
5. (Optional) Deploy to Streamlit Cloud

---

## 🆘 Troubleshooting

### Authentication Issues

If you get authentication errors when pushing:

**Option 1: Use Personal Access Token (Recommended)**
```bash
# Generate token at: https://github.com/settings/tokens
# Use token as password when prompted
git push -u origin main
```

**Option 2: Use SSH**
```bash
# Change remote URL to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/music-recommendation-system.git
git push -u origin main
```

### Need to change repository name?
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/NEW_REPO_NAME.git
```

---

Good luck with your project! 🎵
