import pandas as pd
import numpy as np
import pickle
import os
import json
from sklearn.decomposition import TruncatedSVD
from typing import List, Dict, Optional, Tuple

class CollaborativeFilter:
    def __init__(self, n_components: int = 50, random_state: int = 42):
        self.n_components = n_components
        self.random_state = random_state
        self.model = None
        self.user_item_matrix = None
        self.user_mapper = None  # user_id -> index
        self.item_mapper = None  # movie_id -> index
        self.reverse_user_mapper = None  # index -> user_id
        self.reverse_item_mapper = None  # index -> movie_id
        self.metadata = {}

    def train(self, ratings_df: pd.DataFrame):
        """
        Train the SVD model on the provided ratings DataFrame.
        Expected columns: 'user_id', 'movielens_movie_id', 'rating'
        """
        print("Creating user-item matrix...")
        # Create sparse matrix
        self.user_item_matrix = ratings_df.pivot(
            index='user_id',
            columns='movielens_movie_id',
            values='rating'
        ).fillna(0)

        # Create mappings
        self.user_mapper = {user: i for i, user in enumerate(self.user_item_matrix.index)}
        self.reverse_user_mapper = {i: user for i, user in enumerate(self.user_item_matrix.index)}
        self.item_mapper = {item: i for i, item in enumerate(self.user_item_matrix.columns)}
        self.reverse_item_mapper = {i: item for i, item in enumerate(self.user_item_matrix.columns)}

        print(f"Matrix shape: {self.user_item_matrix.shape}")
        
        # Train SVD
        print("Training TruncatedSVD...")
        self.model = TruncatedSVD(
            n_components=self.n_components,
            random_state=self.random_state
        )
        self.model.fit(self.user_item_matrix)
        
        explained_variance = self.model.explained_variance_ratio_.sum()
        print(f"Explained Variance Ratio: {explained_variance:.4f}")
        
        self.metadata = {
            "n_components": self.n_components,
            "explained_variance": float(explained_variance),
            "n_users": self.user_item_matrix.shape[0],
            "n_items": self.user_item_matrix.shape[1]
        }

    def recommend(self, user_id: int, top_n: int = 10) -> List[Dict]:
        """
        Get recommendations for a specific user.
        Returns list of dicts: {'movielens_id': int, 'score': float}
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
            
        if user_id not in self.user_mapper:
            print(f"User {user_id} not found in training data (Cold Start)")
            return []

        # Get user index and vector
        user_idx = self.user_mapper[user_id]
        user_vector = self.user_item_matrix.iloc[user_idx].values.reshape(1, -1)
        
        # Transform user vector to latent space
        user_latent = self.model.transform(user_vector)
        
        # Reconstruct prediction (dot product with item components)
        # item_components shape: (n_components, n_items)
        predicted_ratings = np.dot(user_latent, self.model.components_)
        predicted_ratings = predicted_ratings.flatten()

        # Identify already rated items to filter them out
        rated_indices = np.where(user_vector.flatten() > 0)[0]
        
        # Create (index, score) pairs
        recommendations = []
        for idx, score in enumerate(predicted_ratings):
            if idx not in rated_indices:
                recommendations.append((idx, score))
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        # Top N
        top_recs = recommendations[:top_n]
        
        # Map back to item IDs
        results = []
        for idx, score in top_recs:
            movie_id = self.reverse_item_mapper[idx]
            results.append({
                "movielens_id": int(movie_id),
                "score": float(score)
            })
            
        return results

    def save(self, output_dir: str):
        """Save model and artifacts"""
        os.makedirs(output_dir, exist_ok=True)
        
        artifacts = {
            "model": self.model,
            "user_item_matrix": self.user_item_matrix,
            "user_mapper": self.user_mapper,
            "item_mapper": self.item_mapper,
            "metadata": self.metadata
        }
        
        with open(os.path.join(output_dir, "cf_model.pkl"), "wb") as f:
            pickle.dump(artifacts, f)
            
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(self.metadata, f, indent=2)
            
        print(f"Model saved to {output_dir}")

    def load(self, source_dir: str):
        """Load model and artifacts"""
        path = os.path.join(source_dir, "cf_model.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError(f"No model found at {path}")
            
        with open(path, "rb") as f:
            artifacts = pickle.load(f)
            
        self.model = artifacts["model"]
        self.user_item_matrix = artifacts["user_item_matrix"]
        self.user_mapper = artifacts["user_mapper"]
        self.item_mapper = artifacts["item_mapper"]
        self.metadata = artifacts.get("metadata", {})
        
        # Reconstruct reverse mappers
        self.reverse_user_mapper = {i: u for u, i in self.user_mapper.items()}
        self.reverse_item_mapper = {i: m for m, i in self.item_mapper.items()}
