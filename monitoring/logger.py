"""
Structured Logging for Movie Recommendation System

Provides JSON-formatted logging for production observability.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable for request ID (thread-safe)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add extra fields from record
        if hasattr(record, "event"):
            log_data["event"] = record.event

        if hasattr(record, "metadata"):
            log_data["metadata"] = record.metadata

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(
    name: str = "movie_recommender", level: int = logging.INFO
) -> logging.Logger:
    """
    Set up a logger with JSON formatting.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Global logger instance
logger = setup_logger()


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for the current context.

    Args:
        request_id: Optional request ID. If not provided, generates a new UUID.

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def clear_request_id():
    """Clear the request ID from the current context."""
    request_id_var.set(None)


def log_event(
    event: str, level: str = "INFO", metadata: Optional[Dict[str, Any]] = None, **kwargs
):
    """
    Log a structured event.

    Args:
        event: Event name (e.g., "recommendation_generated", "feedback_recorded")
        level: Log level (INFO, WARNING, ERROR)
        metadata: Additional metadata dictionary
        **kwargs: Additional key-value pairs to include in metadata
    """
    # Merge metadata and kwargs
    full_metadata = metadata or {}
    full_metadata.update(kwargs)

    # Get logger level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create log record with extra fields
    logger.log(log_level, event, extra={"event": event, "metadata": full_metadata})


# Convenience functions for common events


def log_recommendation(
    movie_title: str,
    num_recommendations: int,
    latency_ms: float,
    model_version: str,
    method: str = "tfidf",
):
    """Log a recommendation generation event."""
    log_event(
        "recommendation_generated",
        level="INFO",
        metadata={
            "movie_title": movie_title,
            "num_recommendations": num_recommendations,
            "latency_ms": latency_ms,
            "model_version": model_version,
            "method": method,
        },
    )


def log_feedback(session_id: str, movie_id: int, event_type: str):
    """Log a user feedback event."""
    log_event(
        "feedback_recorded",
        level="INFO",
        metadata={
            "session_id": session_id,
            "movie_id": movie_id,
            "event_type": event_type,
        },
    )


def log_cold_start(movie_title: str, fallback_type: str, reason: str):
    """Log a cold-start fallback event."""
    log_event(
        "cold_start_fallback",
        level="WARNING",
        metadata={
            "movie_title": movie_title,
            "fallback_type": fallback_type,
            "reason": reason,
        },
    )


def log_error(
    error_type: str, error_message: str, endpoint: Optional[str] = None, **kwargs
):
    """Log an error event."""
    log_event(
        "error_occurred",
        level="ERROR",
        metadata={
            "error_type": error_type,
            "error_message": error_message,
            "endpoint": endpoint,
            **kwargs,
        },
    )


def log_model_load(model_version: str, num_movies: int, load_time_ms: float):
    """Log model loading event."""
    log_event(
        "model_loaded",
        level="INFO",
        metadata={
            "model_version": model_version,
            "num_movies": num_movies,
            "load_time_ms": load_time_ms,
        },
    )
