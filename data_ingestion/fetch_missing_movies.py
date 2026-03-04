import os
import sys
import asyncio
import json
import sqlite3
import re
import httpx
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"
DB_PATH = "movie_rec.db"
ML_DATA_DIR = "data/movielens-100k"

if not TMDB_API_KEY:
    print("ERROR: TMDB_API_KEY not found")
    sys.exit(1)

class MovieLensBackfiller:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stats = {"searched": 0, "found": 0, "inserted": 0, "errors": 0}

    async def close(self):
        await self.client.aclose()

    async def tmdb_get(self, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        params["api_key"] = TMDB_API_KEY
        try:
            response = await self.client.get(f"{TMDB_BASE}{path}", params=params)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print("⚠️ Rate limited, sleeping...")
                await asyncio.sleep(5)
                return await self.tmdb_get(path, params)
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    async def search_movie(self, title: str, year: int = None):
        params = {"query": title, "language": "en-US", "include_adult": "false"}
        if year:
            params["year"] = year
        
        data = await self.tmdb_get("/search/movie", params)
        if data and data.get("results"):
            return data["results"][0]  # Return top match
        return None

    async def fetch_details(self, movie_id: int):
        return await self.tmdb_get(f"/movie/{movie_id}", {"language": "en-US"})

    def get_unmapped_movies(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Get already mapped
        cur.execute("SELECT movielens_movie_id FROM movielens_tmdb_map")
        mapped_ids = {r[0] for r in cur.fetchall()}
        conn.close()

        # Read u.item
        todos = []
        with open(os.path.join(ML_DATA_DIR, "u.item"), "r", encoding="ISO-8859-1") as f:
            for line in f:
                parts = line.split("|")
                if len(parts) < 2: continue
                
                mid = int(parts[0])
                if mid in mapped_ids:
                    continue
                    
                raw_title = parts[1]
                # Extract year
                match = re.search(r'\((\d{4})\)$', raw_title.strip())
                year = int(match.group(1)) if match else None
                clean_title = raw_title.replace(f"({year})", "").strip() if year else raw_title
                
                todos.append((mid, clean_title, year))
        
        return todos

    def insert_movie(self, movie: Dict[str, Any]):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            genres_json = json.dumps([g["name"] for g in movie.get("genres", [])])
            
            cursor.execute("""
                INSERT OR IGNORE INTO movies (
                    tmdb_id, title, overview, genres, 
                    poster_path, popularity, vote_average, vote_count, 
                    release_date, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                movie["id"], movie.get("title", ""), movie.get("overview", ""), genres_json,
                movie.get("poster_path"), movie.get("popularity", 0), 
                movie.get("vote_average", 0), movie.get("vote_count", 0),
                movie.get("release_date"), datetime.utcnow().isoformat()
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Error: {e}")
            return False
        finally:
            conn.close()

    def update_map(self, ml_id: int, tmdb_id: int):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT OR REPLACE INTO movielens_tmdb_map (movielens_movie_id, tmdb_id, match_method)
            VALUES (?, ?, 'tmdb_search')
        """, (ml_id, tmdb_id))
        conn.commit()
        conn.close()

    async def run(self):
        todos = self.get_unmapped_movies()
        print(f"🔍 Found {len(todos)} unmapped MovieLens movies.")
        
        for i, (ml_id, title, year) in enumerate(todos):
            result = await self.search_movie(title, year)
            
            # Fallback without year if not found
            if not result:
                 result = await self.search_movie(title)

            if result:
                tmdb_id = result["id"]
                details = await self.fetch_details(tmdb_id)
                
                if details:
                    self.insert_movie(details)
                    self.update_map(ml_id, tmdb_id)
                    self.stats["found"] += 1
                    print(f"✅ [{i+1}/{len(todos)}] Mapped: {title} ({year}) -> {details['title']}")
                else:
                    print(f"⚠️ [{i+1}/{len(todos)}] Found but failed details: {title}")
            else:
                print(f"❌ [{i+1}/{len(todos)}] Not found: {title}")
                
            self.stats["searched"] += 1
            await asyncio.sleep(0.25) # Rate limit
            
        print("\n🏁 Backfill Complete.")
        print(f"Matched: {self.stats['found']}/{len(todos)}")

if __name__ == "__main__":
    backfiller = MovieLensBackfiller()
    asyncio.run(backfiller.run())
