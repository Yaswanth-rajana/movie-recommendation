import argparse
import pandas as pd
import sqlite3
import os
from cf_model import CollaborativeFilter

def train_cf_model(database_path: str, output_dir: str, n_components: int = 50):
    print(f"Connecting to database: {database_path}")
    conn = sqlite3.connect(database_path)
    
    query = "SELECT user_id, movielens_movie_id, rating FROM movielens_ratings"
    print("Fetching ratings...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df)} ratings")
    
    cf = CollaborativeFilter(n_components=n_components)
    cf.train(df)
    
    cf.save(output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Collaborative Filtering Model")
    parser.add_argument("--database", type=str, default="movie_rec.db", help="Path to SQLite database")
    parser.add_argument("--output", type=str, default="artifacts/cf/v1.0.0", help="Output directory for artifacts")
    parser.add_argument("--components", type=int, default=50, help="Number of SVD components")
    
    args = parser.parse_args()
    
    train_cf_model(args.database, args.output, args.components)
