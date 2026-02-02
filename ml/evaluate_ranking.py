"""
Evaluate Ranking Metrics

Computes Precision@k, Recall@k, and NDCG@k for the recommendation model
using the ground-truth dataset built from user interactions.

Metrics:
- Precision@k: Proportion of recommended items that are relevant
- Recall@k: Proportion of relevant items found in top k
- NDCG@k: Normalized Discounted Cumulative Gain (ranking quality)

Usage:
    python ml/evaluate_ranking.py --version v1.0.0
"""

import os
import sys
import json
import argparse
import numpy as np
import pickle
import time
from typing import List, Dict, Set
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        self.indices = None
        self.df = None

    def load_model(self):
        print(f"📦 Loading model version: {self.version}")

        if not os.path.exists(self.artifacts_dir):
            print(f"❌ Model artifacts not found at {self.artifacts_dir}")
            return False

        try:
            with open(os.path.join(self.artifacts_dir, "tfidf_matrix.pkl"), "rb") as f:
                self.tfidf_matrix = pickle.load(f)

            with open(os.path.join(self.artifacts_dir, "indices.pkl"), "rb") as f:
                self.indices = pickle.load(f)

            # Load metadata to get count
            with open(os.path.join(self.artifacts_dir, "metadata.json"), "r") as f:
                self.metadata = json.load(f)

            print("   ✓ Model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False

    def get_recommendations(self, query_id: int, top_n: int = 10) -> List[int]:
        """
        Get similar movie IDs for a given movie ID using TF-IDF matrix.
        Returns list of TMDB IDs.
        """
        # Find index for this movie ID
        # indices maps lower(title) -> index
        # We need mapping from ID -> index.
        # But wait, indices.pkl maps TITLE to index.
        # We handle this by loading df to map ID to Title?
        # Actually proper way: we need ID->Index map.

        # In current system, we have to iterate or load the reverse map.
        # For efficiency in this script, let's build ID->Index map from movies.pkl if possible
        # Or Just load movies.pkl which has 'tmdb_id' column, and align with matrix index.

        if self.df is None:
            with open(os.path.join(self.artifacts_dir, "movies.pkl"), "rb") as f:
                self.df = pickle.load(f)

        # Get index by ID
        try:
            # Assuming df index corresponds to matrix row index (which it should)
            idx = self.df.index[self.df["tmdb_id"] == query_id].tolist()
            if not idx:
                return []
            idx = idx[0]

            # Compute similarity
            vec = self.tfidf_matrix[idx]
            similarities = (self.tfidf_matrix @ vec.T).toarray().flatten()

            # Top N
            similar_indices = np.argsort(-similarities)

            recommendations = []
            for i in similar_indices:
                if i == idx:
                    continue
                recommendations.append(int(self.df.iloc[int(i)]["tmdb_id"]))
                if len(recommendations) >= top_n:
                    break

            return recommendations

        except Exception:
            return []

    def evaluate(self, dataset_path="outputs/eval_dataset.json"):
        if not os.path.exists(dataset_path):
            print(f"❌ Dataset not found at {dataset_path}")
            return

        with open(dataset_path, "r") as f:
            dataset = json.load(f)

        print(f"📊 Evaluating on {len(dataset)} sessions...")

        metrics = {
            "p@5": [],
            "p@10": [],
            "r@5": [],
            "r@10": [],
            "ndcg@5": [],
            "ndcg@10": [],
        }

        # Item-to-item evaluation strategy:
        # For each session:
        #   Take relevant items (score > 0)
        #   Leave-one-out?
        #   Or: For each known relevant item A, predict similar items.
        #   Check if other relevant items B, C appear in predictions.

        for session_id, data in dataset.items():
            relevant_items = data["relevant_items"]  # dict {id: score}
            relevant_ids = [int(mid) for mid in relevant_items.keys()]

            # For each relevant item, try to find others
            for query_id in relevant_ids:
                # Ground truth for this query: all OTHER relevant items in the session
                truth_ids = set(relevant_ids) - {query_id}
                if not truth_ids:
                    continue

                # Get Recs
                preds = self.get_recommendations(query_id, top_n=10)

                # Compute Metrics
                # Hit = pred in truth_ids
                # Relevance score for NDCG: use the user's score for that item?

                hits_at_5 = [1 if pid in truth_ids else 0 for pid in preds[:5]]
                hits_at_10 = [1 if pid in truth_ids else 0 for pid in preds[:10]]

                # Precision
                metrics["p@5"].append(sum(hits_at_5) / 5)
                metrics["p@10"].append(sum(hits_at_10) / 10)

                # Recall
                metrics["r@5"].append(sum(hits_at_5) / len(truth_ids))
                metrics["r@10"].append(sum(hits_at_10) / len(truth_ids))

                # NDCG
                # Ideal DCG: sorted truth scores (max possible)
                # Here binary relevance for hit vs miss in truth set?
                # Or use the stored relevance score?
                # Let's use simple binary relevance for hit (1) or miss (0) for now
                # as item-item similarity is a proxy.

                metrics["ndcg@5"].append(ndcg_at_k(hits_at_5, 5))
                metrics["ndcg@10"].append(ndcg_at_k(hits_at_10, 10))

        # Aggregate
        final_metrics = {k: float(np.mean(v)) if v else 0.0 for k, v in metrics.items()}

        print("\n📈 Evaluation Results:")
        print(f"   Precision@5: {final_metrics['p@5']:.4f}")
        print(f"   Recall@5:    {final_metrics['r@5']:.4f}")
        print(f"   NDCG@5:      {final_metrics['ndcg@5']:.4f}")

        # Save Report
        report = {
            "model_version": self.version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dataset_size": len(dataset),
            "metrics": final_metrics,
        }

        output_path = f"outputs/evaluation_report_{self.version}.json"
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
