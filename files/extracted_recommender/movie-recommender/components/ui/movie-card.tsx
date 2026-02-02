"use client";

import { motion } from "framer-motion";
import { Star } from "lucide-react";
import Image from "next/image";
import { MovieCard as MovieCardType } from "@/types/api";
import { formatRating, formatYear } from "@/lib/utils";

interface MovieCardProps {
  movie: MovieCardType;
  onClick: () => void;
  index?: number;
}

export function MovieCard({ movie, onClick, index = 0 }: MovieCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      whileHover={{ scale: 1.05, zIndex: 10 }}
      className="group relative cursor-pointer"
      onClick={onClick}
    >
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-cinema-gray">
        {movie.poster_url ? (
          <Image
            src={movie.poster_url}
            alt={movie.title}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-110"
            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 20vw"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-gray-600">
            No Image
          </div>
        )}

        {/* Gradient overlay on hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

        {/* Info overlay */}
        <div className="absolute bottom-0 left-0 right-0 translate-y-full p-4 transition-transform duration-300 group-hover:translate-y-0">
          <h3 className="mb-1 line-clamp-2 font-display text-sm font-bold text-white">
            {movie.title}
          </h3>
          <div className="flex items-center gap-2 text-xs text-gray-300">
            {movie.release_date && (
              <span>{formatYear(movie.release_date)}</span>
            )}
            <div className="flex items-center gap-1">
              <Star className="h-3 w-3 fill-cinema-gold text-cinema-gold" />
              <span className="font-semibold">{formatRating(movie.vote_average)}</span>
            </div>
          </div>
        </div>

        {/* Rating badge (always visible) */}
        <div className="absolute right-2 top-2 flex items-center gap-1 rounded-full bg-black/70 px-2 py-1 backdrop-blur-sm">
          <Star className="h-3 w-3 fill-cinema-gold text-cinema-gold" />
          <span className="text-xs font-bold text-white">
            {formatRating(movie.vote_average)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
