import { Geist, Geist_Mono } from 'next/font/google';
import AuthGuard from '@/components/auth-guard';
import AppSidebar from '@/components/app-sidebar';
import { Toaster } from '@/components/toaster';
import { PageTransition } from '@/components/transitions';
import { CommandPalette as EnhancedCommandPalette } from '@/components/enhanced-command-palette';
import { ErrorBoundary } from '@/components/error-boundary';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata = {
  title: 'AEIOU AI - Business Assistant',
  description: 'AI-powered business assistant for documents, tasks, and analytics',
  icons: {
    icon: '/logos/app-logo.svg',
    shortcut: '/logos/app-logo.svg',
    apple: '/logos/app-logo.svg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-[#fafafa]" suppressHydrationWarning>
        <AuthGuard>
          <div className="flex h-screen overflow-hidden">
            <AppSidebar />
            <main className="flex-1 min-w-0 overflow-auto transition-all duration-300 ease-out">
              <PageTransition>
                <ErrorBoundary>
                  {children}
                </ErrorBoundary>
              </PageTransition>
            </main>
          </div>
        </AuthGuard>
        <Toaster />
        <EnhancedCommandPalette />
      </body>
    </html>
  );
}
