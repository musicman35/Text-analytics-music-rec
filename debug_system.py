#!/usr/bin/env python
"""
Debug script to test the music recommendation system
Checks each component systematically
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def test_environment():
    """Test environment variables"""
    print("\n" + "="*60)
    print("1. TESTING ENVIRONMENT VARIABLES")
    print("="*60)

    required_vars = {
        "QDRANT_HOST": os.getenv("QDRANT_HOST"),
        "QDRANT_API_KEY": os.getenv("QDRANT_API_KEY"),
        "QDRANT_USE_CLOUD": os.getenv("QDRANT_USE_CLOUD"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "COHERE_API_KEY": os.getenv("COHERE_API_KEY")
    }

    for var, value in required_vars.items():
        if value:
            if "KEY" in var:
                print(f"✓ {var}: {'*' * 10} (hidden)")
            else:
                print(f"✓ {var}: {value[:50]}...")
        else:
            print(f"✗ {var}: NOT SET")

    return all(required_vars.values())

def test_qdrant_connection():
    """Test Qdrant connection and collections"""
    print("\n" + "="*60)
    print("2. TESTING QDRANT CONNECTION")
    print("="*60)

    try:
        from src.database.qdrant_storage import QdrantStorage

        print("Creating QdrantStorage instance...")
        storage = QdrantStorage()
        print("✓ QdrantStorage created successfully")

        # Check collections
        try:
            collections = storage.client.get_collections()
            print(f"\nCollections found: {[c.name for c in collections.collections]}")

            # Check song collection
            if storage.songs_collection in [c.name for c in collections.collections]:
                collection_info = storage.client.get_collection(storage.songs_collection)
                print(f"✓ Songs collection: {collection_info.vectors_count} vectors")
            else:
                print(f"✗ Songs collection '{storage.songs_collection}' not found")

            return True

        except Exception as e:
            print(f"✗ Error accessing collections: {e}")
            return False

    except Exception as e:
        print(f"✗ Error creating QdrantStorage: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_functionality():
    """Test search functionality"""
    print("\n" + "="*60)
    print("3. TESTING SEARCH FUNCTIONALITY")
    print("="*60)

    try:
        from src.database.qdrant_storage import QdrantStorage

        storage = QdrantStorage()

        # Test search
        print("Testing search for 'happy songs'...")
        results = storage.search_songs("happy songs", limit=5)

        if results:
            print(f"✓ Found {len(results)} results")
            for i, song in enumerate(results[:3], 1):
                print(f"  {i}. {song.get('name', 'Unknown')} by {song.get('artist', 'Unknown')}")
        else:
            print("✗ No results found - database may be empty")

        return len(results) > 0

    except Exception as e:
        print(f"✗ Search error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retriever_agent():
    """Test RetrieverAgent"""
    print("\n" + "="*60)
    print("4. TESTING RETRIEVER AGENT")
    print("="*60)

    try:
        from src.agents.retriever import RetrieverAgent

        print("Creating RetrieverAgent...")
        retriever = RetrieverAgent()
        print("✓ RetrieverAgent created")

        # Check if retrieve_with_expansion exists
        if hasattr(retriever, 'retrieve_with_expansion'):
            print("✓ retrieve_with_expansion method exists")

            # Test retrieval
            result = retriever.retrieve_with_expansion(
                "upbeat happy songs",
                use_enhancement=False
            )

            if 'candidates' in result:
                print(f"✓ Retrieved {len(result['candidates'])} candidates")
                return True
            else:
                print(f"✗ Unexpected result format: {result.keys()}")
                return False
        else:
            print("✗ retrieve_with_expansion method not found")
            print(f"Available methods: {[m for m in dir(retriever) if not m.startswith('_')]}")
            return False

    except Exception as e:
        print(f"✗ RetrieverAgent error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_operations():
    """Test user creation and retrieval"""
    print("\n" + "="*60)
    print("5. TESTING USER OPERATIONS")
    print("="*60)

    try:
        from src.database.qdrant_storage import QdrantStorage
        import uuid

        storage = QdrantStorage()

        # Test user creation
        test_username = f"debug_user_{uuid.uuid4().hex[:8]}"
        print(f"Creating test user: {test_username}")

        user_id = storage.create_user(test_username)
        print(f"✓ User created with ID: {user_id}")

        # Test user retrieval by username
        user = storage.get_user(username=test_username)
        if user:
            print(f"✓ User retrieved by username: {user.get('username')}")
        else:
            print("✗ Failed to retrieve user by username")

        # Test user retrieval by ID
        user2 = storage.get_user(user_id=user_id)
        if user2:
            print(f"✓ User retrieved by ID")
        else:
            print("✗ Failed to retrieve user by ID")

        return True

    except Exception as e:
        print(f"✗ User operations error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_pipeline():
    """Test the full recommendation pipeline"""
    print("\n" + "="*60)
    print("6. TESTING FULL RECOMMENDATION PIPELINE")
    print("="*60)

    try:
        from src.recommendation_system import MusicRecommendationSystem
        import uuid

        print("Creating MusicRecommendationSystem...")
        system = MusicRecommendationSystem()
        print("✓ System created")

        # Create test user
        test_user_id = str(uuid.uuid4())

        # Test recommendation
        print(f"\nTesting recommendation for user {test_user_id[:8]}...")
        result = system.get_recommendations(
            user_id=test_user_id,
            query="upbeat pop songs",
            enable_time_matching=False,
            enable_reranking=False
        )

        if 'success' in result:
            if result['success']:
                print(f"✓ Got {len(result.get('recommendations', []))} recommendations")
            else:
                print(f"✗ Pipeline failed: {result.get('message', 'Unknown error')}")
        else:
            print(f"✗ Unexpected result format: {result.keys()}")

        return result.get('success', False)

    except Exception as e:
        print(f"✗ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MUSIC RECOMMENDATION SYSTEM DEBUG")
    print("="*60)

    results = {
        "Environment": test_environment(),
        "Qdrant Connection": test_qdrant_connection(),
        "Search": test_search_functionality(),
        "Retriever Agent": test_retriever_agent(),
        "User Operations": test_user_operations(),
        "Full Pipeline": test_full_pipeline()
    }

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for test, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test}: {status}")

    if all(results.values()):
        print("\n✓ ALL TESTS PASSED")
    else:
        print(f"\n✗ {sum(not v for v in results.values())} TESTS FAILED")
        print("\nRecommendations:")

        if not results["Environment"]:
            print("- Check your .env file and ensure all API keys are set")

        if not results["Qdrant Connection"]:
            print("- Verify Qdrant Cloud credentials and connection")
            print("- Check if Qdrant Cloud instance is running")

        if not results["Search"]:
            print("- Database may be empty - run data collection")
            print("- Check if embeddings are properly stored")

        if not results["Retriever Agent"]:
            print("- Check RetrieverAgent implementation")
            print("- Verify retrieve_with_expansion method exists")

        if not results["Full Pipeline"]:
            print("- Review pipeline stages for errors")
            print("- Check agent integrations")

if __name__ == "__main__":
    main()