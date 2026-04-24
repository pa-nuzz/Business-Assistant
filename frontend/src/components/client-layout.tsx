'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Toaster } from 'sonner';
import { ChatProvider } from '@/components/chat-context';
import { LoadingProvider } from '@/components/loading-context';
import AuthGuard from '@/components/auth-guard';
import { usePathname } from 'next/navigation';

// Dynamic imports for code splitting
const Sidebar = dynamic(() => import('@/components/sidebar-new'), {
  ssr: false,
  loading: () => <div className="w-[280px] h-screen bg-slate-50 border-r border-slate-200" />
});

const CommandPalette = dynamic(() => import('@/components/enhanced-command-palette').then(mod => mod.CommandPalette), {
  ssr: false
});

const publicPaths = ['/login', '/register', '/forgot-password', '/verify-email', '/reset-password'];

// Loading skeleton component with proper branding
function LoadingSkeleton({ showSidebar = false }: { showSidebar?: boolean }) {
  return (
    <div className="flex h-screen bg-white">
      {showSidebar && (
        <div className="w-[280px] h-screen bg-slate-50 border-r border-slate-200 flex flex-col">
          {/* Logo skeleton */}
          <div className="h-16 flex items-center px-4 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-slate-200 rounded-lg animate-pulse" />
              <div className="w-24 h-5 bg-slate-200 rounded animate-pulse" />
            </div>
          </div>
          {/* Nav items skeleton */}
          <div className="p-4 space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-slate-100 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      )}
      <main className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          {/* Animated logo */}
          <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="50" width="8" height="30" rx="4" fill="#E2E8F0">
              <animate attributeName="height" values="30;20;35;30" dur="3s" repeatCount="indefinite" />
              <animate attributeName="y" values="50;60;45;50" dur="3s" repeatCount="indefinite" />
            </rect>
            <rect x="35" y="40" width="8" height="40" rx="4" fill="#CBD5E1">
              <animate attributeName="height" values="40;30;45;40" dur="2.5s" repeatCount="indefinite" />
              <animate attributeName="y" values="40;50;35;40" dur="2.5s" repeatCount="indefinite" />
            </rect>
            <rect x="50" y="30" width="8" height="50" rx="4" fill="#E2E8F0">
              <animate attributeName="height" values="50;35;55;50" dur="2s" repeatCount="indefinite" />
              <animate attributeName="y" values="30;45;25;30" dur="2s" repeatCount="indefinite" />
            </rect>
            <rect x="65" y="45" width="8" height="35" rx="4" fill="#CBD5E1">
              <animate attributeName="height" values="35;25;40;35" dur="2.7s" repeatCount="indefinite" />
              <animate attributeName="y" values="45;55;40;45" dur="2.7s" repeatCount="indefinite" />
            </rect>
            <rect x="80" y="55" width="8" height="25" rx="4" fill="#E2E8F0">
              <animate attributeName="height" values="25;15;30;25" dur="3.2s" repeatCount="indefinite" />
              <animate attributeName="y" values="55;65;50;55" dur="3.2s" repeatCount="indefinite" />
            </rect>
          </svg>
          <p className="text-slate-400 text-sm font-medium">Loading AEIOU AI...</p>
        </div>
      </main>
    </div>
  );
}

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [hasError, setHasError] = useState(false);
  const pathname = usePathname();
  
  // Handle hydration safely - pathname may be null during initial render
  const isPublicPage = pathname ? publicPaths.some((path) => pathname.startsWith(path)) : false;

  useEffect(() => {
    // Mark as mounted after hydration completes
    setMounted(true);
    
    // Safety timeout: force render after 3 seconds even if something is stuck
    const safetyTimer = setTimeout(() => {
      if (!mounted) {
        console.warn('[ClientLayout] Safety timeout triggered - forcing render');
        setMounted(true);
      }
    }, 3000);
    
    return () => clearTimeout(safetyTimer);
  }, []);

  // Error boundary fallback
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

  // During SSR/hydration: show skeleton that matches server render
  // This prevents hydration mismatch by not rendering different content on server vs client
  if (!mounted) {
    return <LoadingSkeleton showSidebar={!isPublicPage} />;
  }

  return (
    <LoadingProvider>
      <ChatProvider>
        <AuthGuard>
          <div className="flex h-screen overflow-hidden">
            {!isPublicPage && <Sidebar />}
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
