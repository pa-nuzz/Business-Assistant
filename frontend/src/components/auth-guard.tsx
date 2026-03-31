'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { auth } from '@/lib/api';

const publicPaths = ['/login', '/register'];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const isPublic = publicPaths.includes(pathname);
    const isAuth = auth.isAuthenticated();

    if (!isAuth && !isPublic) {
      router.push('/login');
    } else if (isAuth && isPublic) {
      router.push('/chat');
    } else {
      setIsReady(true);
    }
  }, [pathname, router]);

  // Show nothing while redirecting
  if (!isReady) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: 'var(--surface-1)'
      }}>
        <div 
          className="animate-pulse-slow"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            backgroundColor: 'var(--accent-blue)',
          }}
        />
      </div>
    );
  }

  // On login page, don't wrap in sidebar layout
  if (publicPaths.includes(pathname)) {
    return <>{children}</>;
  }

  return <>{children}</>;
}
