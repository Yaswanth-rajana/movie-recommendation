# Movie Recommendation Data

This directory contains the data used for training the TF-IDF recommendation model.

## Data Provenance

All movie data is sourced from **The Movie Database (TMDB) API**:
- API Documentation: https://developers.themoviedb.org/3
- Data License: TMDB API Terms of Service
- Attribution Required: "This product uses the TMDB API but is not endorsed or certified by TMDB."

## Directory Structure

```
data/
├── raw/              # Raw data from TMDB API (JSON)
│   └── movies_*.json
├── processed/        # Cleaned and processed data (CSV/Parquet)
│   └── movies_processed.csv
└── README.md         # This file
```

## Data Schema

### Raw Data (`raw/movies_*.json`)

Each movie record from TMDB contains:
- `id` (int): TMDB movie ID
- `title` (str): Movie title
- `overview` (str): Plot summary
- `genres` (list): Genre objects with id and name
- `keywords` (list): Keyword objects (from separate API call)
- `poster_path` (str): Poster image path
- `backdrop_path` (str): Backdrop image path
- `popularity` (float): TMDB popularity score
- `vote_average` (float): Average user rating (0-10)
- `vote_count` (int): Number of votes
- `release_date` (str): Release date (YYYY-MM-DD)
- `runtime` (int): Runtime in minutes

### Processed Data (`processed/movies_processed.csv`)

Cleaned data ready for TF-IDF training:
- `tmdb_id` (int): TMDB movie ID
- `title` (str): Movie title
- `overview_clean` (str): Cleaned plot summary (lowercased, punctuation removed)
- `genres_str` (str): Space-separated genre names
- `keywords_str` (str): Space-separated keywords
- `combined_features` (str): Concatenated text for TF-IDF (overview + genres + keywords)
- `popularity` (float): Popularity score
- `vote_average` (float): Rating
- `release_date` (str): Release date

## Data Cleaning Steps

1. **Fetch from TMDB**: Use `data_ingestion/fetch_tmdb.py` to download movie data
2. **Filter**: Remove movies with < 100 votes (low-quality/unreliable data)
3. **Text Cleaning**:
   - Lowercase all text
   - Remove special characters and punctuation
   - Remove extra whitespace
   - Handle missing values (fill with empty string)
4. **Feature Engineering**:
   - Combine overview, genres, and keywords into single text field
   - Apply weighted concatenation (overview: 1.0, genres: 0.5, keywords: 0.3)
5. **Deduplication**: Remove duplicate movies by TMDB ID

## Reproducibility

To regenerate the dataset:

```bash
# 1. Set your TMDB API key
export TMDB_API_KEY=your_api_key_here

# 2. Fetch raw data from TMDB
python data_ingestion/fetch_tmdb.py --pages 50 --output ml/data/raw/

# 3. Process and clean data
python ml/train_tfidf.py --config ml/config.yaml
```

This will:
- Download ~1000 popular movies from TMDB
- Clean and process the data
- Save to `ml/data/processed/`
- Train TF-IDF model and save artifacts

## Data Statistics

After processing (example from v1.0.0):
- **Total Movies**: 1,000
- **Date Range**: 1970 - 2026
- **Average Overview Length**: 150 words
- **Genres Coverage**: 19 unique genres
- **Missing Overviews**: < 5%

## Privacy & Ethics

- **No Personal Data**: Only public movie metadata is used
- **No User Data**: User interactions are stored separately with session IDs (no PII)
- **Attribution**: TMDB is properly credited in all public-facing interfaces
- **Rate Limiting**: API calls respect TMDB rate limits (40 requests/10 seconds)

## Future Improvements

- [ ] Add IMDb ID mapping for cross-referencing
- [ ] Include cast and crew information
- [ ] Add movie collections/franchises
- [ ] Support multiple languages
- [ ] Implement incremental updates (only fetch new movies)
