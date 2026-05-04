"use client";

import { AlertCircle, Clock, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface RateLimitBannerProps {
  isRateLimited: boolean;
  retryAfterSeconds: number;
  scope: string;
  message?: string;
  formatCountdown: (seconds: number) => string;
}

const scopeLabels: Record<string, string> = {
  upload: "Uploads",
  auth: "Authentication",
  strict: "Heavy Operations",
  burst: "Rapid Requests",
  standard: "API Requests",
};

const scopeDescriptions: Record<string, string> = {
  upload: "You've reached your upload limit for this time period.",
  auth: "Too many authentication attempts. Please wait before trying again.",
  strict: "This operation has strict limits. Consider upgrading for more capacity.",
  burst: "You're making requests too quickly. Slow down a bit.",
  standard: "You've reached the request limit for your plan.",
};

export function RateLimitBanner({
  isRateLimited,
  retryAfterSeconds,
  scope,
  message,
  formatCountdown,
}: RateLimitBannerProps) {
  if (!isRateLimited) return null;

  const scopeLabel = scopeLabels[scope] || "Requests";
  const description = message || scopeDescriptions[scope] || "Rate limit exceeded";

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-[400px] z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
      <div className="bg-amber-50 border border-amber-200 rounded-lg shadow-lg p-4 dark:bg-amber-950/30 dark:border-amber-900/50">
        <div className="flex items-start gap-3">
          <div className="h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0 dark:bg-amber-900/50">
            <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm text-amber-900 dark:text-amber-100">
              {scopeLabel} Limited
            </h4>
            <p className="text-sm text-amber-700 dark:text-amber-200 mt-1">
              {description}
            </p>
            
            {/* Countdown Timer */}
            <div className="flex items-center gap-2 mt-3 text-sm text-amber-800 dark:text-amber-300">
              <Clock className="h-4 w-4" />
              <span>Resets in {formatCountdown(retryAfterSeconds)}</span>
            </div>

            {/* Upgrade CTA */}
            <div className="mt-4 pt-3 border-t border-amber-200 dark:border-amber-900/50">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm">
                  <Zap className="h-4 w-4 text-primary" />
                  <span className="text-amber-800 dark:text-amber-200">
                    Need more capacity?
                  </span>
                </div>
                <Link href="/pricing">
                  <Button size="sm" variant="default" className="h-8 text-xs">
                    Upgrade
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
