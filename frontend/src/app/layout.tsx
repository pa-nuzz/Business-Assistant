'use client';

import { Geist, Geist_Mono } from 'next/font/google';
import AuthGuard from '@/components/auth-guard';
import AppSidebar from '@/components/app-sidebar';
import { Toaster } from '@/components/toaster';
import { PageTransition } from '@/components/transitions';
import { CommandPalette } from '@/components/command-palette';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-[#fafafa]">
        <AuthGuard>
          <div className="flex h-screen overflow-hidden">
            <AppSidebar />
            <main className="flex-1 min-w-0 overflow-auto transition-all duration-300 ease-out">
              <PageTransition>
                {children}
              </PageTransition>
            </main>
          </div>
        </AuthGuard>
        <Toaster />
        <CommandPalette />
      </body>
    </html>
  );
}
