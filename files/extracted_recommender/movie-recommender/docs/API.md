# 🔌 API Integration Guide

This document explains how the frontend integrates with your FastAPI backend.

## Overview

The frontend uses a centralized API client (`lib/api.ts`) with typed TypeScript interfaces for all endpoints.

## API Client Architecture

### Base Configuration

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

### ApiClient Class

```typescript
class ApiClient {
  private async fetch<T>(endpoint: string): Promise<T>
  private async post<T>(endpoint: string, data: unknown): Promise<T>
  
  async getHomeMovies(category, limit): Promise<MovieCard[]>
  async searchMovies(query, limit): Promise<MovieCard[]>
  async getMovieDetails(tmdbId): Promise<MovieDetails>
  async getRecommendations(movieTitle, sessionId, topN): Promise<RecommendationItem[]>
  async trackEvent(payload): Promise<void>
}
```

## Endpoints Used

### 1. Home Page Movies

```
GET /home?category={category}&limit={limit}
```

**Parameters:**
- `category`: `"trending"` | `"popular"` | `"top_rated"`
- `limit`: Number (default: 20)

**Response:** Array of `MovieCard`
```typescript
interface MovieCard {
  id: number;
  title: string;
  poster_url: string;
  vote_average: number;
  release_date?: string;
}
```

**Frontend Usage:**
```typescript
const trending = await api.getHomeMovies("trending", 20);
```

**When Called:**
- On initial page load (`app/page.tsx`)
- Loads 3 categories in parallel

---

### 2. Movie Search

```
GET /search?query={query}&limit={limit}
```

**Parameters:**
- `query`: String (URL-encoded)
- `limit`: Number (default: 20)

**Response:** Array of `MovieCard`

**Frontend Usage:**
```typescript
const results = await api.searchMovies("inception", 10);
```

**When Called:**
- In `SearchModal` component
- Debounced by 300ms on user input
- Auto-encodes special characters

---

### 3. Movie Details

```
GET /movie/{tmdb_id}
```

**Parameters:**
- `tmdb_id`: Number (path parameter)

**Response:** `MovieDetails`
```typescript
interface MovieDetails {
  id: number;
  title: string;
  poster_url: string;
  backdrop_url: string;
  overview: string;
  vote_average: number;
  genres: string[];
  release_date?: string;
  runtime?: number;
  tagline?: string;
}
```

**Frontend Usage:**
```typescript
const movie = await api.getMovieDetails(550);
```

**When Called:**
- Hero section (first trending movie)
- Movie detail modal opened
- Recommendation click

---

### 4. Recommendations

```
GET /recommend/tfidf?title={title}&top_n={n}&session_id={id}
```

**Parameters:**
- `title`: String (URL-encoded movie title)
- `top_n`: Number (default: 10)
- `session_id`: String (user session UUID)

**Response:** Array of `RecommendationItem`
```typescript
interface RecommendationItem {
  id: number;
  title: string;
  poster_url: string;
  similarity_score?: number;
  vote_average?: number;
}
```

**Frontend Usage:**
```typescript
const recommendations = await api.getRecommendations(
  "The Matrix",
  sessionId,
  6
);
```

**When Called:**
- In `MovieDetailModal` after movie details load
- Uses stored session ID from localStorage

---

### 5. Event Tracking

```
POST /events
```

**Request Body:**
```typescript
interface EventPayload {
  session_id: string;
  movie_id: number;
  event_type: "click" | "like" | "dislike" | "impression";
}
```

**Response:** Void (success/error status)

**Frontend Usage:**
```typescript
await api.trackEvent({
  session_id: "session_123",
  movie_id: 550,
  event_type: "like"
});
```

**When Called:**
- `impression`: Movie detail modal opened
- `click`: Movie card clicked (any category row)
- `like`: Like button pressed in detail modal
- `dislike`: Dislike button pressed in detail modal

## Session Management

### Session ID Generation

```typescript
// lib/api.ts
export function getSessionId(): string {
  let sessionId = localStorage.getItem("movie_session_id");
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("movie_session_id", sessionId);
  }
  return sessionId;
}
```

### Usage in Components

```typescript
// hooks/useSessionTracking.ts
const { sessionId, trackEvent } = useSessionTracking();

// Track events
await trackEvent(movieId, "like");
```

## Error Handling

### API Client Level

```typescript
private async fetch<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`);
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  
  return response.json();
}
```

### Component Level

```typescript
try {
  const movies = await api.getHomeMovies("trending");
  setMovies(movies);
} catch (error) {
  console.error("Failed to load movies:", error);
  // Fallback: Show empty state or error message
}
```

## CORS Requirements

Your FastAPI backend must allow requests from:
- Development: `http://localhost:3000`
- Production: Your deployed domain

**FastAPI CORS Setup:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Request Flow Examples

### Home Page Load
```
1. User visits http://localhost:3000
2. Frontend calls:
   - GET /home?category=trending&limit=20
   - GET /home?category=popular&limit=20
   - GET /home?category=top_rated&limit=20
3. Frontend calls GET /movie/{id} for hero movie
4. Renders page with all data
```

### Search Flow
```
1. User types "matrix" in search
2. Frontend debounces 300ms
3. Calls GET /search?query=matrix&limit=10
4. Displays results in dropdown
5. User clicks result
6. Calls POST /events with type="click"
7. Opens detail modal
```

### Movie Detail Flow
```
1. User clicks movie card
2. Calls POST /events with type="click"
3. Calls GET /movie/{id}
4. Calls POST /events with type="impression"
5. Calls GET /recommend/tfidf?title={title}&session_id={id}
6. Displays movie details + recommendations
```

### Like/Dislike Flow
```
1. User clicks Like button
2. UI updates immediately (optimistic)
3. Calls POST /events with type="like"
4. Backend can use this for future recommendations
```

## Testing API Integration

### 1. Check Backend Health
```bash
curl http://localhost:8000/docs
```

### 2. Test Individual Endpoints
```bash
# Get trending movies
curl http://localhost:8000/home?category=trending&limit=5

# Search
curl "http://localhost:8000/search?query=matrix&limit=5"

# Get movie details
curl http://localhost:8000/movie/603

# Track event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test123","movie_id":603,"event_type":"click"}'
```

### 3. Monitor Network Tab
Open Chrome DevTools → Network tab while using the app to see all API calls in real-time.

## Optimization Opportunities

### 1. Implement Caching
```typescript
// Use SWR or React Query
import useSWR from 'swr';

const { data, error } = useSWR(
  '/home?category=trending',
  () => api.getHomeMovies('trending')
);
```

### 2. Batch Requests
Combine multiple category requests into one endpoint if backend supports it.

### 3. Pagination
Implement infinite scroll instead of loading all 20 movies at once.

### 4. Request Deduplication
Prevent duplicate simultaneous requests for the same movie details.

## API Response Validation

The frontend expects specific fields. Ensure your backend returns:

**Required Fields:**
- `id`, `title`, `poster_url`, `vote_average`

**Optional Fields:**
- `release_date`, `genres`, `runtime`, `tagline`, `backdrop_url`

**Fallback Handling:**
```typescript
// Frontend gracefully handles missing images
{movie.poster_url ? (
  <Image src={movie.poster_url} ... />
) : (
  <div>No Image</div>
)}
```

---

## Support

For API-specific issues:
1. Check FastAPI logs
2. Verify endpoint returns expected JSON structure
3. Test with curl/Postman first
4. Check CORS configuration
5. Verify session_id is being sent correctly
