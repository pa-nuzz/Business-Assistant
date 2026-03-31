'use client';

import { useState } from 'react';
import LoadingScreen from '@/components/loading-screen';
import { Geist, Geist_Mono } from 'next/font/google';
import AuthGuard from '@/components/auth-guard';
import AppSidebar from '@/components/app-sidebar';
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
  const [loading, setLoading] = useState(true);

  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-[#fafafa]">
        {loading && <LoadingScreen onComplete={() => setLoading(false)} minDuration={2500} />}
        <AuthGuard>
          <div className="flex h-screen overflow-hidden">
            <AppSidebar />
            <main className="flex-1 min-w-0 overflow-auto animate-fade-in">
              {children}
            </main>
          </div>
        </AuthGuard>
      </body>
    </html>
  );
}
