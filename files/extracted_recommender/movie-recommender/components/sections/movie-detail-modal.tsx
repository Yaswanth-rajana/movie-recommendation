"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Star, ThumbsUp, ThumbsDown, Play, Calendar, Clock } from "lucide-react";
import Image from "next/image";
import { api } from "@/lib/api";
import { MovieDetails, RecommendationItem } from "@/types/api";
import { formatRating, formatYear, formatRuntime } from "@/lib/utils";
import { useSessionTracking } from "@/hooks/useSessionTracking";

interface MovieDetailModalProps {
  movieId: number | null;
  onClose: () => void;
  onMovieClick: (movieId: number) => void;
}

export function MovieDetailModal({
  movieId,
  onClose,
  onMovieClick,
}: MovieDetailModalProps) {
  const [movie, setMovie] = useState<MovieDetails | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [liked, setLiked] = useState<boolean | null>(null);
  const { sessionId, trackEvent } = useSessionTracking();

  useEffect(() => {
    if (movieId) {
      loadMovieDetails(movieId);
    }
  }, [movieId]);

  const loadMovieDetails = async (id: number) => {
    setIsLoading(true);
    try {
      const details = await api.getMovieDetails(id);
      setMovie(details);

      // Track impression
      if (sessionId) {
        trackEvent(id, "impression");
      }

      // Load recommendations
      if (details.title && sessionId) {
        const recs = await api.getRecommendations(details.title, sessionId, 6);
        setRecommendations(recs);
      }
    } catch (error) {
      console.error("Failed to load movie details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLike = async () => {
    if (!movie || !sessionId) return;
    setLiked(true);
    await trackEvent(movie.id, "like");
  };

  const handleDislike = async () => {
    if (!movie || !sessionId) return;
    setLiked(false);
    await trackEvent(movie.id, "dislike");
  };

  if (!movieId) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-50 overflow-y-auto bg-black/90 backdrop-blur-sm"
      >
        <div className="min-h-screen py-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            onClick={(e) => e.stopPropagation()}
            className="relative mx-auto max-w-5xl overflow-hidden rounded-2xl bg-cinema-dark shadow-2xl"
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute right-4 top-4 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-black/50 backdrop-blur-sm transition-colors hover:bg-black/70"
            >
              <X className="h-6 w-6 text-white" />
            </button>

            {isLoading || !movie ? (
              <div className="flex h-96 items-center justify-center">
                <div className="h-12 w-12 animate-spin rounded-full border-4 border-cinema-accent border-t-transparent" />
              </div>
            ) : (
              <>
                {/* Hero Section */}
                <div className="relative h-[50vh] overflow-hidden">
                  {movie.backdrop_url && (
                    <>
                      <Image
                        src={movie.backdrop_url}
                        alt={movie.title}
                        fill
                        className="object-cover"
                        sizes="(max-width: 1280px) 100vw, 1280px"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-cinema-dark via-cinema-dark/60 to-transparent" />
                    </>
                  )}

                  {/* Title Overlay */}
                  <div className="absolute bottom-0 left-0 right-0 p-8">
                    <h1 className="mb-4 font-display text-4xl font-black text-white md:text-5xl">
                      {movie.title}
                    </h1>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-300">
                      <div className="flex items-center gap-1.5">
                        <Star className="h-5 w-5 fill-cinema-gold text-cinema-gold" />
                        <span className="font-bold text-white">
                          {formatRating(movie.vote_average)}
                        </span>
                      </div>
                      {movie.release_date && (
                        <div className="flex items-center gap-1.5">
                          <Calendar className="h-4 w-4" />
                          <span>{formatYear(movie.release_date)}</span>
                        </div>
                      )}
                      {movie.runtime && (
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-4 w-4" />
                          <span>{formatRuntime(movie.runtime)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-8">
                  {/* Action Buttons */}
                  <div className="mb-8 flex flex-wrap gap-4">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex items-center gap-2 rounded-lg bg-white px-6 py-3 font-display font-bold text-black transition-colors hover:bg-gray-200"
                    >
                      <Play className="h-5 w-5 fill-current" />
                      <span>Watch Now</span>
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleLike}
                      className={`flex items-center gap-2 rounded-lg px-6 py-3 font-display font-bold transition-colors ${
                        liked === true
                          ? "bg-cinema-accent text-white"
                          : "bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      <ThumbsUp className="h-5 w-5" />
                      <span>Like</span>
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleDislike}
                      className={`flex items-center gap-2 rounded-lg px-6 py-3 font-display font-bold transition-colors ${
                        liked === false
                          ? "bg-gray-700 text-white"
                          : "bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      <ThumbsDown className="h-5 w-5" />
                      <span>Dislike</span>
                    </motion.button>
                  </div>

                  {/* Genres */}
                  {movie.genres && movie.genres.length > 0 && (
                    <div className="mb-6 flex flex-wrap gap-2">
                      {movie.genres.map((genre) => (
                        <span
                          key={genre}
                          className="rounded-full bg-white/10 px-4 py-1.5 text-sm font-semibold text-gray-300"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Overview */}
                  <div className="mb-8">
                    <h2 className="mb-3 font-display text-xl font-bold text-white">
                      Overview
                    </h2>
                    <p className="leading-relaxed text-gray-300">{movie.overview}</p>
                  </div>

                  {/* Recommendations */}
                  {recommendations.length > 0 && (
                    <div>
                      <h2 className="mb-4 font-display text-xl font-bold text-white">
                        You Might Also Like
                      </h2>
                      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                        {recommendations.map((rec, index) => (
                          <motion.button
                            key={rec.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            whileHover={{ scale: 1.05 }}
                            onClick={() => onMovieClick(rec.id)}
                            className="group relative aspect-[2/3] overflow-hidden rounded-lg bg-cinema-gray"
                          >
                            {rec.poster_url && (
                              <Image
                                src={rec.poster_url}
                                alt={rec.title}
                                fill
                                className="object-cover transition-transform duration-300 group-hover:scale-110"
                                sizes="(max-width: 768px) 50vw, 33vw"
                              />
                            )}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                            <div className="absolute bottom-0 left-0 right-0 translate-y-full p-3 transition-transform group-hover:translate-y-0">
                              <p className="line-clamp-2 text-sm font-semibold text-white">
                                {rec.title}
                              </p>
                            </div>
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
