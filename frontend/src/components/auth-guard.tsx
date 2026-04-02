'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { auth } from '@/lib/api';
import { useLoading } from './loading-context';

const publicPaths = ['/login', '/register', '/forgot-password', '/verify-email', '/reset-password'];

function isPublicPath(path: string): boolean {
  const normalizedPath = path.replace(/\/$/, '') || '/';
  return publicPaths.some(publicPath => 
    normalizedPath === publicPath || 
    normalizedPath.startsWith(publicPath + '/')
  );
}

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { showLoading, hideLoading } = useLoading();

  useEffect(() => {
    const isPublic = isPublicPath(pathname);
    const isAuth = auth.isAuthenticated();

    // Show loading before redirect
    if ((!isAuth && !isPublic) || (isAuth && isPublic)) {
      showLoading();
    }

    if (!isAuth && !isPublic) {
      // Not logged in, trying to access protected page
      // Small delay to let loading screen render before navigation
      setTimeout(() => {
        router.replace('/login');
      }, 100);
      // Hide loading after redirect completes
      setTimeout(() => hideLoading(), 700);
    } else if (isAuth && isPublic) {
      // Logged in but on public page
      // Small delay to let loading screen render before navigation
      setTimeout(() => {
        router.replace('/chat');
      }, 100);
      // Hide loading after redirect completes
      setTimeout(() => hideLoading(), 700);
    } else {
      // No redirect needed
      hideLoading();
    }
  }, [pathname, router, showLoading, hideLoading]);

  return <>{children}</>;
}
