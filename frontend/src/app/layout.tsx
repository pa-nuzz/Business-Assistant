import { Geist, Geist_Mono } from 'next/font/google';
import AuthGuard from '@/components/auth-guard';
import ConditionalSidebar from '@/components/conditional-sidebar';
import { Toaster } from '@/components/toaster';
import { CommandPalette as EnhancedCommandPalette } from '@/components/enhanced-command-palette';
import { ErrorBoundary } from '@/components/error-boundary';
import LoadingScreen from '@/components/loading-screen';
import { LoadingProvider } from '@/components/loading-context';
import { ChatProvider } from '@/components/chat-context';
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
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`} style={{background:'linear-gradient(135deg,#dbeafe 0%,#eff6ff 50%,#e0f2fe 100%)'}}>
      <head>
        <style>{`html,body{background:linear-gradient(135deg,#dbeafe 0%,#eff6ff 50%,#e0f2fe 100%) !important}`}</style>
      </head>
      <body className="min-h-full flex flex-col" style={{background:'linear-gradient(135deg,#dbeafe 0%,#eff6ff 50%,#e0f2fe 100%)'}} suppressHydrationWarning>
        <LoadingProvider>
          <ChatProvider>
            <LoadingScreen>
              <AuthGuard>
                <div className="flex h-screen overflow-hidden">
                  <ConditionalSidebar />
                  <main className="flex-1 min-w-0 overflow-auto transition-all duration-300 ease-out">
                    <ErrorBoundary>
                      {children}
                    </ErrorBoundary>
                  </main>
                </div>
                <EnhancedCommandPalette />
              </AuthGuard>
              <Toaster />
            </LoadingScreen>
          </ChatProvider>
        </LoadingProvider>
      </body>
    </html>
  );
}
