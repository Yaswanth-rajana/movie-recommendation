-- Database Schema for Production-Ready Movie Recommendation System

-- ============================================
-- Table: movies (Local Movie Metadata)
-- Purpose: Store TMDB movie data locally to decouple from runtime API calls
-- ============================================
CREATE TABLE IF NOT EXISTS movies (
    tmdb_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    overview TEXT,
    genres TEXT,  -- JSON array: ["Action", "Thriller"]
    keywords TEXT,  -- JSON array for future use
    poster_path TEXT,
    backdrop_path TEXT,
    popularity REAL DEFAULT 0.0,
    vote_average REAL DEFAULT 0.0,
    vote_count INTEGER DEFAULT 0,
    release_date TEXT,
    runtime INTEGER,  -- in minutes
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title);
CREATE INDEX IF NOT EXISTS idx_movies_popularity ON movies(popularity DESC);
CREATE INDEX IF NOT EXISTS idx_movies_release_date ON movies(release_date DESC);

-- ============================================
-- Table: recommendation_events (Feedback Loop)
-- Purpose: Track user interactions for learning and personalization
-- ============================================
CREATE TABLE IF NOT EXISTS recommendation_events (
    id TEXT PRIMARY KEY,  -- UUID
    session_id TEXT NOT NULL,
    movie_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('impression', 'click', 'dislike', 'like')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON: {"source": "tfidf", "rank": 3, "score": 0.85}
    FOREIGN KEY (movie_id) REFERENCES movies(tmdb_id)
);

CREATE INDEX IF NOT EXISTS idx_events_session ON recommendation_events(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_movie ON recommendation_events(movie_id, event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON recommendation_events(timestamp DESC);

-- ============================================
-- Table: user_interactions (Aggregated User Preferences)
-- Purpose: Store aggregated user interaction scores for hybrid ranking
-- ============================================
CREATE TABLE IF NOT EXISTS user_interactions (
    session_id TEXT NOT NULL,
    movie_id INTEGER NOT NULL,
    interaction_score REAL DEFAULT 1.0,  -- Weighted score based on event types
    click_count INTEGER DEFAULT 0,
    impression_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, movie_id),
    FOREIGN KEY (movie_id) REFERENCES movies(tmdb_id)
);

CREATE INDEX IF NOT EXISTS idx_interactions_session ON user_interactions(session_id, interaction_score DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_score ON user_interactions(interaction_score DESC);

-- ============================================
-- Table: model_versions (Model Registry)
-- Purpose: Track deployed models and their metadata
-- ============================================
CREATE TABLE IF NOT EXISTS model_versions (
    version TEXT PRIMARY KEY,
    trained_on TIMESTAMP NOT NULL,
    num_movies INTEGER NOT NULL,
    config TEXT,  -- JSON: TF-IDF config, features used, etc.
    metrics TEXT,  -- JSON: avg_similarity, sparsity, etc.
    artifact_path TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 0,
    deployed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_active ON model_versions(is_active, version);

-- ============================================
-- Table: api_metrics (Request Tracking)
-- Purpose: Store API request metrics for analysis
-- ============================================
CREATE TABLE IF NOT EXISTS api_metrics (
    id TEXT PRIMARY KEY,  -- UUID
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    model_version TEXT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_metrics_endpoint ON api_metrics(endpoint, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON api_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_status ON api_metrics(status_code, timestamp DESC);
