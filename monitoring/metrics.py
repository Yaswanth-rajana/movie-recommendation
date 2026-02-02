"""
Prometheus Metrics for Movie Recommendation System

This module provides production-grade observability metrics.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable

# ============================================
# Metrics Definitions
# ============================================

# Request Counters
recommendation_requests_total = Counter(
    "recommendation_requests_total",
    "Total number of recommendation requests",
    ["endpoint", "method"],
)

recommendation_errors_total = Counter(
    "recommendation_errors_total",
    "Total number of recommendation errors",
    ["endpoint", "error_type"],
)

cold_start_fallback_total = Counter(
    "cold_start_fallback_total",
    "Total number of cold-start fallback recommendations",
    ["fallback_type"],  # 'movie_not_found', 'no_tfidf_data', etc.
)

feedback_events_total = Counter(
    "feedback_events_total",
    "Total number of feedback events recorded",
    ["event_type"],  # 'impression', 'click', 'dislike', 'like'
)

# Latency Histograms
recommendation_latency_seconds = Histogram(
    "recommendation_latency_seconds",
    "Recommendation request latency in seconds",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

database_query_latency_seconds = Histogram(
    "database_query_latency_seconds",
    "Database query latency in seconds",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

# Gauges
active_sessions = Gauge("active_sessions", "Number of active user sessions")

movies_in_database = Gauge(
    "movies_in_database", "Total number of movies in local database"
)

model_load_timestamp = Gauge(
    "model_load_timestamp", "Timestamp when the current model was loaded"
)

# Info Metrics
model_version_info = Info(
    "model_version", "Information about the current recommendation model"
)

# ============================================
# Decorator for Automatic Metric Tracking
# ============================================


def track_request_metrics(endpoint: str):
    """
    Decorator to automatically track request metrics.

    Usage:
        @track_request_metrics("recommend_tfidf")
        async def recommend_tfidf(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Increment request counter
            recommendation_requests_total.labels(endpoint=endpoint, method="GET").inc()

            # Track latency
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # Track errors
                error_type = type(e).__name__
                recommendation_errors_total.labels(
                    endpoint=endpoint, error_type=error_type
                ).inc()
                raise
            finally:
                # Record latency
                latency = time.time() - start_time
                recommendation_latency_seconds.labels(endpoint=endpoint).observe(
                    latency
                )

        return wrapper

    return decorator


def track_database_query(query_type: str):
    """
    Decorator to track database query performance.

    Usage:
        @track_database_query("fetch_movie")
        async def get_movie_by_id(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                latency = time.time() - start_time
                database_query_latency_seconds.labels(query_type=query_type).observe(
                    latency
                )

        return wrapper

    return decorator


# ============================================
# Helper Functions
# ============================================


def record_cold_start(fallback_type: str):
    """Record a cold-start fallback event."""
    cold_start_fallback_total.labels(fallback_type=fallback_type).inc()


def record_feedback_event(event_type: str):
    """Record a user feedback event."""
    feedback_events_total.labels(event_type=event_type).inc()


def update_model_info(version: str, num_movies: int, trained_on: str):
    """Update model version information."""
    model_version_info.info(
        {"version": version, "num_movies": str(num_movies), "trained_on": trained_on}
    )
    model_load_timestamp.set(time.time())


def update_database_stats(movie_count: int):
    """Update database statistics."""
    movies_in_database.set(movie_count)
