"""
Evaluate Ranking Metrics

Computes Precision@k, Recall@k, and NDCG@k for the recommendation model
using the ground-truth MovieLens dataset.

Methodology (Hide-One):
1. Select users with >= 2 highly rated movies (>= 4.0).
2. For each user, pick one target movie to hide.
3. Use the remaining movies as context to generate a user profile.
4. Rank all movies based on similarity to this profile.
5. Check if the hidden target appears in the top K recommendations.

Usage:
    python ml/evaluate_ranking.py --version v1.0.0
"""

import os
import sys
import json
import argparse
import numpy as np
import pickle
import sqlite3
import random
from typing import List, Dict, Set
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = "movie_rec.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def dcg_at_k(r, k, method=0):
    r = np.asarray(r, dtype=float)[:k]
    if r.size:
        if method == 0:
            return r[0] + np.sum(r[1:] / np.log2(np.arange(2, r.size + 1)))
        elif method == 1:
            return np.sum(r / np.log2(np.arange(2, r.size + 2)))
    return 0.0

def ndcg_at_k(r, k, method=0):
    dcg_max = dcg_at_k(sorted(r, reverse=True), k, method)
    if not dcg_max:
        return 0.0
    return dcg_at_k(r, k, method) / dcg_max

class ModelEvaluator:
    def __init__(self, version="v1.0.0"):
        self.version = version
        self.artifacts_dir = f"artifacts/tfidf/{version}"
        self.tfidf_matrix = None
        self.indices = None # Maps title -> index
        self.df = None      # Dataframe with tmdb_id
        self.id_to_idx = {} # Maps tmdb_id -> matrix index

    def load_model(self):
        print(f"📦 Loading model version: {self.version}")

        if not os.path.exists(self.artifacts_dir):
            print(f"❌ Model artifacts not found at {self.artifacts_dir}")
            return False

        try:
            with open(os.path.join(self.artifacts_dir, "tfidf_matrix.pkl"), "rb") as f:
                self.tfidf_matrix = pickle.load(f)

            with open(os.path.join(self.artifacts_dir, "movies.pkl"), "rb") as f:
                self.df = pickle.load(f)
            
            # Create fast ID to Index map
            # Assuming the order in df corresponds to rows in tfidf_matrix
            for idx, row in self.df.iterrows():
                self.id_to_idx[row['tmdb_id']] = idx

            print("   ✓ Model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False

    def get_user_vector(self, movie_ids: List[int]):
        """
        Compute User Profile Vector = Mean of TF-IDF vectors of liked movies.
        """
        valid_indices = []
        for mid in movie_ids:
            if mid in self.id_to_idx:
                valid_indices.append(self.id_to_idx[mid])
        
        if not valid_indices:
            return None
            
        # Select rows and average
        vectors = self.tfidf_matrix[valid_indices]
        user_vector = vectors.mean(axis=0)
        # Convert to numpy array if matrix is sparse
        try:
           user_vector = np.array(user_vector) 
        except:
           pass
        return user_vector

    def recommend(self, user_vector, top_n=50, exclude_ids=None):
        """
        Recommend items similar to user_vector.
        """
        if user_vector is None:
            return []
            
        # Compute cosine similarity
        # user_vector is (1, features), tfidf_matrix is (num_movies, features)
        similarities = (self.tfidf_matrix @ user_vector.T)
        
        # Convert to flat array
        try:
            similarities = similarities.toarray().flatten()
        except:
            similarities = similarities.flatten()
            
        # Sort
        sorted_indices = np.argsort(-similarities)
        
        recommendations = []
        for idx in sorted_indices:
            tmdb_id = self.df.iloc[int(idx)]["tmdb_id"]
            if exclude_ids and tmdb_id in exclude_ids:
                continue
                
            recommendations.append(tmdb_id)
            if len(recommendations) >= top_n:
                break
                
        return recommendations

    def evaluate(self):
        print("🚀 Starting Offline Evaluation with MovieLens 100K...")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch relevant user histories
        # Join with mapping table to get TMDB IDs
        query = """
            SELECT 
                r.user_id, 
                m.tmdb_id, 
                r.rating 
            FROM movielens_ratings r
            JOIN movielens_tmdb_map m ON r.movielens_movie_id = m.movielens_movie_id
            WHERE r.rating >= 4.0
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        user_history = {}
        for uid, mid, rating in rows:
            if uid not in user_history:
                user_history[uid] = []
            user_history[uid].append(mid)
            
        # 2. Filter Users (< 2 movies)
        eval_users = {u: m for u, m in user_history.items() if len(m) >= 2}
        print(f"📊 Evaluated Users: {len(eval_users)} (filtered from {len(user_history)})")
        
        metrics = {
            "p@5": [], "p@10": [],
            "r@5": [], "r@10": [],
            "ndcg@5": [], "ndcg@10": []
        }
        
        print(f"🔄 Processing users...")
        count = 0 
        
        for uid, movies in eval_users.items():
            # Hide-One Strategy
            # Use deterministic seed per user for reproducibility? Or random.
            # Random is fine as long as we average enough.
            target = random.choice(movies)
            context = [m for m in movies if m != target]
            
            # Generate User Profile from Context
            user_vec = self.get_user_vector(context)
            if user_vec is None:
                continue
                
            # Get Recommendations
            # We need enough top_n to check for top 10
            preds = self.recommend(user_vec, top_n=10, exclude_ids=set(context))
            
            # Compute Metrics
            # Target is the ONLY relevant item in the "Holdout Set"
            hit_at_5 = 1 if target in preds[:5] else 0
            hit_at_10 = 1 if target in preds[:10] else 0
            
            # Precision@K: (hits / k)
            metrics["p@5"].append(hit_at_5 / 5.0)
            metrics["p@10"].append(hit_at_10 / 10.0)
            
            # Recall@K: (hits / total_relevant_in_holdout). Total relevant is 1.
            metrics["r@5"].append(hit_at_5 / 1.0)
            metrics["r@10"].append(hit_at_10 / 1.0)
            
            # NDCG@K
            # Ideal ranking: Target at rank 1.
            # Current ranking: Relevance list [0, 0, 1, 0...]
            # Construct relevance list for our preds
            rel_5 = [1 if p == target else 0 for p in preds[:5]]
            rel_10 = [1 if p == target else 0 for p in preds[:10]]
            
            metrics["ndcg@5"].append(ndcg_at_k(rel_5, 5))
            metrics["ndcg@10"].append(ndcg_at_k(rel_10, 10))
            
            count += 1
            if count % 100 == 0:
                print(f"   Processed {count} users...", end="\r")

        # Aggregate
        final_metrics = {k: float(np.mean(v)) if v else 0.0 for k, v in metrics.items()}
        
        print("\n\n📈 Evaluation Results:")
        print(f"   Precision@5: {final_metrics['p@5']:.4f}")
        print(f"   Recall@5:    {final_metrics['r@5']:.4f}")
        print(f"   NDCG@5:      {final_metrics['ndcg@5']:.4f}")
        print(f"   Precision@10:{final_metrics['p@10']:.4f}")
        print(f"   Recall@10:   {final_metrics['r@10']:.4f}")
        print(f"   NDCG@10:     {final_metrics['ndcg@10']:.4f}")

        # Save Report
        report = {
            "model_version": self.version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "num_users_evaluated": len(metrics["p@5"]),
            "metrics": final_metrics,
        }

        output_path = "outputs/evaluation_report_v1.1.0.json"
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.0.0")
    args = parser.parse_args()

    evaluator = ModelEvaluator(args.version)
    if evaluator.load_model():
        evaluator.evaluate()

if __name__ == "__main__":
    main()
