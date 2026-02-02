"""
Hybrid Recommendation Engine

Combines content-based similarity (TF-IDF) with user interaction signals
for personalized recommendations.
"""

import sqlite3
from typing import List, Dict, Tuple, Optional
import numpy as np


class HybridRecommender:
    """
    Hybrid recommendation engine that combines:
    1. Content similarity (TF-IDF cosine similarity)
    2. User interaction history (clicks, likes)
    """

    def __init__(self, database_path: str):
        self.database_path = database_path

    def get_user_preferences(self, session_id: str) -> Dict[int, float]:
        """
        Get user interaction scores for movies.

        Returns:
            Dict mapping movie_id to interaction_score
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT movie_id, interaction_score
            FROM user_interactions
            WHERE session_id = ?
            ORDER BY interaction_score DESC
        """,
            (session_id,),
        )

        preferences = {}
        for row in cursor.fetchall():
            movie_id, score = row
            preferences[movie_id] = score

        conn.close()
        return preferences

    def get_user_genre_preferences(self, session_id: str) -> Dict[str, float]:
        """
        Compute user's genre preferences based on interaction history.

        Returns:
            Dict mapping genre to preference score
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Get movies user has interacted with
        cursor.execute(
            """
            SELECT m.genres, ui.interaction_score
            FROM user_interactions ui
            JOIN movies m ON ui.movie_id = m.tmdb_id
            WHERE ui.session_id = ?
        """,
            (session_id,),
        )

        genre_scores = {}
        for row in cursor.fetchall():
            genres_json, score = row

            if not genres_json:
                continue

            try:
                import json

                genres = json.loads(genres_json)
                for genre in genres:
                    genre_scores[genre] = genre_scores.get(genre, 0.0) + score
            except:
                continue

        conn.close()

        # Normalize scores
        if genre_scores:
            max_score = max(genre_scores.values())
            if max_score > 0:
                genre_scores = {g: s / max_score for g, s in genre_scores.items()}

        return genre_scores

    def compute_genre_boost(
        self, movie_genres: List[str], user_genre_prefs: Dict[str, float]
    ) -> float:
        """
        Compute boost score based on genre overlap with user preferences.

        Args:
            movie_genres: List of genres for the recommended movie
            user_genre_prefs: User's genre preference scores

        Returns:
            Boost score (0.0 to 1.0)
        """
        if not movie_genres or not user_genre_prefs:
            return 0.0

        # Average preference score for movie's genres
        scores = [user_genre_prefs.get(genre, 0.0) for genre in movie_genres]
        return np.mean(scores) if scores else 0.0

    def hybrid_rank(
        self,
        recommendations: List[Tuple[str, float, int, List[str]]],
        session_id: Optional[str] = None,
        content_weight: float = 0.7,
        user_weight: float = 0.3,
    ) -> List[Tuple[str, float, int, List[str], Dict[str, float]]]:
        """
        Re-rank recommendations using hybrid scoring.

        Args:
            recommendations: List of (title, similarity_score, movie_id, genres)
            session_id: User session ID (optional)
            content_weight: Weight for content similarity (default: 0.7)
            user_weight: Weight for user signals (default: 0.3)

        Returns:
            List of (title, hybrid_score, movie_id, genres, score_breakdown)
        """
        if not session_id:
            # No personalization, return as-is with score breakdown
            return [
                (
                    title,
                    sim,
                    mid,
                    genres,
                    {
                        "content_score": sim,
                        "user_boost": 0.0,
                        "genre_boost": 0.0,
                        "hybrid_score": sim,
                    },
                )
                for title, sim, mid, genres in recommendations
            ]

        # Get user preferences
        user_prefs = self.get_user_preferences(session_id)
        genre_prefs = self.get_user_genre_preferences(session_id)

        if not user_prefs and not genre_prefs:
            # No user history, return as-is
            return [
                (
                    title,
                    sim,
                    mid,
                    genres,
                    {
                        "content_score": sim,
                        "user_boost": 0.0,
                        "genre_boost": 0.0,
                        "hybrid_score": sim,
                    },
                )
                for title, sim, mid, genres in recommendations
            ]

        # Compute hybrid scores
        hybrid_recs = []

        for title, similarity, movie_id, genres in recommendations:
            # User interaction boost (if user has interacted with this movie before)
            user_boost = user_prefs.get(movie_id, 0.0)

            # Genre preference boost
            genre_boost = self.compute_genre_boost(genres, genre_prefs)

            # Combined user signal
            user_signal = user_boost * 0.6 + genre_boost * 0.4

            # Hybrid score
            hybrid_score = (similarity * content_weight) + (user_signal * user_weight)

            score_breakdown = {
                "content_score": float(similarity),
                "user_boost": float(user_boost),
                "genre_boost": float(genre_boost),
                "user_signal": float(user_signal),
                "hybrid_score": float(hybrid_score),
            }

            hybrid_recs.append((title, hybrid_score, movie_id, genres, score_breakdown))

        # Sort by hybrid score
        hybrid_recs.sort(key=lambda x: x[1], reverse=True)

        return hybrid_recs

    def record_interaction(
        self, session_id: str, movie_id: int, event_type: str, increment: bool = True
    ):
        """
        Record or update user interaction.

        Args:
            session_id: User session ID
            movie_id: Movie ID
            event_type: Type of event ('click', 'like', 'dislike', 'impression')
            increment: Whether to increment counts or just update timestamp
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Event type weights
        weights = {"impression": 0.1, "click": 1.0, "like": 2.0, "dislike": -1.0}

        weight = weights.get(event_type, 0.1)

        # Check if interaction exists
        cursor.execute(
            """
            SELECT interaction_score, click_count, impression_count
            FROM user_interactions
            WHERE session_id = ? AND movie_id = ?
        """,
            (session_id, movie_id),
        )

        row = cursor.fetchone()

        if row:
            # Update existing interaction
            current_score, click_count, impression_count = row

            new_score = current_score + weight if increment else current_score
            new_click_count = click_count + (1 if event_type == "click" else 0)
            new_impression_count = impression_count + (
                1 if event_type == "impression" else 0
            )

            cursor.execute(
                """
                UPDATE user_interactions
                SET interaction_score = ?,
                    click_count = ?,
                    impression_count = ?,
                    last_interaction = CURRENT_TIMESTAMP
                WHERE session_id = ? AND movie_id = ?
            """,
                (
                    new_score,
                    new_click_count,
                    new_impression_count,
                    session_id,
                    movie_id,
                ),
            )
        else:
            # Insert new interaction
            click_count = 1 if event_type == "click" else 0
            impression_count = 1 if event_type == "impression" else 0

            cursor.execute(
                """
                INSERT INTO user_interactions (
                    session_id, movie_id, interaction_score,
                    click_count, impression_count
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (session_id, movie_id, weight, click_count, impression_count),
            )

        conn.commit()
        conn.close()
