"""
Flask API for Music Recommendation System
Provides REST API endpoints for web interface
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict
import config
from src.recommendation_system import get_recommendation_system
from src.database.sqlite_manager import SQLiteManager
from src.evaluation.metrics import get_metrics, get_ab_testing

app = Flask(__name__)
CORS(app)

# Initialize components
rec_system = get_recommendation_system()
db = SQLiteManager()
metrics = get_metrics()
ab_testing = get_ab_testing()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'API is running'})


# ========== User Endpoints ==========

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        user_id = db.create_user(username)
        user = db.get_user(user_id=user_id)
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<username>', methods=['GET'])
def get_user(username):
    """Get user by username"""
    user = db.get_user(username=username)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user})


@app.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile with preferences"""
    try:
        profile = rec_system.get_user_profile(user_id)
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<int:user_id>/history', methods=['GET'])
def get_user_history(user_id):
    """Get user recommendation history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = rec_system.get_session_history(user_id, limit)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== Recommendation Endpoints ==========

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get music recommendations"""
    data = request.json

    user_id = data.get('user_id')
    query = data.get('query')
    session_id = data.get('session_id')
    genre_filter = data.get('genre_filter')
    enable_time_matching = data.get('enable_time_matching', True)
    enable_reranking = data.get('enable_reranking', True)

    if not user_id or not query:
        return jsonify({'error': 'user_id and query are required'}), 400

    try:
        result = rec_system.get_recommendations(
            user_id=user_id,
            query=query,
            session_id=session_id,
            genre_filter=genre_filter,
            enable_time_matching=enable_time_matching,
            enable_reranking=enable_reranking
        )

        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    """Record user feedback on a recommendation"""
    data = request.json

    user_id = data.get('user_id')
    song_id = data.get('song_id')
    rating = data.get('rating')
    action_type = data.get('action_type', 'view')
    session_id = data.get('session_id')

    if not user_id or not song_id:
        return jsonify({'error': 'user_id and song_id are required'}), 400

    try:
        rec_system.record_feedback(
            user_id=user_id,
            song_id=song_id,
            rating=rating,
            action_type=action_type,
            session_id=session_id
        )

        return jsonify({'success': True, 'message': 'Feedback recorded'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== Song Endpoints ==========

@app.route('/api/songs/<int:song_id>', methods=['GET'])
def get_song(song_id):
    """Get song details"""
    song = db.get_song(song_id=song_id)

    if not song:
        return jsonify({'error': 'Song not found'}), 404

    return jsonify({'song': song})


@app.route('/api/songs/search', methods=['GET'])
def search_songs():
    """Search songs by name or artist"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)

    # Simple search implementation (you can enhance this)
    all_songs = db.get_all_songs(limit=1000)

    # Filter by query
    results = []
    query_lower = query.lower()

    for song in all_songs:
        if (query_lower in song['name'].lower() or
            query_lower in song['artist'].lower()):
            results.append(song)

        if len(results) >= limit:
            break

    return jsonify({'songs': results, 'count': len(results)})


@app.route('/api/songs/stats', methods=['GET'])
def get_songs_stats():
    """Get database statistics"""
    total_songs = db.get_songs_count()

    return jsonify({
        'total_songs': total_songs,
        'genres': config.GENRES
    })


# ========== Evaluation Endpoints ==========

@app.route('/api/evaluation/user/<int:user_id>', methods=['POST'])
def evaluate_user_recommendations(user_id):
    """Evaluate recommendations for a user"""
    data = request.json
    recommended = data.get('recommended', [])

    try:
        evaluation = metrics.evaluate_recommendations(user_id, recommended)
        return jsonify({'success': True, 'evaluation': evaluation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluation/ab-test', methods=['POST'])
def run_ab_test():
    """Run A/B test comparing strategies"""
    data = request.json

    user_id = data.get('user_id')
    test_type = data.get('test_type', 'reranker')  # 'reranker' or 'time_matching'
    query = data.get('query')

    if not user_id or not query:
        return jsonify({'error': 'user_id and query are required'}), 400

    try:
        # Get candidates first
        from src.agents.retriever import RetrieverAgent
        retriever = RetrieverAgent()
        result = retriever.retrieve_with_expansion(query)
        candidates = result['candidates']

        # Run comparison
        if test_type == 'reranker':
            comparison = ab_testing.test_with_without_reranker(
                user_id, query, candidates
            )
        elif test_type == 'time_matching':
            comparison = ab_testing.test_with_without_time_matching(
                user_id, query, candidates
            )
        else:
            return jsonify({'error': 'Invalid test_type'}), 400

        return jsonify({'success': True, 'comparison': comparison})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ========== Data Collection Endpoints ==========

@app.route('/api/data/collect/status', methods=['GET'])
def get_collection_status():
    """Get data collection status"""
    total_songs = db.get_songs_count()

    return jsonify({
        'total_songs': total_songs,
        'target': config.TOTAL_SONGS_TARGET,
        'progress': total_songs / config.TOTAL_SONGS_TARGET * 100
    })


# ========== Error Handlers ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("Starting Flask API server...")
    print(f"Host: {config.FLASK_HOST}")
    print(f"Port: {config.FLASK_PORT}")

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
