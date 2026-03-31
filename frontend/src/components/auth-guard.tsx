'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { auth } from '@/lib/api';

const publicPaths = ['/login', '/register'];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const isPublic = publicPaths.includes(pathname);
    const isAuth = auth.isAuthenticated();

    if (!isAuth && !isPublic) {
      router.push('/login');
    } else if (isAuth && isPublic) {
      router.push('/chat');
    }
  }, [pathname, router]);

  return <>{children}</>;
}
