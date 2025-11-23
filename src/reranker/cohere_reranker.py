"""
Cohere Reranker Integration
Reranks candidate songs using Cohere's reranking API
"""

import cohere
from typing import List, Dict
import config


class CohereReranker:
    """Reranks songs using Cohere's reranking model"""

    def __init__(self):
        self.client = cohere.Client(config.COHERE_API_KEY)
        self.model = config.COHERE_RERANK_MODEL

    def prepare_documents(self, songs: List[Dict]) -> List[str]:
        """
        Convert songs to text documents for reranking

        Args:
            songs: List of song dictionaries

        Returns:
            List of text descriptions
        """
        documents = []

        for song in songs:
            features = song.get('features', {})

            # Create feature description
            feature_parts = []

            energy = features.get('energy', 0.5)
            if energy > 0.7:
                feature_parts.append("high energy")
            elif energy < 0.3:
                feature_parts.append("low energy")
            else:
                feature_parts.append("moderate energy")

            valence = features.get('valence', 0.5)
            if valence > 0.7:
                feature_parts.append("positive/happy")
            elif valence < 0.3:
                feature_parts.append("sad/melancholic")
            else:
                feature_parts.append("neutral mood")

            if features.get('danceability', 0) > 0.7:
                feature_parts.append("very danceable")

            if features.get('acousticness', 0) > 0.7:
                feature_parts.append("acoustic")

            if features.get('instrumentalness', 0) > 0.5:
                feature_parts.append("mostly instrumental")

            features_desc = ", ".join(feature_parts)

            # Build document
            doc = f"Song: {song['name']} by {song['artist']}. "
            doc += f"Genre: {song.get('genre', 'unknown')}. "
            doc += f"Characteristics: {features_desc}. "

            # Add lyrics preview if available
            lyrics_preview = song.get('lyrics_preview', '')
            if lyrics_preview:
                doc += f"Lyrics excerpt: {lyrics_preview}"

            documents.append(doc)

        return documents

    def create_rerank_query(self, user_query: str, user_profile_summary: str = None) -> str:
        """
        Create enriched query for reranking

        Args:
            user_query: Original user query
            user_profile_summary: Summary of user preferences

        Returns:
            Enhanced query string
        """
        query = user_query

        if user_profile_summary:
            query += f". User preferences: {user_profile_summary}"

        return query

    def rerank(self, songs: List[Dict], user_query: str,
               user_profile_summary: str = None, top_n: int = None) -> List[Dict]:
        """
        Rerank songs using Cohere

        Args:
            songs: List of candidate songs
            user_query: User's search/recommendation query
            user_profile_summary: Optional user preference summary
            top_n: Number of results to return (default from config)

        Returns:
            Reranked list of songs
        """
        if not songs:
            return []

        if top_n is None:
            top_n = config.COHERE_RERANK_TOP_N

        # Ensure we don't request more than we have
        top_n = min(top_n, len(songs))

        try:
            # Prepare documents
            documents = self.prepare_documents(songs)

            # Create query
            query = self.create_rerank_query(user_query, user_profile_summary)

            # Call Cohere reranker
            results = self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=top_n
            )

            # Map results back to songs
            reranked_songs = []
            for result in results.results:
                song = songs[result.index].copy()
                song['rerank_score'] = result.relevance_score
                song['rerank_position'] = len(reranked_songs) + 1
                reranked_songs.append(song)

            return reranked_songs

        except Exception as e:
            print(f"Error in reranking: {e}")
            # Return original order if reranking fails
            return songs[:top_n]

    def rerank_with_explanation(self, songs: List[Dict], user_query: str,
                                user_profile_summary: str = None,
                                top_n: int = None) -> Dict:
        """
        Rerank songs and provide explanations

        Returns:
            Dict with 'songs' and 'metadata' keys
        """
        reranked_songs = self.rerank(songs, user_query, user_profile_summary, top_n)

        metadata = {
            'original_count': len(songs),
            'reranked_count': len(reranked_songs),
            'query': user_query,
            'user_profile_used': user_profile_summary is not None,
            'model': self.model
        }

        return {
            'songs': reranked_songs,
            'metadata': metadata
        }


# Convenience function
def get_reranker() -> CohereReranker:
    """Get CohereReranker instance"""
    return CohereReranker()


# Testing
if __name__ == "__main__":
    print("Testing Cohere Reranker\n" + "="*60)

    # Sample songs for testing
    sample_songs = [
        {
            'name': 'Shape of You',
            'artist': 'Ed Sheeran',
            'genre': 'pop',
            'features': {
                'energy': 0.8,
                'valence': 0.9,
                'danceability': 0.8
            },
            'lyrics_preview': 'The club isn\'t the best place to find a lover...'
        },
        {
            'name': 'Someone Like You',
            'artist': 'Adele',
            'genre': 'pop',
            'features': {
                'energy': 0.3,
                'valence': 0.2,
                'acousticness': 0.9
            },
            'lyrics_preview': 'I heard that you\'re settled down...'
        },
        {
            'name': 'Uptown Funk',
            'artist': 'Mark Ronson ft. Bruno Mars',
            'genre': 'pop',
            'features': {
                'energy': 0.9,
                'valence': 0.8,
                'danceability': 0.9
            },
            'lyrics_preview': 'This hit, that ice cold...'
        }
    ]

    reranker = CohereReranker()

    # Test 1: Happy workout music
    print("\nTest 1: Query = 'upbeat songs for working out'\n")
    result = reranker.rerank_with_explanation(
        sample_songs,
        "upbeat songs for working out"
    )

    for song in result['songs']:
        print(f"  {song['rerank_position']}. {song['name']} by {song['artist']}")
        print(f"     Rerank score: {song['rerank_score']:.3f}")

    # Test 2: Sad music with user profile
    print("\n\nTest 2: Query = 'sad songs' with user profile\n")
    result = reranker.rerank_with_explanation(
        sample_songs,
        "sad songs",
        user_profile_summary="User prefers acoustic, emotional songs with meaningful lyrics"
    )

    for song in result['songs']:
        print(f"  {song['rerank_position']}. {song['name']} by {song['artist']}")
        print(f"     Rerank score: {song['rerank_score']:.3f}")

    print(f"\n{'='*60}")
    print("Reranker test complete!")
