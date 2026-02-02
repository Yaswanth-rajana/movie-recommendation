"""
TF-IDF Model Training Pipeline

This script trains a content-based recommendation model using TF-IDF vectorization.
It creates versioned artifacts with full reproducibility.

Usage:
    python ml/train_tfidf.py --config ml/config.yaml --database movie_rec.db
"""

import os
import sys
import argparse
import pickle
import json
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
import yaml

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TFIDFTrainer:
    """Handles TF-IDF model training with versioning and reproducibility."""

    def __init__(self, config_path: str, database_path: str):
        self.config_path = config_path
        self.database_path = database_path
        self.config = self.load_config()
        self.df = None
        self.tfidf_matrix = None
        self.vectorizer = None
        self.indices = None

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def load_data_from_database(self) -> pd.DataFrame:
        """Load movie data from SQLite database."""
        print("\n📊 Loading data from database...")

        conn = sqlite3.connect(self.database_path)

        query = """
            SELECT 
                tmdb_id,
                title,
                overview,
                genres,
                keywords,
                popularity,
                vote_average,
                release_date
            FROM movies
            WHERE vote_count >= ?
            ORDER BY popularity DESC
        """

        min_votes = self.config.get("data_source", {}).get("min_vote_count", 100)
        df = pd.read_sql_query(query, conn, params=(min_votes,))
        conn.close()

        print(f"   ✓ Loaded {len(df)} movies")
        return df

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if pd.isna(text) or text is None:
            return ""

        text = str(text).lower()
        # Remove special characters but keep spaces
        text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
        # Remove extra whitespace
        text = " ".join(text.split())
        return text

    def parse_json_field(self, json_str: str) -> List[str]:
        """Parse JSON string field (genres, keywords)."""
        if pd.isna(json_str) or not json_str:
            return []

        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return [str(item).lower() for item in data]
            return []
        except:
            return []

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and engineer features for TF-IDF."""
        print("\n🔧 Engineering features...")

        df = df.copy()

        # Clean overview
        df["overview_clean"] = df["overview"].apply(self.clean_text)

        # Parse and clean genres
        df["genres_list"] = df["genres"].apply(self.parse_json_field)
        df["genres_str"] = df["genres_list"].apply(lambda x: " ".join(x))

        # Parse and clean keywords
        df["keywords_list"] = df["keywords"].apply(self.parse_json_field)
        df["keywords_str"] = df["keywords_list"].apply(lambda x: " ".join(x))

        # Combine features with weights
        feature_config = self.config.get("features", {})
        weight_overview = feature_config.get("weight_overview", 1.0)
        weight_genres = feature_config.get("weight_genres", 0.5)
        weight_keywords = feature_config.get("weight_keywords", 0.3)

        def combine_features(row):
            parts = []
            
            # Overview (weighted by repetition)
            if row.get('overview_clean'):
                parts.extend([str(row['overview_clean'])] * int(weight_overview * 2))
            
            # Genres (weighted)
            if row.get('genres_str'):
                parts.extend([str(row['genres_str'])] * int(weight_genres * 4))
            
            # Keywords (weighted)
            if row.get('keywords_str'):
                parts.extend([str(row['keywords_str'])] * int(weight_keywords * 3))
            
            return ' '.join(parts)
        
        if not df.empty:
            df['combined_features'] = df.apply(combine_features, axis=1)
        else:
            df['combined_features'] = pd.Series([], dtype=object) # Ensure column exists with correct dtype for empty DF

        # Filter out movies with no features
        df = df[df["combined_features"].str.len() > 0].reset_index(drop=True)

        print(f"   ✓ Prepared {len(df)} movies with features")
        print(
            f"   ✓ Average feature length: {df['combined_features'].str.len().mean():.0f} chars"
        )

        return df

    def train_tfidf(self, df: pd.DataFrame) -> Tuple[Any, Any]:
        """Train TF-IDF vectorizer and compute similarity matrix."""
        print("\n🤖 Training TF-IDF model...")

        tfidf_config = self.config.get("tfidf", {})

        # Initialize vectorizer
        vectorizer = TfidfVectorizer(
            max_features=tfidf_config.get("max_features", 5000),
            ngram_range=tuple(tfidf_config.get("ngram_range", [1, 2])),
            min_df=tfidf_config.get("min_df", 2),
            max_df=tfidf_config.get("max_df", 0.8),
            use_idf=tfidf_config.get("use_idf", True),
            sublinear_tf=tfidf_config.get("sublinear_tf", True),
            stop_words="english",
        )

        # Fit and transform
        start_time = time.time()
        tfidf_matrix = vectorizer.fit_transform(df["combined_features"])
        training_time = time.time() - start_time

        print(f"   ✓ TF-IDF matrix shape: {tfidf_matrix.shape}")
        print(f"   ✓ Vocabulary size: {len(vectorizer.vocabulary_)}")
        print(
            f"   ✓ Sparsity: {(1.0 - tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1])):.2%}"
        )
        print(f"   ✓ Training time: {training_time:.2f}s")

        return vectorizer, tfidf_matrix

    def build_indices(self, df: pd.DataFrame) -> Dict[str, int]:
        """Build title-to-index mapping."""
        indices = {}
        for idx, title in enumerate(df["title"]):
            # Normalize title (lowercase, strip)
            normalized = str(title).strip().lower()
            indices[normalized] = idx
        return indices

    def compute_metrics(self, tfidf_matrix: Any) -> Dict[str, Any]:
        """Compute model evaluation metrics."""
        print("\n📈 Computing metrics...")

        # Sample similarities
        sample_size = min(100, tfidf_matrix.shape[0])
        sample_indices = np.random.choice(
            tfidf_matrix.shape[0], sample_size, replace=False
        )

        similarities = []
        for idx in sample_indices:
            vec = tfidf_matrix[idx]
            sims = cosine_similarity(vec, tfidf_matrix).flatten()
            # Exclude self-similarity
            sims = sims[sims < 0.9999]
            similarities.extend(sims.tolist())

        metrics = {
            "avg_similarity": float(np.mean(similarities)),
            "median_similarity": float(np.median(similarities)),
            "std_similarity": float(np.std(similarities)),
            "sparsity": float(
                1.0 - tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1])
            ),
            "matrix_shape": list(tfidf_matrix.shape),
            "nnz": int(tfidf_matrix.nnz),
        }

        print(f"   ✓ Average similarity: {metrics['avg_similarity']:.3f}")
        print(f"   ✓ Median similarity: {metrics['median_similarity']:.3f}")
        print(f"   ✓ Sparsity: {metrics['sparsity']:.2%}")

        return metrics

    def save_artifacts(
        self,
        df: pd.DataFrame,
        vectorizer: Any,
        tfidf_matrix: Any,
        indices: Dict[str, int],
        metrics: Dict[str, Any],
    ):
        """Save versioned model artifacts."""
        print("\n💾 Saving artifacts...")

        version = self.config.get("model_version", "v1.0.0")
        base_dir = self.config.get("artifacts", {}).get("base_dir", "artifacts/tfidf")
        version_dir = os.path.join(base_dir, version)

        os.makedirs(version_dir, exist_ok=True)

        # Save TF-IDF matrix
        matrix_path = os.path.join(version_dir, "tfidf_matrix.pkl")
        with open(matrix_path, "wb") as f:
            pickle.dump(tfidf_matrix, f)
        print(f"   ✓ Saved TF-IDF matrix: {matrix_path}")

        # Save vectorizer
        vectorizer_path = os.path.join(version_dir, "vectorizer.pkl")
        with open(vectorizer_path, "wb") as f:
            pickle.dump(vectorizer, f)
        print(f"   ✓ Saved vectorizer: {vectorizer_path}")

        # Save indices
        indices_path = os.path.join(version_dir, "indices.pkl")
        with open(indices_path, "wb") as f:
            pickle.dump(indices, f)
        print(f"   ✓ Saved indices: {indices_path}")

        # Save dataframe
        df_path = os.path.join(version_dir, "movies.pkl")
        with open(df_path, "wb") as f:
            pickle.dump(
                df[["tmdb_id", "title", "popularity", "vote_average", "release_date"]],
                f,
            )
        print(f"   ✓ Saved dataframe: {df_path}")

        # Save metadata
        metadata = {
            "model_version": version,
            "trained_on": datetime.utcnow().isoformat() + "Z",
            "num_movies": len(df),
            "tfidf_config": self.config.get("tfidf", {}),
            "feature_config": self.config.get("features", {}),
            "metrics": metrics,
            "vocabulary_size": len(vectorizer.vocabulary_),
            "artifact_paths": {
                "tfidf_matrix": matrix_path,
                "vectorizer": vectorizer_path,
                "indices": indices_path,
                "dataframe": df_path,
            },
        }

        metadata_path = os.path.join(version_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"   ✓ Saved metadata: {metadata_path}")

        print(f"\n✅ All artifacts saved to: {version_dir}")

    def train(self):
        """Run the complete training pipeline."""
        print("=" * 60)
        print("🎬 TF-IDF Movie Recommendation Model Training")
        print("=" * 60)

        start_time = time.time()

        # Load data
        self.df = self.load_data_from_database()

        # Prepare features
        self.df = self.prepare_features(self.df)

        # Train TF-IDF
        self.vectorizer, self.tfidf_matrix = self.train_tfidf(self.df)

        # Build indices
        self.indices = self.build_indices(self.df)

        # Compute metrics
        metrics = self.compute_metrics(self.tfidf_matrix)

        # Save artifacts
        self.save_artifacts(
            self.df, self.vectorizer, self.tfidf_matrix, self.indices, metrics
        )

        total_time = time.time() - start_time
        print(f"\n⏱️  Total training time: {total_time:.2f}s")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Train TF-IDF recommendation model")
    parser.add_argument(
        "--config", type=str, default="ml/config.yaml", help="Config file path"
    )
    parser.add_argument(
        "--database", type=str, default="movie_rec.db", help="Database path"
    )

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"ERROR: Config file not found: {args.config}")
        sys.exit(1)

    if not os.path.exists(args.database):
        print(f"ERROR: Database not found: {args.database}")
        print("Run data ingestion first: python data_ingestion/fetch_tmdb.py")
        sys.exit(1)

    trainer = TFIDFTrainer(args.config, args.database)
    trainer.train()


if __name__ == "__main__":
    main()
