"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Loader2 } from "lucide-react";
import Image from "next/image";
import { api } from "@/lib/api";
import { debounce } from "@/lib/utils";
import { MovieCard } from "@/types/api";

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMovieClick: (movie: MovieCard) => void;
}

export function SearchModal({ isOpen, onClose, onMovieClick }: SearchModalProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MovieCard[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Debounced search function
  const searchMovies = useCallback(
    debounce(async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const movies = await api.searchMovies(searchQuery, 10);
        setResults(movies);
      } catch (error) {
        console.error("Search failed:", error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    []
  );

  useEffect(() => {
    searchMovies(query);
  }, [query, searchMovies]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (!isOpen) {
          // Open search modal
        }
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.2 }}
            className="fixed left-1/2 top-20 z-50 w-full max-w-2xl -translate-x-1/2 px-4"
          >
            <div className="overflow-hidden rounded-2xl bg-cinema-dark shadow-2xl">
              {/* Search Input */}
              <div className="flex items-center gap-4 border-b border-white/10 px-6 py-4">
                <Search className="h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search for movies..."
                  className="flex-1 bg-transparent font-sans text-lg text-white placeholder:text-gray-500 focus:outline-none"
                  autoFocus
                />
                {isLoading && <Loader2 className="h-5 w-5 animate-spin text-gray-400" />}
                <button
                  onClick={onClose}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 transition-colors hover:bg-white/20"
                >
                  <X className="h-4 w-4 text-white" />
                </button>
              </div>

              {/* Results */}
              <div className="max-h-[60vh] overflow-y-auto">
                {query.trim() && results.length === 0 && !isLoading && (
                  <div className="py-12 text-center text-gray-500">
                    No movies found for "{query}"
                  </div>
                )}

                {results.length > 0 && (
                  <div className="p-4">
                    {results.map((movie) => (
                      <motion.button
                        key={movie.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        whileHover={{ backgroundColor: "rgba(255, 255, 255, 0.05)" }}
                        onClick={() => {
                          onMovieClick(movie);
                          onClose();
                        }}
                        className="flex w-full items-center gap-4 rounded-lg p-3 text-left transition-colors"
                      >
                        {/* Poster */}
                        <div className="relative h-20 w-14 flex-shrink-0 overflow-hidden rounded bg-cinema-gray">
                          {movie.poster_url ? (
                            <Image
                              src={movie.poster_url}
                              alt={movie.title}
                              fill
                              className="object-cover"
                              sizes="56px"
                            />
                          ) : (
                            <div className="flex h-full items-center justify-center text-xs text-gray-600">
                              No Image
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <h3 className="mb-1 truncate font-display font-semibold text-white">
                            {movie.title}
                          </h3>
                          <div className="flex items-center gap-2 text-sm text-gray-400">
                            {movie.release_date && (
                              <span>{new Date(movie.release_date).getFullYear()}</span>
                            )}
                            <span>⭐ {movie.vote_average.toFixed(1)}</span>
                          </div>
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>

              {/* Hint */}
              {!query && (
                <div className="border-t border-white/10 px-6 py-3 text-center text-sm text-gray-500">
                  Start typing to search for movies
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
