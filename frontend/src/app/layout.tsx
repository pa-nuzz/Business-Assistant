import type { Metadata, Viewport } from 'next';
import './globals.css';
import '@/styles/tokens.css';
import { ClientLayout } from '@/components/client-layout';
import { ErrorBoundary } from '@/components/error-boundary';

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
    <html lang="en" className="h-full antialiased" data-scroll-behavior="smooth">
      <body className="min-h-full bg-background text-foreground font-sans">
        <ErrorBoundary>
          <ClientLayout>{children}</ClientLayout>
        </ErrorBoundary>
      </body>
    </html>
  );
}
