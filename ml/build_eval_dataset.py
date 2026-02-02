"""
Build Evaluation Dataset

Connects to the local SQLite database and constructs a ground-truth dataset
for offline evaluation of the recommendation model.

Logic:
1. Connect to movie_rec.db
2. Query recommendation_events
3. Group by session_id
4. Define relevance: like=2 (strong), click=1 (weak), dislike=0
5. Filter sessions with < 2 relevant items (need at least one query and one target)
6. Output to outputs/eval_dataset.json
"""

import sqlite3
import json
import os
import sys
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_PATH = "movie_rec.db"
OUTPUT_DIR = "outputs"
OUTPUT_FILE = "eval_dataset.json"


def build_dataset():
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at {DATABASE_PATH}")
        return

    print(f"📊 Connecting to {DATABASE_PATH}...")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Query all events
    # We prioritize 'like' > 'click' > 'impression'
    # Event types: 'click', 'like', 'dislike', 'impression'
    try:
        cursor.execute(
            """
            SELECT session_id, movie_id, event_type 
            FROM recommendation_events 
            ORDER BY timestamp ASC
        """
        )
        events = cursor.fetchall()
    except sqlite3.OperationalError:
        print(
            "⚠️  Table 'recommendation_events' not found. Checking 'user_interactions'..."
        )
        # Fallback to user_interactions if events not available (aggregated view)
        try:
            cursor.execute(
                """
                SELECT session_id, movie_id, interaction_score, click_count, impression_count
                FROM user_interactions
            """
            )
            # Synthesize events from aggregated stats
            events = []
            for row in cursor.fetchall():
                sid, mid, score, clicks, imps = row
                # heuristics to reconstruction
                if score >= 2.0:
                    events.append((sid, mid, "like"))
                elif clicks > 0:
                    events.append((sid, mid, "click"))
                elif imps > 0:
                    events.append((sid, mid, "impression"))
        except Exception as e:
            print(f"❌ Failed to query interactions: {e}")
            return

    conn.close()

    print(f"   Fetched {len(events)} raw events")

    # Group by session
    sessions = defaultdict(lambda: {"relevant": {}, "candidates": set()})

    # Relevance mapping
    # like = 2 (strong)
    # click = 1 (weak)
    # dislike = 0 (irrelevant - strictly)
    # impression = 0 (candidate but not necessarily relevant)

    relevance_map = {"like": 2, "click": 1, "dislike": 0, "impression": 0}

    for session_id, movie_id, event_type in events:
        score = relevance_map.get(event_type, 0)

        # Track candidates (everything shown or interacted with is a candidate space for that session)
        # Note: strictly 'impression' defines what was shown, but we include clicked items too
        sessions[session_id]["candidates"].add(movie_id)

        # Update relevance if higher
        current_score = sessions[session_id]["relevant"].get(movie_id, 0)
        if score > current_score:
            sessions[session_id]["relevant"][movie_id] = score

    # Filter and Format
    final_dataset = {}

    for session_id, data in sessions.items():
        # Filter 0 relevance items from 'relevant' dict
        relevant_items = {
            mid: score for mid, score in data["relevant"].items() if score > 0
        }

        # Check sufficient data: need at least 2 relevant items (1 to query, 1 to rank)
        # Or at least 1 relevant item if we just want to test if it recommends meaningful things?
        # User requirement: "Skip sessions with < 2 relevant items"
        if len(relevant_items) < 2:
            continue

        final_dataset[session_id] = {
            "relevant_items": relevant_items,
            "candidate_items": list(data["candidates"]),
        }

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    with open(output_path, "w") as f:
        json.dump(final_dataset, f, indent=2)

    print(f"✅ Dataset built with {len(final_dataset)} valid sessions")
    print(f"   Saved to {output_path}")

    if len(final_dataset) == 0:
        print(
            "⚠️  Warning: Dataset is empty. Not enough interaction data for offline evaluation."
        )
        print("   (Need sessions with >= 2 clicks/likes)")


if __name__ == "__main__":
    build_dataset()
