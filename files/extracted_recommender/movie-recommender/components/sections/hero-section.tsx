"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Info, Star } from "lucide-react";
import Image from "next/image";
import { MovieDetails } from "@/types/api";
import { formatRating, formatYear, formatRuntime, cn } from "@/lib/utils";

interface HeroSectionProps {
  movies: MovieDetails[];
  onPlayClick: (movieId: number) => void;
  onInfoClick: (movieId: number) => void;
}

export function HeroSection({
  movies,
  onPlayClick,
  onInfoClick,
}: HeroSectionProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (movies.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % movies.length);
    }, 8000);

    return () => clearInterval(interval);
  }, [movies.length]);

  if (movies.length === 0) {
    return (
      <div className="relative h-[85vh] w-full bg-cinema-black animate-pulse" />
    );
  }

  const movie = movies[currentIndex];

  return (
    <div className="relative h-[85vh] w-full overflow-hidden bg-cinema-black">
      <AnimatePresence mode="wait">
        <motion.div
          key={movie.id}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1 }}
          className="absolute inset-0"
        >
          {/* Background Image */}
          {movie.backdrop_url && (
            <div className="absolute inset-0">
              <Image
                src={movie.backdrop_url}
                alt={movie.title}
                fill
                priority
                className="object-cover object-center"
                sizes="100vw"
              />
              {/* Vignette effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-cinema-black via-transparent to-cinema-black/80" />
              <div className="absolute inset-0 bg-gradient-to-t from-cinema-black via-cinema-black/40 to-transparent" />
            </div>
          )}

          {/* Content */}
          <div className="relative z-10 flex h-full items-end pb-48">
            <div className="container mx-auto px-6 md:px-12">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="max-w-2xl"
              >
                {/* Title */}
                <h1 className="mb-4 font-display text-5xl font-black leading-tight text-white md:text-7xl lg:text-8xl">
                  {movie.title}
                </h1>

                {/* Meta info */}
                <div className="mb-4 flex flex-wrap items-center gap-4 text-sm text-gray-300">
                  <div className="flex items-center gap-1.5 rounded-full bg-black/40 px-3 py-1 backdrop-blur-sm">
                    <Star className="h-4 w-4 fill-cinema-gold text-cinema-gold" />
                    <span className="font-bold text-white">
                      {formatRating(movie.vote_average)}
                    </span>
                  </div>
                  {movie.release_date && (
                    <span className="font-semibold">
                      {formatYear(movie.release_date)}
                    </span>
                  )}
                  {movie.runtime && (
                    <span className="font-semibold">
                      {formatRuntime(movie.runtime)}
                    </span>
                  )}
                  {movie.genres && movie.genres.length > 0 && (
                    <span className="font-semibold">
                      {movie.genres.slice(0, 3).join(" • ")}
                    </span>
                  )}
                </div>

                {/* Tagline */}
                {movie.tagline && (
                  <p className="mb-4 font-display text-lg italic text-gray-300">
                    {movie.tagline}
                  </p>
                )}

                {/* Overview */}
                <p className="mb-8 max-w-xl text-base leading-relaxed text-gray-200 md:text-lg line-clamp-3">
                  {movie.overview}
                </p>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-4">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onPlayClick(movie.id)}
                    className="flex items-center gap-3 rounded-lg bg-white px-8 py-3.5 font-display text-base font-bold text-black transition-colors hover:bg-gray-200"
                  >
                    <Play className="h-5 w-5 fill-current" />
                    <span>Watch Now</span>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onInfoClick(movie.id)}
                    className="flex items-center gap-3 rounded-lg bg-white/20 px-8 py-3.5 font-display text-base font-bold text-white backdrop-blur-sm transition-colors hover:bg-white/30"
                  >
                    <Info className="h-5 w-5" />
                    <span>More Info</span>
                  </motion.button>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Indicators */}
      {movies.length > 1 && (
        <div className="absolute bottom-48 right-12 z-20 hidden flex-col gap-4 md:flex">
          {movies.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={cn(
                "h-2 rounded-full transition-all duration-300",
                index === currentIndex
                  ? "w-8 bg-cinema-accent"
                  : "w-2 bg-white/50 hover:bg-white"
              )}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
