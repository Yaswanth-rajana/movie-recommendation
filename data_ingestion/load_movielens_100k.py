import sqlite3
import os
import re

# Paths
DB_PATH = "movie_rec.db"
ML_DATA_DIR = "data/movielens-100k"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def ingest_ratings():
    print("🚀 Ingesting MovieLens ratings...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    ratings_file = os.path.join(ML_DATA_DIR, "u.data")
    if not os.path.exists(ratings_file):
        print(f"❌ File not found: {ratings_file}")
        return

    count = 0
    with open(ratings_file, "r", encoding="ISO-8859-1") as f:
        # Batch insert for speed
        batch = []
        for line in f:
            # u.data: user id | item id | rating | timestamp
            parts = line.strip().split("\t")
            if len(parts) == 4:
                batch.append((int(parts[0]), int(parts[1]), float(parts[2]), int(parts[3])))
            
            if len(batch) >= 5000:
                cur.executemany("""
                    INSERT OR IGNORE INTO movielens_ratings
                    (user_id, movielens_movie_id, rating, timestamp)
                    VALUES (?, ?, ?, ?)
                """, batch)
                count += len(batch)
                batch = []
        
        if batch:
            cur.executemany("""
                INSERT OR IGNORE INTO movielens_ratings
                (user_id, movielens_movie_id, rating, timestamp)
                VALUES (?, ?, ?, ?)
            """, batch)
            count += len(batch)

    conn.commit()
    conn.close()
    print(f"✅ Ingested {count} ratings.")

def normalize_title(title):
    # Remove 'The ', convert to lower, remove punctuation
    if not title:
        return ""
    t = title.lower()
    if t.startswith("the "):
        t = t[4:]
    t = re.sub(r'[^\w\s]', '', t)
    return t.strip()

def extract_year(title_str):
    # Extract year (YYYY) from end of string
    match = re.search(r'\((\d{4})\)$', title_str.strip())
    if match:
        year = int(match.group(1))
        # Remove year from title
        clean_title = title_str.replace(f"({year})", "").strip()
        return clean_title, year
    return title_str, None

def map_movies():
    print("🚀 Mapping MovieLens movies to TMDB...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Load all local movies
    cur.execute("SELECT tmdb_id, title, release_date FROM movies")
    local_movies = cur.fetchall()
    
    # Pre-process local movies
    # Map: (normalized_title, year) -> list of tmdb_ids (handle duplicates)
    # Map: (normalized_title) -> list of tmdb_ids
    map_title_year = {}
    map_title_only = {}
    
    for mid, title, rdate in local_movies:
        norm_title = normalize_title(title)
        year = None
        if rdate and len(rdate) >= 4:
            try:
                year = int(rdate[:4])
            except:
                pass
        
        if year:
            key = (norm_title, year)
            if key not in map_title_year:
                map_title_year[key] = []
            map_title_year[key].append(mid)
            
        if norm_title not in map_title_only:
            map_title_only[norm_title] = []
        map_title_only[norm_title].append(mid)
        
    # Read u.item
    items_file = os.path.join(ML_DATA_DIR, "u.item")
    if not os.path.exists(items_file):
        print(f"❌ File not found: {items_file}")
        return

    mappings = []
    mapped_count = 0
    total_count = 0
    
    with open(items_file, "r", encoding="ISO-8859-1") as f:
        for line in f:
            parts = line.split("|")
            if len(parts) < 2:
                continue
                
            ml_id = int(parts[0])
            raw_title = parts[1]
            total_count += 1
            
            clean_title, ml_year = extract_year(raw_title)
            norm_title = normalize_title(clean_title)
            
            tmdb_id = None
            method = None
            
            # Strategy 1: Title + Year
            if ml_year:
                candidates = map_title_year.get((norm_title, ml_year))
                if candidates:
                    tmdb_id = candidates[0] # Pick first match
                    method = 'title_year'
            
            # Strategy 2: Title Only (Fallback)
            if not tmdb_id:
                candidates = map_title_only.get(norm_title)
                if candidates:
                    tmdb_id = candidates[0]
                    method = 'title_only'
            
            if tmdb_id:
                mappings.append((ml_id, tmdb_id, method))
                mapped_count += 1
    
    # Save mappings
    cur.executemany("""
        INSERT OR REPLACE INTO movielens_tmdb_map
        (movielens_movie_id, tmdb_id, match_method)
        VALUES (?, ?, ?)
    """, mappings)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Mapped {mapped_count}/{total_count} movies ({(mapped_count/total_count)*100:.1f}%)")

def main():
    if not os.path.exists("data/movielens-100k"):
        print("❌ MovieLens data not found. Please download it first.")
        return

    ingest_ratings()
    map_movies()

if __name__ == "__main__":
    main()
