"""
Streamlit Web Interface for Music Recommendation System
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.recommendation_system import get_recommendation_system
from src.database.qdrant_storage import QdrantStorage
from src.evaluation.metrics import get_metrics

# Page config
st.set_page_config(
    page_title="Music Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'pipeline_trace' not in st.session_state:
    st.session_state.pipeline_trace = None
if 'rated_songs' not in st.session_state:
    st.session_state.rated_songs = set()  # Track songs that have been rated to prevent duplicate recordings

# Initialize components
@st.cache_resource
def get_components():
    return {
        'system': get_recommendation_system(),
        'db': QdrantStorage(),
        'metrics': get_metrics()
    }

components = get_components()
rec_system = components['system']
db = components['db']
metrics = components['metrics']

# Helper function to get song ID
def get_song_id(song):
    """Get song ID from song dict, handling different field names"""
    return song.get('song_id', song.get('spotify_id', song.get('name', 'unknown')))

# Custom CSS
st.markdown("""
    <style>
    .song-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
    }
    .metric-card {
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        background-color: #e8f4f8;
    }
    </style>
""", unsafe_allow_html=True)


# Sidebar - User Management
with st.sidebar:
    st.title("🎵 Music Recommender")

    st.header("User Profile")

    if st.session_state.user_id is None:
        # Login/Register
        username = st.text_input("Username")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login"):
                user = db.get_user(username=username)
                if user:
                    st.session_state.user_id = user['id']
                    st.session_state.username = username
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("User not found")

        with col2:
            if st.button("Register"):
                if not username:
                    st.error("Please enter a username")
                else:
                    # Check if user already exists
                    existing_user = db.get_user(username=username)
                    if existing_user:
                        st.error("Username already exists")
                    else:
                        try:
                            user_id = db.create_user(username)
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.success(f"Welcome, {username}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating user: {str(e)}")

    else:
        st.write(f"**Logged in as:** {st.session_state.username}")

        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.recommendations = None
            st.rerun()

        # User stats
        st.divider()
        st.subheader("Your Stats")

        # Get accurate interaction count
        interaction_count = db.get_user_interaction_count(st.session_state.user_id)
        profile = rec_system.get_user_profile(st.session_state.user_id)

        # Show actual interaction count from database
        st.metric("Total Interactions", interaction_count)
        st.caption("💡 Interactions include: ratings, likes, dislikes, and plays")

        if profile.get('genre_preferences'):
            st.write("**Top Genres:**")
            top_genres = sorted(
                profile['genre_preferences'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for genre, weight in top_genres:
                st.write(f"- {genre.capitalize()}: {weight:.2f}")


# Main content
st.title("🎵 Music Recommendation System")

# Check if user is logged in
if st.session_state.user_id is None:
    st.info("👈 Please login or register to get started!")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Search & Recommendations",
    "📊 User Profile",
    "📈 Evaluation",
    "🔬 Agent Trace",
    "ℹ️ About"
])

# Tab 1: Search & Recommendations
with tab1:
    st.header("Get Music Recommendations")

    # Search form
    with st.form("search_form"):
        query = st.text_input(
            "What kind of music are you looking for?",
            placeholder="e.g., upbeat songs for working out, sad acoustic songs, chill electronic music"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            enable_time_matching = st.checkbox("Time-of-Day Matching", value=True)

        with col2:
            enable_reranking = st.checkbox("Enable Reranking", value=True)

        with col3:
            genre_filter = st.selectbox("Genre Filter (Optional)", ["None"] + [g.capitalize() for g in ["pop", "rock", "hip-hop", "electronic", "r&b"]])

        submitted = st.form_submit_button("Get Recommendations", type="primary")

    if submitted and query:
        with st.spinner("🎵 Finding the perfect songs for you..."):
            try:
                genre = None if genre_filter == "None" else genre_filter.lower()

                result = rec_system.get_recommendations(
                    user_id=st.session_state.user_id,
                    query=query,
                    session_id=st.session_state.session_id,
                    genre_filter=genre,
                    enable_time_matching=enable_time_matching,
                    enable_reranking=enable_reranking
                )

                if result['success']:
                    st.session_state.recommendations = result['recommendations']
                    st.session_state.pipeline_trace = result['pipeline_trace']
                    # Clear rated songs set for new recommendations
                    st.session_state.rated_songs = set()
                    st.success(f"Found {len(result['recommendations'])} recommendations!")

                else:
                    st.error(result.get('message', 'No results found'))

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Display recommendations
    if st.session_state.recommendations:
        st.divider()
        st.subheader("Your Recommendations")
        st.caption("💡 Click on a song to expand and play preview")

        for i, song in enumerate(st.session_state.recommendations, 1):
            # Create expander title with song info
            expander_title = f"{i}. {song['name']} - {song['artist']}"

            # Only expand first song by default
            with st.expander(expander_title, expanded=(i == 1)):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Genre:** {song.get('genre', 'Unknown').capitalize()}")

                    # Features - check both features dict and individual fields
                    features = song.get('features', {})
                    energy = features.get('energy') if features else song.get('energy', 0)
                    valence = features.get('valence') if features else song.get('valence', 0)
                    danceability = features.get('danceability') if features else song.get('danceability', 0)

                    if energy or valence or danceability:
                        feature_text = f"Energy: {energy:.2f} | "
                        feature_text += f"Valence: {valence:.2f} | "
                        feature_text += f"Danceability: {danceability:.2f}"
                        st.caption(feature_text)

                    # Spotify Preview Player - only loads when expander is opened
                    spotify_id = song.get('spotify_id')
                    if spotify_id:
                        st.components.v1.html(
                            f'''
                            <iframe style="border-radius:12px"
                                    src="https://open.spotify.com/embed/track/{spotify_id}"
                                    width="100%"
                                    height="152"
                                    frameBorder="0"
                                    allowfullscreen=""
                                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                                    loading="lazy">
                            </iframe>
                            ''',
                            height=170
                        )
                    else:
                        st.caption("🎵 Preview not available")

                with col2:
                    # Rating
                    song_key = f"{get_song_id(song)}_rate"
                    rating = st.selectbox(
                        "Rate",
                        options=[None, 1, 2, 3, 4, 5],
                        format_func=lambda x: "⭐" * x if x else "Rate",
                        key=f"rating_{i}_{get_song_id(song)}"
                    )

                    # Only record if rating is selected and hasn't been recorded yet
                    if rating and song_key not in st.session_state.rated_songs:
                        rec_system.record_feedback(
                            user_id=st.session_state.user_id,
                            song_id=get_song_id(song),
                            rating=rating,
                            action_type='rate',
                            session_id=st.session_state.session_id,
                            spotify_id=song.get('spotify_id')
                        )
                        st.session_state.rated_songs.add(song_key)
                        st.success("✓ Rated!")

                    # Actions
                    col_like, col_dislike = st.columns(2)

                    with col_like:
                        if st.button("👍", key=f"like_{i}_{get_song_id(song)}", use_container_width=True):
                            rec_system.record_feedback(
                                st.session_state.user_id,
                                get_song_id(song),
                                action_type='like',
                                session_id=st.session_state.session_id,
                                spotify_id=song.get('spotify_id')
                            )
                            st.success("✓")

                    with col_dislike:
                        if st.button("👎", key=f"dislike_{i}_{get_song_id(song)}", use_container_width=True):
                            rec_system.record_feedback(
                                st.session_state.user_id,
                                get_song_id(song),
                                action_type='dislike',
                                session_id=st.session_state.session_id,
                                spotify_id=song.get('spotify_id')
                            )
                            st.info("✓")

# Tab 2: User Profile
with tab2:
    st.header("Your Music Profile")

    profile = rec_system.get_user_profile(st.session_state.user_id)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Genre Preferences")
        if profile.get('genre_preferences'):
            genre_df = pd.DataFrame([
                {'Genre': g.capitalize(), 'Preference': v}
                for g, v in profile['genre_preferences'].items()
            ])
            fig = px.bar(genre_df, x='Genre', y='Preference', title="Your Genre Preferences")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Listen to more music to build your profile!")

    with col2:
        st.subheader("Audio Feature Preferences")
        if profile.get('audio_feature_preferences'):
            features_data = []
            for feature, stats in profile['audio_feature_preferences'].items():
                features_data.append({
                    'Feature': feature.capitalize(),
                    'Mean': stats['mean']
                })

            if features_data:
                feature_df = pd.DataFrame(features_data)
                fig = px.bar(feature_df, x='Feature', y='Mean', title="Your Audio Preferences")
                st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Favorite Artists")
        liked_artists = profile.get('liked_artists', [])
        if liked_artists:
            for artist in liked_artists[:10]:
                st.write(f"- {artist}")
        else:
            st.info("No favorite artists yet")

    with col2:
        st.subheader("Recent Activity")
        interactions = db.get_user_interactions(st.session_state.user_id, limit=10)
        if interactions:
            for interaction in interactions:
                # Handle both 'action_type' and 'interaction_type' field names
                action = interaction.get('action_type', interaction.get('interaction_type', 'unknown'))
                rating = interaction.get('rating', '')
                song_name = interaction.get('song_name', 'Unknown Song')
                st.write(f"- {song_name} ({action}{f' - {rating}⭐' if rating else ''})")
        else:
            st.info("No activity yet")

# Tab 3: Evaluation
with tab3:
    st.header("Recommendation Evaluation")

    if st.session_state.recommendations:
        # Evaluate current recommendations
        evaluation = metrics.evaluate_recommendations(
            st.session_state.user_id,
            st.session_state.recommendations
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Diversity Score", f"{evaluation['diversity_score']:.2f}")

        with col2:
            st.metric("User Satisfaction", f"{evaluation['user_satisfaction']:.2f}")

        with col3:
            st.metric("Recommendations", evaluation['num_recommendations'])

        # Precision@K
        st.subheader("Precision@K")
        precision_data = []
        for key, value in evaluation['precision_at_k'].items():
            k = key.split('@')[1]
            precision_data.append({'K': int(k), 'Precision': value})

        if precision_data:
            precision_df = pd.DataFrame(precision_data)
            fig = px.line(precision_df, x='K', y='Precision', markers=True, title="Precision@K")
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Get some recommendations first to see evaluation metrics!")

# Tab 4: Agent Trace
with tab4:
    st.header("Multi-Agent Pipeline Trace")

    if st.session_state.pipeline_trace:
        trace = st.session_state.pipeline_trace

        st.info(f"Session ID: {trace['session_id']}")
        st.write(f"**Query:** {trace['query']}")
        st.write(f"**Timestamp:** {trace['timestamp']}")

        st.divider()

        stages = trace.get('stages', {})

        # Stage 1: Retrieval
        if 'retrieval' in stages:
            with st.expander("📥 Stage 1: Retrieval", expanded=True):
                retrieval = stages['retrieval']
                st.write(f"**Agent:** {retrieval['agent']}")
                st.write(f"**Candidates Retrieved:** {retrieval['candidates_count']}")

        # Stage 2: Analysis
        if 'analysis' in stages:
            with st.expander("🔍 Stage 2: User Analysis", expanded=True):
                analysis = stages['analysis']
                st.write(f"**Agent:** {analysis['agent']}")
                st.write(f"**Profile:** {analysis['profile_summary']}")
                st.write(f"**Total Interactions:** {analysis['total_interactions']}")

        # Stage 3: Curation
        if 'curation' in stages:
            with st.expander("🎯 Stage 3: Curation", expanded=True):
                curation = stages['curation']
                st.write(f"**Agent:** {curation['agent']}")
                st.write(f"**Final Count:** {curation['final_count']}")

                metadata = curation.get('metadata', {})
                st.write(f"**Time Matching:** {'✅' if metadata.get('time_matching_enabled') else '❌'}")
                st.write(f"**Reranking:** {'✅' if metadata.get('reranking_enabled') else '❌'}")

                if metadata.get('time_period'):
                    st.write(f"**Time Period:** {metadata['time_period'].capitalize()}")

        # Stage 4: Critique
        if 'critique' in stages:
            with st.expander("✅ Stage 4: Evaluation", expanded=True):
                critique = stages['critique']
                st.write(f"**Agent:** {critique['agent']}")
                st.write(f"**Diversity Score:** {critique['diversity_score']:.2f}")
                st.write(f"**Quality Score:** {critique['quality_score']:.2f}")
                st.write(f"**Issues Found:** {critique['issues_count']}")
                st.write(f"**Feedback:** {critique['feedback']}")

    else:
        st.info("Get some recommendations first to see the pipeline trace!")

# Tab 5: About
with tab5:
    st.header("About This System")

    st.markdown("""
    ## Multi-Agent Music Recommendation System

    This system uses a sophisticated multi-agent RAG (Retrieval-Augmented Generation) architecture
    to provide personalized music recommendations.

    ### Architecture

    **Four Specialized Agents:**

    1. **RetrieverAgent** - Performs semantic search on vector database (Qdrant)
    2. **AnalyzerAgent** - Analyzes user listening history and preferences
    3. **CuratorAgent** - Curates final recommendations using scoring, time-matching, and reranking
    4. **CriticAgent** - Evaluates recommendations and provides explanations

    ### Key Features

    - **Vector Database (Qdrant):** Stores song embeddings for semantic search
    - **Cohere Reranker:** Optimizes recommendation order
    - **Time-of-Day Matching:** Adjusts recommendations based on time
    - **Memory Systems:**
      - Short-term: Current session context
      - Long-term: Persistent user profile
    - **Evaluation Metrics:** Precision@K, Diversity, Coverage, User Satisfaction

    ### Technology Stack

    - **LangChain:** Agent framework
    - **OpenAI:** Embeddings and LLM
    - **Cohere:** Reranking
    - **Qdrant:** Vector database
    - **SQLite:** User data and interactions
    - **Spotify API:** Song metadata
    - **Genius API:** Lyrics data

    ### Data

    - 7,400+ songs across 5 genres (pop, rock, hip-hop, electronic, R&B)
    - Rich metadata: audio features, lyrics, artist info
    - ~62% songs with lyrics for enhanced semantic search
    - Real-time user feedback integration

    ---

    Built for GSU Text Analytics Final Project - Fall 2025
    """)

# Run the app
if __name__ == "__main__":
    st.write("🎵 Music Recommendation System")
