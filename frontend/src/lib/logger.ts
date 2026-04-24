// Structured logging utility
// Replaces console.log with environment-aware logging

interface Logger {
  debug: (msg: string, data?: unknown) => void;
  info: (msg: string, data?: unknown) => void;
  warn: (msg: string, data?: unknown) => void;
  error: (msg: string, error?: unknown) => void;
}

const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';

/**
 * Safe stringify for circular objects
 */
function safeStringify(data: unknown): string {
  try {
    return JSON.stringify(data);
  } catch {
    return '[Circular or Unserializable]';
  }
}

/**
 * Send error to monitoring service (Sentry)
 * Only called in production when Sentry is configured
 */
function reportToSentry(message: string, error?: unknown) {
  if (isProduction && typeof window !== 'undefined') {
    const win = window as Window & { Sentry?: { captureException: (e: unknown, ctx?: unknown) => void } };
    if (win.Sentry) {
      win.Sentry.captureException(error, {
        extra: { message, data: error ? safeStringify(error) : undefined },
      });
    }
  }
}

export const logger: Logger = {
  debug: (msg: string, data?: unknown) => {
    if (isDevelopment) {
      console.debug(`[AEIOU:DEBUG] ${msg}`, data);
    }
  },

  info: (msg: string, data?: unknown) => {
    if (isDevelopment) {
      console.info(`[AEIOU:INFO] ${msg}`, data);
    }
    // In production, could send to analytics/monitoring
  },

  warn: (msg: string, data?: unknown) => {
    if (isDevelopment) {
      console.warn(`[AEIOU:WARN] ${msg}`, data);
    }
    // In production, could send to monitoring
  },

  error: (msg: string, error?: unknown) => {
    if (isDevelopment) {
      console.error(`[AEIOU:ERROR] ${msg}`, error);
    }
    
    // Always report to Sentry in production
    if (isProduction) {
      reportToSentry(msg, error);
    }
  },
};

export default logger;
