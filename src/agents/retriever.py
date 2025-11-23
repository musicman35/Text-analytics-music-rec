"""
Retriever Agent
Performs semantic search on Qdrant to retrieve candidate songs
"""

from typing import List, Dict, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
import config
from src.database.qdrant_manager import QdrantManager


class RetrieverAgent:
    """Agent that retrieves relevant songs from vector database"""

    def __init__(self):
        self.qdrant = QdrantManager()
        self.candidate_count = config.RETRIEVAL_CANDIDATE_COUNT

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.AGENT_LLM_MODEL,
            temperature=config.AGENT_TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )

    def retrieve_songs(self, query: str, genre_filter: str = None) -> List[Dict]:
        """
        Retrieve candidate songs based on query

        Args:
            query: User's natural language query
            genre_filter: Optional genre filter

        Returns:
            List of candidate songs
        """
        print(f"\n[RetrieverAgent] Processing query: '{query}'")
        if genre_filter:
            print(f"[RetrieverAgent] Genre filter: {genre_filter}")

        # Perform semantic search in Qdrant
        candidates = self.qdrant.search(
            query=query,
            limit=self.candidate_count,
            genre_filter=genre_filter
        )

        print(f"[RetrieverAgent] Retrieved {len(candidates)} candidate songs")

        return candidates

    def enhance_query(self, query: str, context: Dict = None) -> str:
        """
        Use LLM to enhance/understand user query

        Args:
            query: Original user query
            context: Optional context (short-term memory, etc.)

        Returns:
            Enhanced query for better retrieval
        """
        system_prompt = """You are a music search specialist. Your job is to understand
        user queries about music and reformulate them for better semantic search.

        Consider:
        - Musical characteristics (tempo, energy, mood)
        - Lyrical themes
        - Genre and style
        - Use cases (workout, study, party, etc.)

        Return an enhanced search query that will help find the most relevant songs."""

        messages = [
            ("system", system_prompt),
            ("human", f"Original query: {query}")
        ]

        if context:
            context_str = f"User context: {context}"
            messages.append(("human", context_str))

        messages.append(("human", "Provide an enhanced search query:"))

        try:
            response = self.llm.invoke(messages)
            enhanced = response.content.strip()
            print(f"[RetrieverAgent] Enhanced query: '{enhanced}'")
            return enhanced
        except Exception as e:
            print(f"[RetrieverAgent] Error enhancing query: {e}")
            return query

    def retrieve_with_expansion(self, query: str, use_enhancement: bool = True,
                               genre_filter: str = None, context: Dict = None) -> Dict:
        """
        Retrieve songs with optional query enhancement

        Returns:
            Dict with candidates and metadata
        """
        # Enhance query if requested
        search_query = query
        if use_enhancement and context:
            search_query = self.enhance_query(query, context)

        # Retrieve candidates
        candidates = self.retrieve_songs(search_query, genre_filter)

        return {
            'candidates': candidates,
            'metadata': {
                'original_query': query,
                'search_query': search_query,
                'candidate_count': len(candidates),
                'genre_filter': genre_filter,
                'enhanced': use_enhancement
            }
        }

    def explain_retrieval(self, query: str, candidates: List[Dict], top_n: int = 5) -> str:
        """Generate explanation for why these songs were retrieved"""
        if not candidates:
            return "No songs found matching the query."

        explanation = f"Retrieved {len(candidates)} songs for query: '{query}'\n\n"
        explanation += f"Top {top_n} matches:\n"

        for i, song in enumerate(candidates[:top_n], 1):
            explanation += f"{i}. {song['name']} by {song['artist']}\n"
            explanation += f"   Genre: {song['genre']}, Similarity: {song['score']:.3f}\n"

        return explanation


# Convenience function
def get_retriever_agent() -> RetrieverAgent:
    """Get RetrieverAgent instance"""
    return RetrieverAgent()


# Testing
if __name__ == "__main__":
    print("Testing Retriever Agent\n" + "="*60)

    agent = RetrieverAgent()

    # Test queries
    test_queries = [
        "upbeat songs for working out",
        "sad acoustic songs",
        "chill electronic music for studying"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        result = agent.retrieve_with_expansion(query, use_enhancement=False)

        print(f"\nQuery: {query}")
        print(f"Found {len(result['candidates'])} candidates")

        if result['candidates']:
            print("\nTop 5 results:")
            for i, song in enumerate(result['candidates'][:5], 1):
                print(f"  {i}. {song['name']} by {song['artist']}")
                print(f"     Score: {song['score']:.3f}, Genre: {song['genre']}")

    print(f"\n{'='*60}")
    print("Retriever agent test complete!")
