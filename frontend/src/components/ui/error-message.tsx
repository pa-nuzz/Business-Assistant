"use client";

import { AlertCircle, X } from "lucide-react";
import { useState } from "react";

interface ErrorMessageProps {
  error: string | Error | unknown;
  onDismiss?: () => void;
  className?: string;
}

/**
 * Standardized error message component
 * Handles various error types gracefully without exposing technical details
 */
export function ErrorMessage({ error, onDismiss, className = "" }: ErrorMessageProps) {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  // Extract user-friendly message from various error types
  const getErrorMessage = (err: unknown): string => {
    if (typeof err === "string") return err;
    if (err instanceof Error) return err.message;
    if (err && typeof err === "object") {
      // Check for common API error structures
      const errorObj = err as Record<string, unknown>;
      if (typeof errorObj.message === "string") return errorObj.message;
      if (typeof errorObj.error === "string") return errorObj.error;
      if (Array.isArray(errorObj.errors) && errorObj.errors.length > 0) {
        return String(errorObj.errors[0]);
      }
    }
    return "An unexpected error occurred. Please try again.";
  };

  // Sanitize message - remove technical details
  const sanitizeMessage = (msg: string): string => {
    // Remove JSON artifacts, object notation
    if (msg.startsWith("{") || msg.startsWith("[")) {
      return "An unexpected error occurred. Please try again.";
    }
    // Remove stack traces
    if (msg.includes("at ") && msg.includes("(http")) {
      return msg.split("at ")[0].trim();
    }
    // Limit length
    if (msg.length > 200) {
      return msg.substring(0, 200) + "...";
    }
    return msg;
  };

  const message = sanitizeMessage(getErrorMessage(error));

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  return (
    <div
      role="alert"
      className={`relative flex items-start gap-3 p-4 text-sm bg-red-50 border border-red-200 rounded-xl text-red-700 ${className}`}
    >
      <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">
        <p className="font-medium">Error</p>
        <p className="mt-1 text-red-600">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={handleDismiss}
          className="p-1 rounded-lg hover:bg-red-100 transition-colors flex-shrink-0"
          aria-label="Dismiss error"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

/**
 * Form error component for inline field errors
 */
export function FormError({ error }: { error: string | null }) {
  if (!error) return null;

  return (
    <p className="mt-1.5 text-sm text-red-600" role="alert">
      {error}
    </p>
  );
}
