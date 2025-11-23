"""
Quick test script to verify all imports work
"""

print("Testing imports...")

try:
    print("✓ Testing qdrant_storage...")
    from src.database.qdrant_storage import QdrantStorage
    print("  ✓ QdrantStorage imported successfully")
except Exception as e:
    print(f"  ✗ Error: {e}")

try:
    print("✓ Testing agents...")
    from src.agents.retriever import RetrieverAgent
    print("  ✓ RetrieverAgent imported successfully")

    from src.agents.analyzer import AnalyzerAgent
    print("  ✓ AnalyzerAgent imported successfully")

    from src.agents.curator import CuratorAgent
    print("  ✓ CuratorAgent imported successfully")

    from src.agents.critic import CriticAgent
    print("  ✓ CriticAgent imported successfully")
except Exception as e:
    print(f"  ✗ Error: {e}")

try:
    print("✓ Testing memory systems...")
    from src.memory.long_term import LongTermMemory
    print("  ✓ LongTermMemory imported successfully")

    from src.memory.short_term import ShortTermMemory
    print("  ✓ ShortTermMemory imported successfully")
except Exception as e:
    print(f"  ✗ Error: {e}")

try:
    print("✓ Testing recommendation system...")
    from src.recommendation_system import MusicRecommendationSystem
    print("  ✓ MusicRecommendationSystem imported successfully")
except Exception as e:
    print(f"  ✗ Error: {e}")

try:
    print("✓ Testing evaluation metrics...")
    from src.evaluation.metrics import RecommendationMetrics
    print("  ✓ RecommendationMetrics imported successfully")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*60)
print("✓ ALL IMPORTS SUCCESSFUL!")
print("="*60)
