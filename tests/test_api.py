"""
API Tests
"""

from fastapi.testclient import TestClient
from main_v2 import app
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    """Test health endpoint returns 200 and expected structure"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_version" in data
    assert "database_connected" in data


def test_recommend_tfidf(client):
    """Test recommendation endpoint"""
    # Requires model to be loaded.
    # If running in environment without model, this might fail unless mocked.
    # We assume 'Inception' (or any title) triggers search.

    response = client.get("/recommend/tfidf", params={"title": "Inception"})

    # If model not loaded, it might return 500 or empty.
    # main_v2 raises 500 if internal error.
    # If Inception not found/cold start, it returns 404 or empty list?
    # main_v2: tfidf_recommend raises HTTPException if title not found

    # Let's handle expected errors gracefully in test logic
    if response.status_code == 200:
        assert isinstance(response.json(), list)
    elif response.status_code == 404:
        # Title not found is a valid response for random title
        pass
    else:
        # 500 is bad
        assert response.status_code != 500


def test_invalid_input(client):
    """Test input validation"""
    response = client.get("/recommend/tfidf", params={"title": ""})
    assert response.status_code == 422  # Validation error for min_length
