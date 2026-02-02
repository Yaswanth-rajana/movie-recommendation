"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { MovieCard, MovieDetails } from "@/types/api";
import { Navbar } from "@/components/sections/navbar";
import { HeroSection } from "@/components/sections/hero-section";
import { SearchModal } from "@/components/sections/search-modal";
import { MovieDetailModal } from "@/components/sections/movie-detail-modal";
import { MovieRow } from "@/components/ui/movie-row";
import { useSessionTracking } from "@/hooks/useSessionTracking";

export default function Home() {
  const [heroMovies, setHeroMovies] = useState<MovieDetails[]>([]);
  const [trendingMovies, setTrendingMovies] = useState<MovieCard[]>([]);
  const [popularMovies, setPopularMovies] = useState<MovieCard[]>([]);
  const [topRatedMovies, setTopRatedMovies] = useState<MovieCard[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null);
  const { trackEvent } = useSessionTracking();

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      // Load all categories
      const [trending, popular, topRated] = await Promise.all([
        api.getHomeMovies("trending", 20),
        api.getHomeMovies("popular", 20),
        api.getHomeMovies("top_rated", 20),
      ]);

      setTrendingMovies(trending);
      setPopularMovies(popular);
      setTopRatedMovies(topRated);

      // Set top 5 trending movies as hero carousel
      if (trending.length > 0) {
        const top5 = trending.slice(0, 5);
        const detailsPromises = top5.map((movie) => api.getMovieDetails(movie.id));
        const heroes = await Promise.all(detailsPromises);
        setHeroMovies(heroes);
      }
    } catch (error) {
      console.error("Failed to load home data:", error);
    }
  };

  const handleMovieClick = (movie: MovieCard) => {
    setSelectedMovieId(movie.id);
    trackEvent(movie.id, "click");
  };

  const handleHeroPlay = (movieId: number) => {
    setSelectedMovieId(movieId);
  };

  const handleHeroInfo = (movieId: number) => {
    setSelectedMovieId(movieId);
  };

  return (
    <div className="min-h-screen bg-cinema-black">
      {/* Navigation */}
      <Navbar onSearchClick={() => setIsSearchOpen(true)} />

      {/* Hero Section */}
      {/* Hero Section */}
      <HeroSection
        movies={heroMovies}
        onPlayClick={handleHeroPlay}
        onInfoClick={handleHeroInfo}
      />

      {/* Movie Rows */}
      <div className="relative -mt-32 space-y-8 px-6 md:px-12">
        <MovieRow
          title="Trending Now"
          movies={trendingMovies}
          onMovieClick={handleMovieClick}
        />
        <MovieRow
          title="Popular on Cinematic"
          movies={popularMovies}
          onMovieClick={handleMovieClick}
        />
        <MovieRow
          title="Top Rated"
          movies={topRatedMovies}
          onMovieClick={handleMovieClick}
        />
      </div>

      {/* Footer spacing */}
      <div className="h-32" />

      {/* Modals */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onMovieClick={handleMovieClick}
      />

      <MovieDetailModal
        movieId={selectedMovieId}
        onClose={() => setSelectedMovieId(null)}
        onMovieClick={(id) => setSelectedMovieId(id)}
      />
    </div>
  );
}
