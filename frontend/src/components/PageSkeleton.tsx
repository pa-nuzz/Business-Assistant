'use client';

import { DashboardSkeleton } from './skeletons/DashboardSkeleton';
import { ChatSkeleton } from './skeletons/ChatSkeleton';

interface PageSkeletonProps {
  type: 'dashboard' | 'chat' | 'documents' | 'tasks' | 'settings' | 'default';
}

export function PageSkeleton({ type }: PageSkeletonProps) {
  switch (type) {
    case 'dashboard':
      return <DashboardSkeleton />;
    case 'chat':
      return <ChatSkeleton />;
    case 'documents':
    case 'tasks':
    case 'settings':
    case 'default':
    default:
      return (
        <div className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center">
          <div className="animate-pulse flex flex-col items-center gap-4">
            <div className="h-12 w-48 bg-[var(--bg-elevated)] rounded" />
            <div className="h-4 w-32 bg-[var(--bg-subtle)] rounded" />
          </div>
        </div>
      );
  }
}
