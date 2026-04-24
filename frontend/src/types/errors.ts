// Error type definitions

// API error response structure
export interface ApiErrorResponse {
  error?: string;
  message?: string;
  detail?: string;
  code?: string;
  // Field-specific validation errors (Django returns these as arrays)
  username?: string[];
  email?: string[];
  password?: string[];
  [key: string]: string | string[] | undefined;
}

// Axios error with our API response structure
export interface AxiosApiError extends Error {
  response?: {
    data?: ApiErrorResponse;
    status?: number;
    statusText?: string;
  };
  request?: unknown;
  config?: unknown;
}

// Type guard for API errors
export function isApiError(error: unknown): error is AxiosApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as Error).message === 'string'
  );
}

// Extract error message from API error
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return (
      error.response?.data?.error ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    );
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
}
