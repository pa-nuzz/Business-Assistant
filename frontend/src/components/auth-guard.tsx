'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { auth } from '@/lib/api';

const publicPaths = [
  '/',
  '/login',
  '/register',
  '/forgot-password',
  '/verify-email',
  '/reset-password',
  '/features',
  '/pricing',
  '/about',
  '/contact',
  '/privacy',
  '/terms',
];

function isPublicPath(path: string): boolean {
  if (!path) return false;
  const normalizedPath = path.replace(/\/$/, '') || '/';
  return publicPaths.some(publicPath => 
    normalizedPath === publicPath || 
    normalizedPath.startsWith(publicPath + '/')
  );
}

// Loading overlay component - only shows briefly during auth checks
function AuthLoadingOverlay() {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="20" y="50" width="8" height="30" rx="4" fill="#6366F1">
            <animate attributeName="height" values="30;20;35;30" dur="3s" repeatCount="indefinite" />
            <animate attributeName="y" values="50;60;45;50" dur="3s" repeatCount="indefinite" />
          </rect>
          <rect x="35" y="40" width="8" height="40" rx="4" fill="#8B5CF6">
            <animate attributeName="height" values="40;30;45;40" dur="2.5s" repeatCount="indefinite" />
            <animate attributeName="y" values="40;50;35;40" dur="2.5s" repeatCount="indefinite" />
          </rect>
          <rect x="50" y="30" width="8" height="50" rx="4" fill="#6366F1">
            <animate attributeName="height" values="50;35;55;50" dur="2s" repeatCount="indefinite" />
            <animate attributeName="y" values="30;45;25;30" dur="2s" repeatCount="indefinite" />
          </rect>
          <rect x="65" y="45" width="8" height="35" rx="4" fill="#8B5CF6">
            <animate attributeName="height" values="35;25;40;35" dur="2.7s" repeatCount="indefinite" />
            <animate attributeName="y" values="45;55;40;45" dur="2.7s" repeatCount="indefinite" />
          </rect>
          <rect x="80" y="55" width="8" height="25" rx="4" fill="#6366F1">
            <animate attributeName="height" values="25;15;30;25" dur="3.2s" repeatCount="indefinite" />
            <animate attributeName="y" values="55;65;50;55" dur="3.2s" repeatCount="indefinite" />
          </rect>
        </svg>
        <span className="text-slate-500 text-sm">Verifying...</span>
      </div>
    </div>
  );
}

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [authState, setAuthState] = useState<'checking' | 'ready' | 'redirecting'>('checking');

  // ── Initial mount: attempt to restore session from httpOnly cookie ──
  // This runs once. It ALWAYS tries refresh when accessToken is missing,
  // not just when the aeiou-session indicator cookie happens to exist.
  useEffect(() => {
    const restore = async () => {
      if (!pathname) return;

      const isPublic = isPublicPath(pathname);

      // If we already have a memory token, we're good
      if (auth.isAuthenticated()) {
        setAuthState('ready');
        return;
      }

      // Public pages don't need a token — just render them
      if (isPublic) {
        setAuthState('ready');
        return;
      }

      // Protected page + no memory token: try restoring from httpOnly refresh cookie
      try {
        await auth.refreshSession();
        setAuthState('ready');
      } catch {
        setAuthState('redirecting');
        router.replace('/login');
      }
    };

    restore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount

  // ── Fast path for pathname changes after initial check ──
  // Avoid re-checking cookies/async on every client-side navigation.
  useEffect(() => {
    if (authState === 'checking') return; // Still doing initial restore
    if (!pathname) return;

    const isPublic = isPublicPath(pathname);

    // Public pages: always render, never redirect authenticated users
    if (isPublic) {
      return;
    }

    // Protected page
    if (!auth.isAuthenticated()) {
      setAuthState('redirecting');
      router.replace('/login');
    }
    // If authenticated, stay ready — no state change needed
  }, [pathname, router, authState]);

  // Safety: fail closed on protected pages instead of rendering them unauthenticated.
  useEffect(() => {
    if (authState === 'ready') return;
    const timer = setTimeout(() => {
      if (pathname && !isPublicPath(pathname)) {
        setAuthState('redirecting');
        router.replace('/login');
      } else {
        setAuthState('ready');
      }
    }, 8000);
    return () => clearTimeout(timer);
  }, [authState, pathname, router]);

  if (authState !== 'ready') {
    // For public pages, show children immediately even during 'checking'
    // This prevents the login page from flashing the overlay
    if (pathname && isPublicPath(pathname)) {
      return <>{children}</>;
    }
    return <AuthLoadingOverlay />;
  }

  return <>{children}</>;
}
