export interface MovieCard {
  id: number;
  title: string;
  poster_url: string;
  vote_average: number;
  release_date?: string;
}

export interface MovieDetails {
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

export interface RecommendationItem {
  id: number;
  title: string;
  poster_url: string;
  similarity_score?: number;
  vote_average?: number;
}

export interface EventPayload {
  session_id: string;
  movie_id: number;
  event_type: "click" | "like" | "dislike" | "impression";
}

export type Category = "trending" | "popular" | "top_rated";
