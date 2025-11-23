"""Quick setup verification script"""

import sys
import os
from pathlib import Path

print("="*60)
print("SETUP VERIFICATION")
print("="*60)

# Check Python version
print(f"\n✓ Python version: {sys.version.split()[0]}")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ .env file loaded")
except Exception as e:
    print(f"✗ Error loading .env: {e}")
    sys.exit(1)

# Check API keys
print("\nAPI Keys Status:")
keys_to_check = {
    "SPOTIFY_CLIENT_ID": "Spotify Client ID",
    "SPOTIFY_CLIENT_SECRET": "Spotify Client Secret",
    "GENIUS_API_KEY": "Genius API Key",
    "OPENAI_API_KEY": "OpenAI API Key",
    "COHERE_API_KEY": "Cohere API Key"
}

all_keys_set = True
for key, name in keys_to_check.items():
    value = os.getenv(key, "")
    is_set = bool(value and value != f"your_{key.lower()}" and "your_" not in value)
    status = "✓" if is_set else "✗"
    print(f"  {status} {name}: {'Set' if is_set else 'NOT SET'}")
    if not is_set:
        all_keys_set = False

# Check Qdrant configuration
print("\nQdrant Configuration:")
qdrant_cloud = os.getenv("QDRANT_USE_CLOUD", "false").lower() == "true"
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
print(f"  Mode: {'Cloud' if qdrant_cloud else 'Local'}")
print(f"  Host: {qdrant_host}")

if qdrant_cloud:
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    if qdrant_api_key:
        print(f"  ✓ Cloud API Key: Set")
    else:
        print(f"  ✗ Cloud API Key: NOT SET (required for cloud mode)")
        all_keys_set = False

# Test imports
print("\nTesting Core Imports:")
try:
    import config
    print("  ✓ config.py")
except Exception as e:
    print(f"  ✗ config.py: {e}")

try:
    from src.database.sqlite_manager import SQLiteManager
    print("  ✓ SQLiteManager")
except Exception as e:
    print(f"  ✗ SQLiteManager: {e}")

try:
    from src.database.qdrant_manager import QdrantManager
    print("  ✓ QdrantManager")
except Exception as e:
    print(f"  ✗ QdrantManager: {e}")

# Test database initialization
print("\nTesting Database:")
try:
    from src.database.sqlite_manager import SQLiteManager
    db = SQLiteManager()
    print("  ✓ SQLite database initialized")
except Exception as e:
    print(f"  ✗ SQLite error: {e}")

# Test Qdrant connection
print("\nTesting Qdrant Connection:")
if qdrant_cloud:
    print("  ℹ Skipping connection test for cloud (will test during data collection)")
else:
    try:
        from src.database.qdrant_manager import QdrantManager
        qm = QdrantManager()
        print("  ✓ Qdrant client initialized")
        print("  ℹ Note: Collection will be created during data collection")
    except Exception as e:
        print(f"  ✗ Qdrant connection error: {e}")
        print("  ℹ Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")

# Check data directories
print("\nData Directories:")
data_dir = Path("data")
cache_dir = data_dir / "cache"

if data_dir.exists():
    print(f"  ✓ data/ directory exists")
else:
    print(f"  ℹ data/ directory will be created automatically")

if cache_dir.exists():
    print(f"  ✓ data/cache/ directory exists")
else:
    print(f"  ℹ data/cache/ directory will be created automatically")

# Summary
print("\n" + "="*60)
if all_keys_set:
    print("✓ SETUP COMPLETE - Ready to collect data!")
    print("\nNext steps:")
    print("  1. python collect_data.py --quick    # Test with 100 songs")
    print("  2. streamlit run streamlit_app.py    # Launch the app")
else:
    print("✗ SETUP INCOMPLETE - Please configure missing API keys in .env")
print("="*60)
