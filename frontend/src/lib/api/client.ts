import axios from 'axios';
import { useAuth } from '../auth/AuthContext';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
  withCredentials: true, // Sends httpOnly cookies
});

// Track auth functions (set after AuthProvider mounts)
let getTokenFn: (() => string | null) | null = null;
let refreshTokenFn: (() => Promise<boolean>) | null = null;
let logoutFn: (() => Promise<void>) | null = null;

// Initialize auth functions from AuthContext
export function initializeApiAuth(
  getToken: () => string | null,
  refreshToken: () => Promise<boolean>,
  logout: () => Promise<void>
) {
  getTokenFn = getToken;
  refreshTokenFn = refreshToken;
  logoutFn = logout;
}

// Request interceptor: attach access token from memory
api.interceptors.request.use(
  (config) => {
    if (getTokenFn) {
      const token = getTokenFn();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Network errors
    if (!error.response) {
      return Promise.reject(new Error('Network error: Backend not reachable'));
    }

    // 401 unauthorized - try refresh once
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (refreshTokenFn) {
        const refreshed = await refreshTokenFn();
        if (refreshed && getTokenFn) {
          const newToken = getTokenFn();
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
      }

      // Refresh failed - logout
      if (logoutFn) {
        await logoutFn();
      }
    }

    return Promise.reject(error);
  }
);

export default api;
