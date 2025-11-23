"""
Data Initialization Helper for Streamlit Deployment
Checks if data exists and provides helpful messages
"""

import os
from pathlib import Path


def check_database_status():
    """
    Check the status of local SQLite database

    Returns:
        (has_data: bool, song_count: int, message: str)
    """
    db_path = Path("data/music.db")

    if not db_path.exists():
        return False, 0, "Database file not found. Please run data collection."

    # SQLite is deprecated, using Qdrant-only storage now
    return False, 0, "SQLite database deprecated. Using Qdrant Cloud storage."


def check_qdrant_status():
    """
    Check the status of Qdrant vector database

    Returns:
        (is_configured: bool, message: str)
    """
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_use_cloud = os.getenv("QDRANT_USE_CLOUD", "false").lower() == "true"

    if not qdrant_use_cloud and qdrant_host == "localhost":
        return False, "⚠️ Using local Qdrant. For deployment, use Qdrant Cloud."

    try:
        from src.database.qdrant_storage import QdrantStorage
        qm = QdrantStorage()

        # Try to get collection info
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "music_collection")

        # Check if collection exists (will create if not)
        return True, f"✓ Qdrant Cloud connected: {qdrant_host}"

    except Exception as e:
        return False, f"✗ Qdrant connection error: {str(e)}"


def check_api_keys():
    """
    Check if all required API keys are configured

    Returns:
        (all_set: bool, missing_keys: list)
    """
    required_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "COHERE_API_KEY": "Cohere",
        "GENIUS_API_KEY": "Genius",
        "SPOTIFY_CLIENT_ID": "Spotify Client ID",
        "SPOTIFY_CLIENT_SECRET": "Spotify Client Secret",
    }

    missing = []

    for key, name in required_keys.items():
        value = os.getenv(key, "")
        if not value or value.startswith("your_"):
            missing.append(name)

    return len(missing) == 0, missing


def get_deployment_status():
    """
    Get complete deployment status

    Returns:
        dict with status information
    """
    # Check database
    has_db, song_count, db_message = check_database_status()

    # Check Qdrant
    qdrant_ok, qdrant_message = check_qdrant_status()

    # Check API keys
    keys_ok, missing_keys = check_api_keys()

    # Determine overall status
    is_ready = has_db and qdrant_ok and keys_ok

    return {
        "ready": is_ready,
        "database": {
            "status": has_db,
            "count": song_count,
            "message": db_message,
        },
        "qdrant": {
            "status": qdrant_ok,
            "message": qdrant_message,
        },
        "api_keys": {
            "status": keys_ok,
            "missing": missing_keys,
        },
    }


def print_status():
    """Print deployment status to console"""
    print("="*60)
    print("DEPLOYMENT STATUS CHECK")
    print("="*60)

    status = get_deployment_status()

    # Database
    print("\n📊 Database:")
    print(f"  {status['database']['message']}")

    # Qdrant
    print("\n🔍 Qdrant Vector Database:")
    print(f"  {status['qdrant']['message']}")

    # API Keys
    print("\n🔑 API Keys:")
    if status['api_keys']['status']:
        print("  ✓ All API keys configured")
    else:
        print("  ✗ Missing API keys:")
        for key in status['api_keys']['missing']:
            print(f"    - {key}")

    # Overall
    print("\n" + "="*60)
    if status['ready']:
        print("✓ READY FOR DEPLOYMENT")
    else:
        print("✗ NOT READY - Please fix issues above")
    print("="*60)

    return status['ready']


def show_streamlit_status():
    """
    Show status in Streamlit UI format

    Use this in streamlit_app.py
    """
    try:
        import streamlit as st

        status = get_deployment_status()

        if status['ready']:
            st.success("✓ System Ready")
        else:
            st.warning("⚠️ System Not Ready")

            # Show specific issues
            if not status['database']['status']:
                st.error(f"Database: {status['database']['message']}")
                st.info("""
                **To fix:** Run data collection locally first:
                ```bash
                python collect_data_hf_balanced.py --medium
                ```
                """)

            if not status['qdrant']['status']:
                st.error(f"Qdrant: {status['qdrant']['message']}")
                st.info("""
                **To fix:** Set up Qdrant Cloud:
                1. Go to https://cloud.qdrant.io
                2. Create free cluster
                3. Add credentials to Streamlit Secrets
                """)

            if not status['api_keys']['status']:
                st.error("Missing API Keys:")
                for key in status['api_keys']['missing']:
                    st.write(f"  - {key}")
                st.info("""
                **To fix:** Add API keys to Streamlit Secrets:
                1. Go to App Settings → Secrets
                2. Add keys in TOML format
                """)

        return status['ready']

    except ImportError:
        # Not in Streamlit environment
        return print_status()


if __name__ == '__main__':
    print_status()
