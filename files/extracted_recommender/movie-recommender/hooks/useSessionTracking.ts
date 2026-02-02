"use client";

import { useEffect, useState } from "react";
import { getSessionId, api } from "@/lib/api";

export function useSessionTracking() {
  const [sessionId, setSessionId] = useState<string>("");

  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  const trackEvent = async (
    movieId: number,
    eventType: "click" | "like" | "dislike" | "impression"
  ) => {
    if (!sessionId) return;
    
    try {
      await api.trackEvent({ session_id: sessionId, movie_id: movieId, event_type: eventType });
    } catch (error) {
      console.error("Failed to track event:", error);
    }
  };

  return { sessionId, trackEvent };
}
