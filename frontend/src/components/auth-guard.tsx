'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { auth } from '@/lib/api';

const publicPaths = ['/login', '/register', '/forgot-password', '/verify-email', '/reset-password'];

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
  const [isChecking, setIsChecking] = useState(false);
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    // Skip if pathname isn't ready yet
    if (!pathname) return;

    const isPublic = isPublicPath(pathname);
    const isAuth = auth.isAuthenticated();

    // Determine if we need to redirect
    const needsRedirect = (!isAuth && !isPublic) || (isAuth && isPublic);

    if (needsRedirect) {
      setIsChecking(true);
      
      // Perform redirect
      const timer = setTimeout(() => {
        if (!isAuth && !isPublic) {
          router.replace('/login');
        } else if (isAuth && isPublic) {
          router.replace('/chat');
        }
        setIsChecking(false);
        setHasChecked(true);
      }, 150);

      return () => clearTimeout(timer);
    } else {
      // No redirect needed, mark as checked
      setHasChecked(true);
      setIsChecking(false);
    }
  }, [pathname, router]);

  // Safety timeout: ensure we don't stay in checking state forever
  useEffect(() => {
    if (!isChecking) return;
    
    const safetyTimer = setTimeout(() => {
      setIsChecking(false);
      setHasChecked(true);
    }, 2000);

    return () => clearTimeout(safetyTimer);
  }, [isChecking]);

  // Don't render children until auth check is complete to prevent flash
  if (!hasChecked) {
    return <AuthLoadingOverlay />;
  }

  return <>{children}</>;
}
