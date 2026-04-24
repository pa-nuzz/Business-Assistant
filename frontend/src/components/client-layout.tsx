'use client';

import { useEffect, useState } from 'react';
import { Toaster } from 'sonner';
import { ChatProvider } from '@/components/chat-context';
import { LoadingProvider } from '@/components/loading-context';
import AuthGuard from '@/components/auth-guard';
import { usePathname } from 'next/navigation';
import Sidebar from '@/components/sidebar-new';
import { CommandPalette } from '@/components/enhanced-command-palette';

const publicPaths = ['/login', '/register', '/forgot-password', '/verify-email', '/reset-password'];

// Loading skeleton - matches both collapsed and expanded sidebar states
function LoadingSkeleton({ showSidebar = false }: { showSidebar?: boolean }) {
  return (
    <div className="flex h-screen bg-white overflow-hidden">
      {showSidebar && (
        <div className="w-[72px] h-screen bg-slate-50 border-r border-slate-200 flex flex-col flex-shrink-0">
          {/* Collapsed logo skeleton */}
          <div className="h-16 flex items-center justify-center border-b border-slate-100">
            <div className="w-8 h-8 bg-slate-200 rounded-lg animate-pulse" />
          </div>
          {/* Nav items skeleton - icon only */}
          <div className="p-3 space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="w-12 h-12 mx-auto bg-slate-200 rounded-xl animate-pulse" />
            ))}
          </div>
        </div>
      )}
      <main className="flex-1 flex items-center justify-center min-w-0">
        <div className="flex flex-col items-center gap-4">
          {/* Animated logo */}
          <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
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
          <p className="text-slate-500 text-sm font-medium">Loading AEIOU AI...</p>
        </div>
      </main>
    </div>
  );
}

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [hasError, setHasError] = useState(false);
  const pathname = usePathname();

  // ALL hooks must be called before any conditional returns
  useEffect(() => {
    // Mark as mounted immediately on client
    try {
      setMounted(true);
    } catch (e) {
      console.error('[ClientLayout] Error during mount:', e);
      setMounted(true); // Force it anyway
    }
  }, []);

  // Unblock safety timer - forces render after 2s no matter what
  useEffect(() => {
    const unblockTimer = setTimeout(() => {
      setMounted(true);
    }, 2000);

    return () => clearTimeout(unblockTimer);
  }, []);

  // Compute after all hooks are called
  const isPublicPage = pathname ? publicPaths.some((path) => pathname.startsWith(path)) : false;

  // Error boundary fallback - after all hooks
  if (hasError) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-slate-900 mb-2">Something went wrong</h2>
          <p className="text-slate-500 mb-4">Please refresh the page to continue</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  // Show loading skeleton - after all hooks
  if (!mounted) {
    return (
      <div className="flex h-screen bg-white overflow-hidden">
        <main className="flex-1 flex items-center justify-center min-w-0">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-slate-200 border-t-indigo-600 rounded-full animate-spin" />
            <p className="text-slate-500 text-sm font-medium">Loading AEIOU AI...</p>
            <p className="text-slate-400 text-xs">If this persists, check console for errors</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <LoadingProvider>
      <ChatProvider>
        <AuthGuard>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 min-w-0 overflow-auto relative">
              {children}
            </main>
          </div>
          <CommandPalette />
          <Toaster
            position="top-right"
            richColors
            closeButton
            toastOptions={{
              style: {
                fontSize: '14px',
              },
            }}
          />
        </AuthGuard>
      </ChatProvider>
    </LoadingProvider>
  );
}
