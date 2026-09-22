/**
 * Standardized Error Handling Utilities
 * Consistent patterns for error handling across the application
 */

import { toast } from 'sonner';
import { logger } from './logger';
import { AxiosApiError, getErrorMessage, isApiError } from '@/types/errors';

export interface ErrorHandlerOptions {
  /** Show toast notification (default: true) */
  showToast?: boolean;
  /** Log to console/logger (default: true) */
  logError?: boolean;
  /** Custom error message override */
  customMessage?: string;
  /** Error context for logging */
  context?: Record<string, unknown>;
}

/**
 * Handle API errors with consistent patterns
 */
export function handleApiError(
  error: unknown,
  options: ErrorHandlerOptions = {}
): string {
  const {
    showToast = true,
    logError = true,
    customMessage,
    context,
  } = options;

  const message = customMessage || getErrorMessage(error);

  // Log error
  if (logError) {
    logger.error('API Error', {
      message,
      error: error instanceof Error ? error : undefined,
      context,
    });
  }

  // Show toast
  if (showToast) {
    toast.error(message);
  }

  return message;
}

/**
 * Handle async operations with consistent error handling
 */
export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  options: ErrorHandlerOptions & {
    /** Success message to show on completion */
    successMessage?: string;
  } = {}
): Promise<T | null> {
  const { successMessage, ...errorOptions } = options;

  try {
    const result = await operation();
    
    if (successMessage) {
      toast.success(successMessage);
    }
    
    return result;
  } catch (error) {
    handleApiError(error, errorOptions);
    return null;
  }
}

/**
 * Type-safe error guard for API calls
 */
export function isAxiosError(error: unknown): error is AxiosApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    (error as AxiosApiError).message !== undefined
  );
}

/**
 * Extract HTTP status code from error
 */
export function getErrorStatus(error: unknown): number | undefined {
  if (isAxiosError(error)) {
    return error.response?.status;
  }
  return undefined;
}

/**
 * Check if error is a specific HTTP status
 */
export function isHttpError(error: unknown, status: number): boolean {
  return getErrorStatus(error) === status;
}

/**
 * Handle specific error codes with custom messages
 */
const ERROR_CODE_MESSAGES: Record<string, string> = {
  '401': 'Please sign in to continue',
  '403': 'You do not have permission to perform this action',
  '404': 'The requested resource was not found',
  '429': 'Too many requests. Please try again later.',
  '500': 'Server error. Please try again later.',
  '502': 'Service temporarily unavailable',
  '503': 'Service temporarily unavailable',
};

/**
 * Get user-friendly error message based on status code
 */
export function getFriendlyErrorMessage(error: unknown): string {
  const status = getErrorStatus(error);
  if (status && ERROR_CODE_MESSAGES[status.toString()]) {
    return ERROR_CODE_MESSAGES[status.toString()];
  }
  return getErrorMessage(error);
}