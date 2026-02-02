"""
Model Evaluation Script

Evaluates TF-IDF recommendation model and generates quality reports.

Usage:
    python ml/evaluate.py --version v1.0.0
"""

import os
import sys
import argparse
import pickle
import json
from typing import List, Tuple
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_artifacts(version: str):
    """Load model artifacts for a specific version."""
    base_dir = f"artifacts/tfidf/{version}"

    if not os.path.exists(base_dir):
        print(f"ERROR: Version {version} not found at {base_dir}")
        sys.exit(1)

    print(f"📦 Loading artifacts for version {version}...")

    # Load metadata
    with open(os.path.join(base_dir, "metadata.json"), "r") as f:
        metadata = json.load(f)

    # Load TF-IDF matrix
    with open(os.path.join(base_dir, "tfidf_matrix.pkl"), "rb") as f:
        tfidf_matrix = pickle.load(f)

    # Load dataframe
    with open(os.path.join(base_dir, "movies.pkl"), "rb") as f:
        df = pickle.load(f)

    # Load indices
    with open(os.path.join(base_dir, "indices.pkl"), "rb") as f:
        indices = pickle.load(f)

    print(f"   ✓ Loaded {len(df)} movies")
    print(f"   ✓ Matrix shape: {tfidf_matrix.shape}")

    return metadata, tfidf_matrix, df, indices


def get_recommendations(
    title: str, tfidf_matrix, df, indices, top_n: int = 10
) -> List[Tuple[str, float]]:
    """Get recommendations for a movie."""
    title_lower = title.lower().strip()

    if title_lower not in indices:
        return []

    idx = indices[title_lower]

    # Compute similarities
    vec = tfidf_matrix[idx]
    similarities = (tfidf_matrix @ vec.T).toarray().flatten()

    # Sort and get top N (excluding self)
    similar_indices = np.argsort(-similarities)

    recommendations = []
    for i in similar_indices:
        if int(i) == int(idx):
            continue

        movie_title = df.iloc[int(i)]["title"]
        score = float(similarities[int(i)])
        recommendations.append((movie_title, score))

        if len(recommendations) >= top_n:
            break

    return recommendations


def evaluate_model(metadata, tfidf_matrix, df, indices):
    """Run evaluation tests on the model."""
    print("\n" + "=" * 60)
    print("📊 Model Evaluation Report")
    print("=" * 60)

    # Model info
    print(f"\n📋 Model Information:")
    print(f"   Version: {metadata['model_version']}")
    print(f"   Trained on: {metadata['trained_on']}")
    print(f"   Number of movies: {metadata['num_movies']}")
    print(f"   Vocabulary size: {metadata['vocabulary_size']}")

    # Metrics
    print(f"\n📈 Quality Metrics:")
    metrics = metadata["metrics"]
    print(f"   Average similarity: {metrics['avg_similarity']:.4f}")
    print(f"   Median similarity: {metrics['median_similarity']:.4f}")
    print(f"   Std similarity: {metrics['std_similarity']:.4f}")
    print(f"   Sparsity: {metrics['sparsity']:.2%}")

    # Sample recommendations
    print(f"\n🎬 Sample Recommendations:")

    test_movies = [
        "The Dark Knight",
        "Inception",
        "The Matrix",
        "Pulp Fiction",
        "Forrest Gump",
    ]

    for movie in test_movies:
        movie_lower = movie.lower().strip()

        if movie_lower in indices:
            recs = get_recommendations(movie, tfidf_matrix, df, indices, top_n=5)
            print(f"\n   '{movie}':")
            for i, (title, score) in enumerate(recs, 1):
                print(f"      {i}. {title} (score: {score:.3f})")
        else:
            print(f"\n   '{movie}': Not found in dataset")

    # Coverage analysis
    print(f"\n📊 Coverage Analysis:")

    # Count movies with at least one good recommendation (score > 0.1)
    good_recs_count = 0
    for idx in range(len(df)):
        vec = tfidf_matrix[idx]
        sims = (tfidf_matrix @ vec.T).toarray().flatten()
        sims = sims[sims < 0.9999]  # Exclude self

        if len(sims) > 0 and np.max(sims) > 0.1:
            good_recs_count += 1

    coverage = good_recs_count / len(df) * 100
    print(
        f"   Movies with good recommendations (>0.1): {good_recs_count}/{len(df)} ({coverage:.1f}%)"
    )

    # Distribution of max similarities
    max_sims = []
    for idx in range(min(100, len(df))):
        vec = tfidf_matrix[idx]
        sims = (tfidf_matrix @ vec.T).toarray().flatten()
        sims = sims[sims < 0.9999]
        if len(sims) > 0:
            max_sims.append(np.max(sims))

    print(f"   Max similarity distribution (sample of 100):")
    print(f"      Mean: {np.mean(max_sims):.3f}")
    print(f"      Median: {np.median(max_sims):.3f}")
    print(f"      Min: {np.min(max_sims):.3f}")
    print(f"      Max: {np.max(max_sims):.3f}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Evaluate TF-IDF model")
    parser.add_argument(
        "--version", type=str, default="v1.0.0", help="Model version to evaluate"
    )

    args = parser.parse_args()

    metadata, tfidf_matrix, df, indices = load_artifacts(args.version)
    evaluate_model(metadata, tfidf_matrix, df, indices)


if __name__ == "__main__":
    main()
