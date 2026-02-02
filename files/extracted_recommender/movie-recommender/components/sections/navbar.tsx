"use client";

import { useState, useEffect } from "react";
import { Search, Film } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface NavbarProps {
  onSearchClick: () => void;
}

export function Navbar({ onSearchClick }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn(
        "fixed left-0 right-0 top-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-cinema-black/80 backdrop-blur-xl shadow-2xl"
          : "bg-transparent"
      )}
    >
      <div className="container mx-auto px-6 md:px-12">
        <div className="flex h-16 items-center justify-between md:h-20">
          {/* Logo */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cinema-accent">
              <Film className="h-6 w-6 text-white" />
            </div>
            <span className="hidden font-display text-2xl font-black text-white sm:block">
              CINEMATIC
            </span>
          </motion.div>

          {/* Navigation Items */}
          <div className="flex items-center gap-6">
            <div className="hidden items-center gap-8 font-display text-sm font-semibold text-gray-300 md:flex">
              <button className="transition-colors hover:text-white">Home</button>
              <button className="transition-colors hover:text-white">Movies</button>
              <button className="transition-colors hover:text-white">Popular</button>
              <button className="transition-colors hover:text-white">My List</button>
            </div>

            {/* Search Button */}
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onSearchClick}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 backdrop-blur-sm transition-colors hover:bg-white/20"
              aria-label="Search"
            >
              <Search className="h-5 w-5 text-white" />
            </motion.button>
          </div>
        </div>
      </div>
    </motion.nav>
  );
}
