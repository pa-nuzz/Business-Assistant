'use client';

import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';

const routeLabels: Record<string, string> = {
  '/': 'Home',
  '/chat': 'Chat',
  '/documents': 'Documents',
  '/dashboard': 'Dashboard',
  '/settings': 'Settings',
  '/login': 'Login',
  '/register': 'Register',
  '/forgot-password': 'Forgot Password',
  '/reset-password': 'Reset Password',
};

export function Breadcrumbs() {
  const pathname = usePathname();
  
  // Don't show breadcrumbs on auth pages or home
  if (pathname === '/' || pathname === '/login' || pathname === '/register') {
    return null;
  }
  
  // Get current route label
  const currentLabel = routeLabels[pathname] || 
    pathname.split('/').pop()?.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 
    'Page';

  return (
    <nav className="flex items-center gap-2 text-sm text-gray-500 mb-4">
      <a 
        href="/chat" 
        className="flex items-center gap-1 hover:text-gray-900 transition-colors"
      >
        <Home size={14} />
        <span>Home</span>
      </a>
      <ChevronRight size={14} className="text-gray-400" />
      <span className="text-gray-900 font-medium">{currentLabel}</span>
    </nav>
  );
}
