'use client';

import { usePathname } from 'next/navigation';
import AppSidebar from './app-sidebar';

const publicPaths = ['/login', '/register', '/forgot-password', '/verify-email', '/reset-password'];

export default function ConditionalSidebar() {
  const pathname = usePathname();
  const isPublicPage = publicPaths.some((path) => pathname?.startsWith(path));

  if (isPublicPage) {
    return null;
  }

  return <AppSidebar />;
}
