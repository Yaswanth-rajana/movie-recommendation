"""
Production-Ready Movie Recommendation API

Features:
- Versioned TF-IDF model loading
- Local database for movie metadata (decoupled from TMDB runtime)
- Hybrid recommendations (content + user signals)
- Feedback loop (event tracking)
- Prometheus metrics
- Structured JSON logging
- Rate limiting
- Health checks
"""

import os
import sys
import pickle
import json
import uuid
import sqlite3
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
import httpx
import aiosqlite
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import monitoring modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monitoring.metrics import (
    track_request_metrics,
    record_cold_start,
    record_feedback_event,
    update_model_info,
    update_database_stats,
    recommendation_requests_total,
)
from monitoring.logger import (
    set_request_id,
    log_recommendation,
    log_feedback,
    log_cold_start,
    log_error,
    log_model_load,
)
from recommender.hybrid import HybridRecommender

# Load environment
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movie_rec.db")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "60")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"

if not TMDB_API_KEY:
    print("WARNING: TMDB_API_KEY not set. Cold-start fallback will fail.")

# Extract database path from URL
DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "").replace("./", "")

# ============================================
# Global State
# ============================================
df: Optional[pd.DataFrame] = None
tfidf_matrix: Any = None
indices: Dict[str, int] = {}
model_metadata: Dict[str, Any] = {}
hybrid_recommender: Optional[HybridRecommender] = None


# ============================================
# Rate Limiting
# ============================================
limiter = Limiter(key_func=get_remote_address)


# ============================================
# Lifespan Context Manager
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and initialize resources on startup."""
    global df, tfidf_matrix, indices, model_metadata, hybrid_recommender

    print(f"\n{'='*60}")
    print(f"🚀 Starting Movie Recommendation API")
    print(f"{'='*60}\n")

    # Load model artifacts
    start_time = time.time()

    try:
        artifacts_dir = f"artifacts/tfidf/{MODEL_VERSION}"

        if not os.path.exists(artifacts_dir):
            print(f"ERROR: Model version {MODEL_VERSION} not found at {artifacts_dir}")
            print(
                "Please run: python ml/train_tfidf.py --config ml/config.yaml --database movie_rec.db"
            )
            sys.exit(1)

        print(f"📦 Loading model version: {MODEL_VERSION}")

        # Load metadata
        with open(os.path.join(artifacts_dir, "metadata.json"), "r") as f:
            model_metadata = json.load(f)

        # Load TF-IDF matrix
        with open(os.path.join(artifacts_dir, "tfidf_matrix.pkl"), "rb") as f:
            tfidf_matrix = pickle.load(f)

        # Load dataframe
        with open(os.path.join(artifacts_dir, "movies.pkl"), "rb") as f:
            df = pickle.load(f)

        # Load indices
        with open(os.path.join(artifacts_dir, "indices.pkl"), "rb") as f:
            indices = pickle.load(f)

        load_time_ms = (time.time() - start_time) * 1000

        print(f"   ✓ Loaded {len(df)} movies")
        print(f"   ✓ Matrix shape: {tfidf_matrix.shape}")
        print(f"   ✓ Load time: {load_time_ms:.0f}ms\n")

        # Update metrics
        update_model_info(
            version=MODEL_VERSION,
            num_movies=len(df),
            trained_on=model_metadata.get("trained_on", "unknown"),
        )

        log_model_load(
            model_version=MODEL_VERSION, num_movies=len(df), load_time_ms=load_time_ms
        )

        # Initialize hybrid recommender
        hybrid_recommender = HybridRecommender(DATABASE_PATH)

        # Update database stats
        if os.path.exists(DATABASE_PATH):
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM movies")
            movie_count = cursor.fetchone()[0]
            conn.close()
            update_database_stats(movie_count)
            print(f"📊 Database: {movie_count} movies in local storage\n")

        print(f"✅ API ready to serve requests\n")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    yield

    # Cleanup
    print("\n🛑 Shutting down API...")


# ============================================
# FastAPI App
# ============================================
app = FastAPI(
    title="Production Movie Recommender API",
    version="2.0.0",
    description="Hybrid recommendation system with observability and feedback loops",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Middleware
# ============================================
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# ============================================
# Models
# ============================================
class MovieCard(BaseModel):
    id: int
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    popularity: Optional[float] = None


class MovieDetails(BaseModel):
    id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genres: List[str] = []
    popularity: Optional[float] = None
    vote_average: Optional[float] = None


class RecommendationItem(BaseModel):
    title: str
    id: int
    score: float
    score_breakdown: Optional[Dict[str, float]] = None
    poster_url: Optional[str] = None


class FeedbackEvent(BaseModel):
    session_id: str
    movie_id: int
    event_type: str  # 'impression', 'click', 'like', 'dislike'


class HealthResponse(BaseModel):
    status: str
    model_version: str
    num_movies: int
    database_connected: bool
    timestamp: str


# ============================================
# Database Helpers
# ============================================
async def get_movie_from_db(tmdb_id: int) -> Optional[Dict[str, Any]]:
    """Fetch movie from local database."""
    if not os.path.exists(DATABASE_PATH):
        return None

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM movies WHERE tmdb_id = ?", (tmdb_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if not row:
                return None

            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))


async def search_movies_in_db(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search movies in local database."""
    if not os.path.exists(DATABASE_PATH):
        return []

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """
            SELECT tmdb_id, title, poster_path, release_date, vote_average, popularity
            FROM movies
            WHERE title LIKE ?
            ORDER BY popularity DESC
            LIMIT ?
            """,
            (f"%{query}%", limit),
        ) as cursor:
            rows = await cursor.fetchall()

            results = []
            for row in rows:
                results.append(
                    {
                        "tmdb_id": row[0],
                        "title": row[1],
                        "poster_path": row[2],
                        "release_date": row[3],
                        "vote_average": row[4],
                        "popularity": row[5],
                    }
                )

            return results


async def get_movies_by_category(category: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch movies from local database based on category."""
    if not os.path.exists(DATABASE_PATH):
        return []

    query = ""
    order_by = ""

    if category == "trending":
        # Simulate trending by recent high popularity
        # In a real app, this would be a separate table or complex query
        query = "SELECT tmdb_id, title, poster_path, release_date, vote_average, popularity FROM movies WHERE release_date > '2023-01-01'"
        order_by = "ORDER BY popularity DESC"
    elif category == "top_rated":
        query = "SELECT tmdb_id, title, poster_path, release_date, vote_average, popularity FROM movies WHERE vote_average > 0"
        order_by = "ORDER BY vote_average DESC"
    elif category == "popular":
        query = "SELECT tmdb_id, title, poster_path, release_date, vote_average, popularity FROM movies"
        order_by = "ORDER BY popularity DESC"
    else:
        # Default to popular
        query = "SELECT tmdb_id, title, poster_path, release_date, vote_average, popularity FROM movies"
        order_by = "ORDER BY popularity DESC"

    final_sql = f"{query} {order_by} LIMIT ?"

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(final_sql, (limit,)) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                results.append(
                    {
                        "tmdb_id": row[0],
                        "title": row[1],
                        "poster_path": row[2],
                        "release_date": row[3],
                        "vote_average": row[4],
                        "popularity": row[5],
                    }
                )
            return results


def make_img_url(path: Optional[str]) -> Optional[str]:
    """Convert TMDB image path to full URL."""
    if not path:
        return None
    return f"{TMDB_IMG_500}{path}"


# ============================================
# TF-IDF Recommendation Logic
# ============================================
def tfidf_recommend(
    query_title: str, top_n: int = 10, session_id: Optional[str] = None
) -> List[RecommendationItem]:
    """
    Get TF-IDF recommendations with optional hybrid ranking.
    """
    global df, tfidf_matrix, indices, hybrid_recommender

    if df is None or tfidf_matrix is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    # Normalize title
    title_lower = query_title.strip().lower()

    if title_lower not in indices:
        raise HTTPException(
            status_code=404, detail=f"Movie not found in dataset: '{query_title}'"
        )

    idx = indices[title_lower]

    # Compute similarities
    vec = tfidf_matrix[idx]
    similarities = (tfidf_matrix @ vec.T).toarray().flatten()

    # Get top N (excluding self)
    similar_indices = np.argsort(-similarities)

    # Collect recommendations with movie IDs and genres
    recs_with_metadata = []
    for i in similar_indices:
        if int(i) == int(idx):
            continue

        movie_title = df.iloc[int(i)]["title"]
        tmdb_id = int(df.iloc[int(i)]["tmdb_id"])
        similarity = float(similarities[int(i)])

        # Get genres from database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT genres FROM movies WHERE tmdb_id = ?", (tmdb_id,))
        row = cursor.fetchone()
        conn.close()

        genres = []
        if row and row[0]:
            try:
                genres = json.loads(row[0])
            except:
                pass

        recs_with_metadata.append((movie_title, similarity, tmdb_id, genres))

        if len(recs_with_metadata) >= top_n * 2:  # Get extra for hybrid ranking
            break

    # Apply hybrid ranking if session provided
    if session_id and hybrid_recommender:
        ranked = hybrid_recommender.hybrid_rank(
            recs_with_metadata[: top_n * 2], session_id=session_id
        )
        # Take top N after hybrid ranking
        final_recs = ranked[:top_n]
    else:
        # No hybrid ranking
        final_recs = [
            (title, sim, mid, genres, {"content_score": sim, "hybrid_score": sim})
            for title, sim, mid, genres in recs_with_metadata[:top_n]
        ]

    # Convert to response models
    recommendations = []
    for title, score, tmdb_id, genres, breakdown in final_recs:
        # Get poster from database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT poster_path FROM movies WHERE tmdb_id = ?", (tmdb_id,))
        row = cursor.fetchone()
        conn.close()

        poster_url = make_img_url(row[0]) if row and row[0] else None

        recommendations.append(
            RecommendationItem(
                title=title,
                id=tmdb_id,
                score=score,
                score_breakdown=breakdown,
                poster_url=poster_url,
            )
        )

    return recommendations


# ============================================
# Routes
# ============================================
@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check with model and database status."""
    db_connected = os.path.exists(DATABASE_PATH)

    return HealthResponse(
        status="healthy",
        model_version=MODEL_VERSION,
        num_movies=len(df) if df is not None else 0,
        database_connected=db_connected,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/events")
@limiter.limit(f"{RATE_LIMIT}/minute")
async def record_event(request: Request, event: FeedbackEvent):
    """Record user feedback event."""
    try:
        # Store in database
        event_id = str(uuid.uuid4())

        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                """
                INSERT INTO recommendation_events (id, session_id, movie_id, event_type)
                VALUES (?, ?, ?, ?)
            """,
                (event_id, event.session_id, event.movie_id, event.event_type),
            )
            await db.commit()

        # Update user interactions
        if hybrid_recommender:
            hybrid_recommender.record_interaction(
                event.session_id, event.movie_id, event.event_type
            )

        # Update metrics
        record_feedback_event(event.event_type)
        log_feedback(event.session_id, event.movie_id, event.event_type)

        return {"status": "recorded", "event_id": event_id}

    except Exception as e:
        log_error("feedback_error", str(e), endpoint="/events")
        raise HTTPException(status_code=500, detail=f"Failed to record event: {e}")


@app.get("/recommend/tfidf", response_model=List[RecommendationItem])
@limiter.limit(f"{RATE_LIMIT}/minute")
@track_request_metrics("recommend_tfidf")
async def recommend_tfidf(
    request: Request,
    title: str = Query(..., min_length=1),
    top_n: int = Query(10, ge=1, le=50),
    session_id: Optional[str] = None,
):
    """Get TF-IDF recommendations with optional personalization."""
    start_time = time.time()

    try:
        recommendations = tfidf_recommend(title, top_n, session_id)

        latency_ms = (time.time() - start_time) * 1000
        log_recommendation(
            movie_title=title,
            num_recommendations=len(recommendations),
            latency_ms=latency_ms,
            model_version=MODEL_VERSION,
            method="hybrid" if session_id else "tfidf",
        )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "recommendation_error", str(e), endpoint="/recommend/tfidf", title=title
        )
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}")


@app.get("/movie/{tmdb_id}", response_model=MovieDetails)
async def get_movie_details(tmdb_id: int):
    """Get movie details from local database."""
    movie = await get_movie_from_db(tmdb_id)

    if not movie:
        record_cold_start("movie_not_in_db")
        log_cold_start(
            movie_title=f"TMDB ID {tmdb_id}",
            fallback_type="movie_not_in_db",
            reason="Movie not found in local database",
        )
        raise HTTPException(status_code=404, detail="Movie not found in local database")

    # Parse genres
    genres = []
    if movie.get("genres"):
        try:
            genres = json.loads(movie["genres"])
        except:
            pass

    return MovieDetails(
        id=movie["tmdb_id"],
        title=movie["title"],
        overview=movie.get("overview"),
        release_date=movie.get("release_date"),
        poster_url=make_img_url(movie.get("poster_path")),
        backdrop_url=make_img_url(movie.get("backdrop_path")),
        genres=genres,
        popularity=movie.get("popularity"),
        vote_average=movie.get("vote_average"),
    )


@app.get("/search", response_model=List[MovieCard])
async def search_movies(
    query: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50)
):
    """Search movies in local database."""
    movies = await search_movies_in_db(query, limit)

    return [
        MovieCard(
            id=m["tmdb_id"],
            title=m["title"],
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
            popularity=m.get("popularity"),
        )
        for m in movies
    ]


@app.get("/home", response_model=List[MovieCard])
async def home(
    category: str = Query("popular"),
    limit: int = Query(24, ge=1, le=50),
):
    """
    Home feed for Frontend.
    category:
      - trending
      - popular
      - top_rated
    """
    movies = await get_movies_by_category(category, limit)
    
    return [
        MovieCard(
            id=m["tmdb_id"],
            title=m["title"],
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
            popularity=m.get("popularity"),
        )
        for m in movies
    ]


@app.get("/models")
async def list_models():
    """List available model versions."""
    artifacts_dir = "artifacts/tfidf"

    if not os.path.exists(artifacts_dir):
        return {"models": []}

    versions = []
    for version_dir in os.listdir(artifacts_dir):
        metadata_path = os.path.join(artifacts_dir, version_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                versions.append(
                    {
                        "version": version_dir,
                        "is_active": version_dir == MODEL_VERSION,
                        "trained_on": metadata.get("trained_on"),
                        "num_movies": metadata.get("num_movies"),
                    }
                )

    return {"models": versions, "active_version": MODEL_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
