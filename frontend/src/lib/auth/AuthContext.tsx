'use client';

import React, { createContext, useContext, useRef, useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { initializeApiAuth } from '../api/client';

// ─── Types ───────────────────────────────────────────────────────────────────
interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  getToken: () => string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

// ─── Context ─────────────────────────────────────────────────────────────────
const AuthContext = createContext<AuthContextType | null>(null);

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  
  // SECURITY: Access token stored in useRef (memory only) - never localStorage
  const accessTokenRef = useRef<string | null>(null);
  
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Get token from memory
  const getToken = useCallback(() => accessTokenRef.current, []);

  // Refresh access token using httpOnly cookie
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const response = await axios.post(`${API_BASE}/auth/token/refresh/`, {}, {
        withCredentials: true, // Sends httpOnly refresh cookie
      });
      
      if (response.data.access) {
        accessTokenRef.current = response.data.access;
        return true;
      }
      return false;
    } catch {
      accessTokenRef.current = null;
      setUser(null);
      return false;
    }
  }, []);

  // On mount: try to restore session using refresh cookie
  useEffect(() => {
    const initAuth = async () => {
      const success = await refreshToken();
      if (success) {
        // Fetch user info
        try {
          const response = await axios.get(`${API_BASE}/user/`, {
            headers: { Authorization: `Bearer ${accessTokenRef.current}` },
            withCredentials: true,
          });
          setUser(response.data);
        } catch {
          // Silent fail - user info not critical
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [refreshToken]);

  // Login
  const login = useCallback(async (username: string, password: string) => {
    const response = await axios.post(`${API_BASE}/auth/login/`, {
      username,
      password,
    }, { withCredentials: true });

    if (response.data.access) {
      accessTokenRef.current = response.data.access;
      setUser(response.data.user);
    }
  }, []);

  // Logout
  const logout = useCallback(async () => {
    try {
      await axios.post(`${API_BASE}/auth/logout/`, {}, { withCredentials: true });
    } finally {
      accessTokenRef.current = null;
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  // Initialize API client with auth functions (after all callbacks defined)
  useEffect(() => {
    initializeApiAuth(getToken, refreshToken, logout);
  }, [getToken, refreshToken, logout]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!accessTokenRef.current,
    getToken,
    login,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook for consuming auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
