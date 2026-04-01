'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { auth } from '@/lib/api';

const publicPaths = ['/login', '/register', '/forgot-password'];

function isPublicPath(path: string): boolean {
  // Normalize path - remove trailing slash
  const normalizedPath = path.replace(/\/$/, '') || '/';
  return publicPaths.some(publicPath => 
    normalizedPath === publicPath || 
    normalizedPath.startsWith(publicPath + '/')
  );
}

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);
  const isProcessingRef = useRef(false);

  useEffect(() => {
    // Prevent multiple simultaneous processing
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;
    
    const checkAuth = () => {
      const isPublic = isPublicPath(pathname);
      const isAuth = auth.isAuthenticated();

      if (!isAuth && !isPublic) {
        // Not authenticated and on protected route -> redirect to login
        router.replace('/login');
        return false;
      } else if (isAuth && isPublic) {
        // Authenticated and on public route -> redirect to chat
        router.replace('/chat');
        return false;
      }
      return true;
    };

    const shouldRender = checkAuth();
    
    if (shouldRender) {
      // Small delay for smooth transition
      const timer = setTimeout(() => {
        setIsReady(true);
        isProcessingRef.current = false;
      }, 50);
      return () => clearTimeout(timer);
    } else {
      isProcessingRef.current = false;
    }
  }, [pathname, router]);

  // Show loading indicator while checking auth instead of white screen
  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#fafafa]">
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-5 h-5 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
          <span className="text-sm">Loading...</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
