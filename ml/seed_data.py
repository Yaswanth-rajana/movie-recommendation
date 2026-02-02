"""
Seed Database with Synthetic Data for Testing

1. Creates movie_rec.db if missing.
2. Populates 'movies' table using data from artifacts/movies.pkl (to match model).
3. Populates 'recommendation_events' with synthetic user sessions (cliques of related movies).

This allows ml/build_eval_dataset.py and ml/evaluate_ranking.py to run meaningfully.
"""

import sqlite3
import pandas as pd
import numpy as np
import pickle
import os
import uuid
import random
from datetime import datetime, timedelta

DATABASE_PATH = "movie_rec.db"
ARTIFACTS_PATH = "artifacts/tfidf/v1.0.0/movies.pkl"


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Clean up (Force schema update)
    cursor.execute("DROP TABLE IF EXISTS recommendation_events")
    cursor.execute("DROP TABLE IF EXISTS movies")
    cursor.execute("DROP TABLE IF EXISTS user_interactions")
    
    # Load schema from file
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "database",
        "schema.sql"
    )
    
    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        print(f"   ✓ Initialized schema from {schema_path}")
    else:
        # Fallback to limited schema if file not found (should not happen)
        print("⚠️ Schema file not found, using fallback schema")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                tmdb_id INTEGER PRIMARY KEY,
                title TEXT,
                overview TEXT,
                genres TEXT,
                popularity REAL,
                vote_average REAL,
                release_date TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendation_events (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                movie_id INTEGER,
                event_type TEXT,
                timestamp TEXT,
                metadata TEXT
            )
        """)

    # Clean up
    cursor.execute("DELETE FROM recommendation_events")
    cursor.execute("DELETE FROM movies")

    conn.commit()
    return conn


def seed_data():
    if not os.path.exists(ARTIFACTS_PATH):
        print(f"❌ Artifacts not found at {ARTIFACTS_PATH}")
        return

    print("🌱 Seeding database...")
    conn = init_db()

    # 1. Load Movies from Artifacts
    with open(ARTIFACTS_PATH, "rb") as f:
        df = pickle.load(f)

    print(f"   Loaded {len(df)} movies from artifacts")
    
    # Ensure necessary columns exist and have valid values for testing
    if 'vote_count' not in df.columns:
        df['vote_count'] = 500  # Default high votes
    else:
        df['vote_count'] = df['vote_count'].fillna(500)
        
    if 'overview' not in df.columns:
        df['overview'] = "Synthetic overview for testing purposes."
    else:
        df['overview'] = df['overview'].fillna("Synthetic overview.")

    # Insert movies to DB
    df.to_sql("movies", conn, if_exists="append", index=False)
    print("   ✓ Populated movies table")

    # 2. Generate Synthetic Sessions
    # Create "Interest Groups" to ensure we have ground truth correlations
    # e.g., Group A likes indexes 0, 1, 2, 3, 4

    all_ids = df["tmdb_id"].tolist()

    sessions_to_generate = 50
    events = []

    print(f"   Generating {sessions_to_generate} synthetic sessions...")

    for i in range(sessions_to_generate):
        session_id = str(uuid.uuid4())

        # Pick a random "cluster" of 5-10 movies
        cluster_start = random.randint(0, len(all_ids) - 15)
        cluster_ids = all_ids[cluster_start : cluster_start + 10]

        # User interacts with 3-6 of them (Relevant)
        num_relevant = random.randint(3, 6)
        relevant_ids = random.sample(cluster_ids, num_relevant)

        # Others are just candidates/impressions
        other_ids = set(cluster_ids) - set(relevant_ids)

        base_time = datetime.utcnow()

        # Add Likes/Clicks
        for mid in relevant_ids:
            event_type = random.choice(["click", "like", "like"])  # Bias towards like
            events.append(
                (str(uuid.uuid4()), session_id, mid, event_type, base_time.isoformat())
            )
            base_time += timedelta(seconds=15)

        # Add Impressions (some shown but not clicked)
        for mid in other_ids:
            events.append(
                (
                    str(uuid.uuid4()),
                    session_id,
                    mid,
                    "impression",
                    base_time.isoformat(),
                )
            )

    # Insert events
    conn.executemany(
        """
        INSERT INTO recommendation_events (id, session_id, movie_id, event_type, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """,
        events,
    )

    conn.commit()
    conn.close()

    print(f"   ✓ Inserted {len(events)} interactions")
    print("✅ Database seeded successfully")


if __name__ == "__main__":
    seed_data()
