#!/bin/bash

# Production-Ready Movie Recommendation System Setup Script

set -e  # Exit on error

echo "=========================================="
echo "🎬 Movie Recommendation System Setup"
echo "=========================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.8+"; exit 1; }
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "❗ Please edit .env and add your TMDB_API_KEY"
    echo "   Get your key from: https://www.themoviedb.org/settings/api"
    exit 1
fi

# Check if TMDB_API_KEY is set
source .env
if [ -z "$TMDB_API_KEY" ] || [ "$TMDB_API_KEY" = "your_api_key_here" ]; then
    echo "❌ TMDB_API_KEY not set in .env file"
    echo "   Get your key from: https://www.themoviedb.org/settings/api"
    exit 1
fi

echo "✅ TMDB_API_KEY found"
echo ""

# Check if database exists
if [ ! -f movie_rec.db ]; then
    echo "📊 Database not found. Running data ingestion..."
    echo "   This will fetch ~1000 movies from TMDB (takes 5-10 minutes)"
    read -p "   Continue? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python data_ingestion/fetch_tmdb.py --pages 50 --database movie_rec.db
        echo "✅ Data ingestion complete"
    else
        echo "❌ Database required. Please run manually:"
        echo "   python data_ingestion/fetch_tmdb.py --pages 50 --database movie_rec.db"
        exit 1
    fi
else
    echo "✅ Database found: movie_rec.db"
fi
echo ""

# Check if model artifacts exist
MODEL_VERSION=${MODEL_VERSION:-v1.0.0}
if [ ! -d "artifacts/tfidf/$MODEL_VERSION" ]; then
    echo "🤖 Model artifacts not found. Training TF-IDF model..."
    echo "   This will take 1-2 minutes..."
    python ml/train_tfidf.py --config ml/config.yaml --database movie_rec.db
    echo "✅ Model training complete"
else
    echo "✅ Model artifacts found: $MODEL_VERSION"
fi
echo ""

# Run evaluation
echo "📊 Running model evaluation..."
python ml/evaluate.py --version $MODEL_VERSION
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "🚀 To start the API server:"
echo "   uvicorn main_v2:app --reload --host 127.0.0.1 --port 8000"
echo ""
echo "📊 To start the Streamlit app:"
echo "   streamlit run app.py"
echo ""
echo "📈 Metrics available at:"
echo "   http://localhost:8000/metrics"
echo ""
echo "🏥 Health check:"
echo "   http://localhost:8000/health"
echo ""
