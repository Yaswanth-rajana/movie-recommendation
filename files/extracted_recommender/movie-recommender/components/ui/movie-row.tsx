"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { MovieCard as MovieCardType } from "@/types/api";
import { MovieCard } from "./movie-card";

interface MovieRowProps {
  title: string;
  movies: MovieCardType[];
  onMovieClick: (movie: MovieCardType) => void;
}

export function MovieRow({ title, movies, onMovieClick }: MovieRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);

  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setShowLeftArrow(scrollLeft > 0);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    checkScroll();
    const scrollElement = scrollRef.current;
    scrollElement?.addEventListener("scroll", checkScroll);
    return () => scrollElement?.removeEventListener("scroll", checkScroll);
  }, [movies]);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const scrollAmount = scrollRef.current.clientWidth * 0.8;
      scrollRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      });
    }
  };

  if (movies.length === 0) return null;

  return (
    <div className="group/row relative mb-12">
      <h2 className="mb-4 font-display text-2xl font-bold text-white md:text-3xl">
        {title}
      </h2>

      <div className="relative">
        {/* Left Arrow */}
        {showLeftArrow && (
          <button
            onClick={() => scroll("left")}
            className="absolute left-0 top-0 z-20 flex h-full items-center bg-gradient-to-r from-cinema-black via-cinema-black/80 to-transparent pl-2 pr-8 opacity-0 transition-opacity group-hover/row:opacity-100"
            aria-label="Scroll left"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-black/50 backdrop-blur-sm hover:bg-black/70">
              <ChevronLeft className="h-8 w-8 text-white" />
            </div>
          </button>
        )}

        {/* Right Arrow */}
        {showRightArrow && (
          <button
            onClick={() => scroll("right")}
            className="absolute right-0 top-0 z-20 flex h-full items-center bg-gradient-to-l from-cinema-black via-cinema-black/80 to-transparent pl-8 pr-2 opacity-0 transition-opacity group-hover/row:opacity-100"
            aria-label="Scroll right"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-black/50 backdrop-blur-sm hover:bg-black/70">
              <ChevronRight className="h-8 w-8 text-white" />
            </div>
          </button>
        )}

        {/* Movie Cards */}
        <div
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {movies.map((movie, index) => (
            <div
              key={movie.id}
              className="w-[160px] flex-shrink-0 md:w-[200px] lg:w-[220px]"
            >
              <MovieCard
                movie={movie}
                onClick={() => onMovieClick(movie)}
                index={index}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
