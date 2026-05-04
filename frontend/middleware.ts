import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_PATHS = [
  '/',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-email',
  '/features',
  '/pricing',
  '/about',
  '/contact',
  '/privacy',
  '/terms',
];

const STATIC_ASSETS = ['/_next/', '/static/', '/logos/', '/images/', '/favicon.ico'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip static assets and API routes
  if (STATIC_ASSETS.some(p => pathname.startsWith(p)) || pathname.startsWith('/api/')) {
    return NextResponse.next();
  }

  // Add security headers to all responses
  const response = NextResponse.next();
  const headers = response.headers;

  headers.set('X-Frame-Options', 'DENY');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  // Check if path is public
  const isPublic = PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(`${p}/`));

  // Auth indicator: lightweight client-set cookie (not httpOnly, just a flag)
  // The actual JWT verification happens client-side in AuthGuard
  const hasAuthIndicator = request.cookies.has('aeiou-session');

  // Redirect unauthenticated users from protected routes
  if (!isPublic && !hasAuthIndicator) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users away from auth pages to app
  if (hasAuthIndicator && (pathname === '/login' || pathname === '/register')) {
    return NextResponse.redirect(new URL('/chat', request.url));
  }

  return response;
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
