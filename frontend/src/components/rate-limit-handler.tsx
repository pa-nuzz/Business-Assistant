"use client";

import { useState, useEffect, useCallback } from "react";
import { onRateLimit } from "@/lib/api";
import { RateLimitBanner } from "./rate-limit-banner";

interface RateLimitState {
  isRateLimited: boolean;
  retryAfter: number;
  scope: string;
  message: string;
  countdown: number;
}

export function RateLimitHandler() {
  const [rateLimit, setRateLimit] = useState<RateLimitState>({
    isRateLimited: false,
    retryAfter: 0,
    scope: "",
    message: "",
    countdown: 0,
  });

  const formatCountdown = useCallback((seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  }, []);

  useEffect(() => {
    // Listen for rate limit events from the API
    const unsubscribe = onRateLimit((info) => {
      setRateLimit({
        isRateLimited: true,
        retryAfter: info.retryAfter,
        scope: info.scope,
        message: info.message,
        countdown: info.retryAfter,
      });
    });

    return () => {
      unsubscribe();
    };
  }, []);

  // Countdown timer
  useEffect(() => {
    if (!rateLimit.isRateLimited || rateLimit.countdown <= 0) return;

    const interval = setInterval(() => {
      setRateLimit((prev) => {
        if (prev.countdown <= 1) {
          return {
            ...prev,
            isRateLimited: false,
            countdown: 0,
          };
        }
        return {
          ...prev,
          countdown: prev.countdown - 1,
        };
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [rateLimit.isRateLimited, rateLimit.countdown]);

  return (
    <RateLimitBanner
      isRateLimited={rateLimit.isRateLimited}
      retryAfterSeconds={rateLimit.countdown}
      scope={rateLimit.scope}
      message={rateLimit.message}
      formatCountdown={formatCountdown}
    />
  );
}
