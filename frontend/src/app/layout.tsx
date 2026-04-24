import type { Metadata, Viewport } from 'next';
import { Syne, DM_Sans } from 'next/font/google';
import './globals.css';
import '@/styles/tokens.css';
import { ClientLayout } from '@/components/client-layout';
import { ErrorBoundary } from '@/components/error-boundary';

// Display font for headlines
const syne = Syne({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['400', '600', '700', '800'],
});

// Body font for UI and content
const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: 'AEIOU AI - Your Business Assistant',
  description: 'AI-powered business assistant for managing tasks, documents, and conversations',
  icons: {
    icon: '/logos/app-logo.svg',
    shortcut: '/favicon.ico',
    apple: '/logos/app-logo.svg',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#6C63FF',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${syne.variable} ${dmSans.variable} h-full antialiased`}>
      <body className="min-h-full bg-[var(--bg-base)] text-[var(--text-primary)] font-sans">
        <ErrorBoundary>
          <ClientLayout>{children}</ClientLayout>
        </ErrorBoundary>
      </body>
    </html>
  );
}
