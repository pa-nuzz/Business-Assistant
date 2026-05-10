'use client';

import { useState, useEffect } from 'react';

/**
 * Hook to track component mount state.
 * Use this to prevent hydration mismatches in components that use
 * browser-only APIs (window, localStorage, document, etc.)
 * 
 * @returns boolean - true after component mounts on client
 * 
 * @example
 * const mounted = useMounted();
 * if (!mounted) return <Skeleton />;
 * return <ComponentUsingWindow />;
 */
export function useMounted(): boolean {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted;
}

/**
 * Hook to safely access localStorage with SSR safety.
 * Returns null during SSR, actual value after mount.
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(initialValue);
  const mounted = useMounted();

  useEffect(() => {
    if (!mounted) return;
    
    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        setValue(JSON.parse(item));
      }
    } catch {
      // Silent fail - localStorage not available
    }
  }, [key, mounted]);

  const setStoredValue = (newValue: T) => {
    setValue(newValue);
    if (mounted) {
      try {
        window.localStorage.setItem(key, JSON.stringify(newValue));
      } catch {
        // Silent fail - localStorage not available
      }
    }
  };

  return [value, setStoredValue];
}
