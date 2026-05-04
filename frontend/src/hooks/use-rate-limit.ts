"use client";

import { useState, useCallback, useEffect } from "react";
import { AxiosError } from "axios";
import { toast } from "sonner";

interface RateLimitInfo {
  isRateLimited: boolean;
  retryAfter: number; // seconds
  scope: string;
  message: string;
}

interface RateLimitState extends RateLimitInfo {
  countdown: number;
}

export function useRateLimit() {
  const [rateLimit, setRateLimit] = useState<RateLimitState>({
    isRateLimited: false,
    retryAfter: 0,
    scope: "",
    message: "",
    countdown: 0,
  });

  const parseRateLimitError = useCallback((error: AxiosError): RateLimitInfo | null => {
    if (error.response?.status !== 429) {
      return null;
    }

    const data = error.response?.data as { 
      error?: string; 
      detail?: string;
      retry_after?: number;
      scope?: string;
    };

    const retryAfter = data?.retry_after || 
      parseInt(error.response?.headers["retry-after"] || "60", 10);
    
    const scope = data?.scope || "standard";
    const message = data?.error || data?.detail || "Rate limit exceeded";

    return {
      isRateLimited: true,
      retryAfter,
      scope,
      message,
    };
  }, []);

  const handleRateLimitError = useCallback((error: AxiosError) => {
    const info = parseRateLimitError(error);
    if (!info) return false;

    setRateLimit({
      ...info,
      countdown: info.retryAfter,
    });

    // Show appropriate message based on scope
    const scopeMessages: Record<string, string> = {
      upload: "Upload limit reached",
      auth: "Too many attempts",
      strict: "Operation limit reached",
      burst: "Too many requests",
      standard: "Rate limit exceeded",
    };

    const scopeMessage = scopeMessages[info.scope] || "Rate limit exceeded";
    
    toast.error(scopeMessage, {
      description: info.message,
      duration: 5000,
    });

    return true;
  }, [parseRateLimitError]);

  const clearRateLimit = useCallback(() => {
    setRateLimit({
      isRateLimited: false,
      retryAfter: 0,
      scope: "",
      message: "",
      countdown: 0,
    });
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

  const formatCountdown = useCallback((seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  }, []);

  return {
    rateLimit,
    handleRateLimitError,
    clearRateLimit,
    formatCountdown,
    isRateLimited: rateLimit.isRateLimited,
    retryAfterSeconds: rateLimit.countdown,
  };
}
