"""
TMDB Data Ingestion Script

Fetches movie data from TMDB API and stores it in the local database.
This decouples the recommendation system from runtime TMDB API calls.

Usage:
    python data_ingestion/fetch_tmdb.py --pages 50 --database movie_rec.db
"""

import os
import sys
import argparse
import asyncio
import json
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"

if not TMDB_API_KEY:
    print("ERROR: TMDB_API_KEY not found in environment")
    sys.exit(1)


class TMDBIngestion:
    """Handles TMDB data ingestion with rate limiting and error handling."""

    def __init__(self, database_path: str):
        self.database_path = database_path
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stats = {
            "movies_fetched": 0,
            "movies_inserted": 0,
            "movies_updated": 0,
            "errors": 0,
        }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def tmdb_get(
        self, path: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make a GET request to TMDB API with error handling."""
        params["api_key"] = TMDB_API_KEY

        try:
            response = await self.client.get(f"{TMDB_BASE}{path}", params=params)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"TMDB API error {response.status_code}: {response.text[:200]}")
                self.stats["errors"] += 1
                return None

        except Exception as e:
            print(f"Request error: {type(e).__name__}: {e}")
            self.stats["errors"] += 1
            return None

    async def fetch_popular_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Fetch popular movies from TMDB."""
        data = await self.tmdb_get(
            "/movie/popular", {"language": "en-US", "page": page}
        )

        if data and "results" in data:
            return data["results"]
        return []

    async def fetch_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Fetch detailed movie information including keywords."""
        # Get basic details
        details = await self.tmdb_get(f"/movie/{movie_id}", {"language": "en-US"})

        if not details:
            return None

        # Get keywords (separate endpoint)
        keywords_data = await self.tmdb_get(f"/movie/{movie_id}/keywords", {})
        keywords = []
        if keywords_data and "keywords" in keywords_data:
            keywords = [kw["name"] for kw in keywords_data["keywords"]]

        details["keywords"] = keywords
        return details

    def init_database(self):
        """Initialize database with schema."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "database", "schema.sql"
        )

        if not os.path.exists(schema_path):
            print(f"WARNING: Schema file not found at {schema_path}")
            return

        with open(schema_path, "r") as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.database_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()

        print(f"✓ Database initialized: {self.database_path}")

    def insert_movie(self, movie: Dict[str, Any]) -> bool:
        """Insert or update a movie in the database."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        try:
            # Extract genres
            genres = [g["name"] for g in movie.get("genres", [])]
            genres_json = json.dumps(genres)

            # Extract keywords
            keywords = movie.get("keywords", [])
            keywords_json = json.dumps(keywords)

            # Check if movie exists
            cursor.execute(
                "SELECT tmdb_id FROM movies WHERE tmdb_id = ?", (movie["id"],)
            )
            exists = cursor.fetchone() is not None

            if exists:
                # Update existing movie
                cursor.execute(
                    """
                    UPDATE movies SET
                        title = ?,
                        overview = ?,
                        genres = ?,
                        keywords = ?,
                        poster_path = ?,
                        backdrop_path = ?,
                        popularity = ?,
                        vote_average = ?,
                        vote_count = ?,
                        release_date = ?,
                        runtime = ?,
                        last_updated = ?
                    WHERE tmdb_id = ?
                """,
                    (
                        movie.get("title", ""),
                        movie.get("overview", ""),
                        genres_json,
                        keywords_json,
                        movie.get("poster_path"),
                        movie.get("backdrop_path"),
                        movie.get("popularity", 0.0),
                        movie.get("vote_average", 0.0),
                        movie.get("vote_count", 0),
                        movie.get("release_date"),
                        movie.get("runtime"),
                        datetime.utcnow().isoformat(),
                        movie["id"],
                    ),
                )
                self.stats["movies_updated"] += 1
            else:
                # Insert new movie
                cursor.execute(
                    """
                    INSERT INTO movies (
                        tmdb_id, title, overview, genres, keywords,
                        poster_path, backdrop_path, popularity,
                        vote_average, vote_count, release_date, runtime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        movie["id"],
                        movie.get("title", ""),
                        movie.get("overview", ""),
                        genres_json,
                        keywords_json,
                        movie.get("poster_path"),
                        movie.get("backdrop_path"),
                        movie.get("popularity", 0.0),
                        movie.get("vote_average", 0.0),
                        movie.get("vote_count", 0),
                        movie.get("release_date"),
                        movie.get("runtime"),
                    ),
                )
                self.stats["movies_inserted"] += 1

            conn.commit()
            return True

        except Exception as e:
            print(f"Database error for movie {movie.get('id')}: {e}")
            self.stats["errors"] += 1
            return False

        finally:
            conn.close()

    async def ingest_popular_movies(
        self, num_pages: int = 50, min_vote_count: int = 100
    ):
        """
        Ingest popular movies from TMDB.

        Args:
            num_pages: Number of pages to fetch (20 movies per page)
            min_vote_count: Minimum vote count to include movie
        """
        print(f"\n🎬 Starting TMDB ingestion...")
        print(f"   Pages: {num_pages} (~{num_pages * 20} movies)")
        print(f"   Min votes: {min_vote_count}\n")

        # Initialize database
        self.init_database()

        for page in range(1, num_pages + 1):
            print(f"Fetching page {page}/{num_pages}...", end=" ")

            movies = await self.fetch_popular_movies(page)

            if not movies:
                print("❌ Failed")
                continue

            print(f"✓ Got {len(movies)} movies")

            # Filter and fetch details
            for movie in movies:
                # Skip low-quality movies
                if movie.get("vote_count", 0) < min_vote_count:
                    continue

                movie_id = movie["id"]
                self.stats["movies_fetched"] += 1

                # Fetch detailed info
                details = await self.fetch_movie_details(movie_id)

                if details:
                    self.insert_movie(details)

                # Rate limiting: 40 requests per 10 seconds
                await asyncio.sleep(0.25)

            print(
                f"   Progress: {self.stats['movies_inserted']} inserted, "
                f"{self.stats['movies_updated']} updated, "
                f"{self.stats['errors']} errors"
            )

        print(f"\n✅ Ingestion complete!")
        print(f"   Movies fetched: {self.stats['movies_fetched']}")
        print(f"   Movies inserted: {self.stats['movies_inserted']}")
        print(f"   Movies updated: {self.stats['movies_updated']}")
        print(f"   Errors: {self.stats['errors']}")


async def main():
    parser = argparse.ArgumentParser(description="Ingest TMDB movie data")
    parser.add_argument(
        "--pages", type=int, default=50, help="Number of pages to fetch"
    )
    parser.add_argument("--min-votes", type=int, default=100, help="Minimum vote count")
    parser.add_argument(
        "--database", type=str, default="movie_rec.db", help="Database path"
    )

    args = parser.parse_args()

    ingestion = TMDBIngestion(args.database)

    try:
        await ingestion.ingest_popular_movies(
            num_pages=args.pages, min_vote_count=args.min_votes
        )
    finally:
        await ingestion.close()


if __name__ == "__main__":
    asyncio.run(main())
