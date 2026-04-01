'use client';

import { motion } from 'framer-motion';

interface PageSkeletonProps {
  type?: 'chat' | 'documents' | 'tasks' | 'dashboard' | 'settings';
}

export function PageSkeleton({ type = 'chat' }: PageSkeletonProps) {
  const renderChatSkeleton = () => (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-background">
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="flex justify-end">
            <div className="skeleton w-3/4 h-12 rounded-2xl rounded-br-md" />
          </div>
          <div className="flex justify-start">
            <div className="skeleton w-full h-24 rounded-2xl" />
          </div>
          <div className="flex justify-end">
            <div className="skeleton w-1/2 h-12 rounded-2xl rounded-br-md" />
          </div>
          <div className="flex justify-start">
            <div className="skeleton w-3/4 h-20 rounded-2xl" />
          </div>
        </div>
      </div>
      <div className="border-t border-border bg-background px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="bg-card border border-border rounded-xl h-24 skeleton" />
        </div>
      </div>
    </div>
  );

  const renderDocumentsSkeleton = () => (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="skeleton w-32 h-8 mb-2" />
            <div className="skeleton w-48 h-4" />
          </div>
          <div className="skeleton w-28 h-10 rounded-lg" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center p-4 bg-card rounded-xl border border-border">
              <div className="skeleton w-12 h-12 rounded-xl mr-4" />
              <div className="flex-1">
                <div className="skeleton w-1/2 h-5 mb-2" />
                <div className="skeleton w-1/3 h-3" />
              </div>
              <div className="skeleton w-16 h-6 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTasksSkeleton = () => (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="skeleton w-24 h-8 mb-2" />
            <div className="skeleton w-40 h-4" />
          </div>
          <div className="skeleton w-28 h-10 rounded-xl" />
        </div>
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-5 bg-card rounded-xl border border-border">
              <div className="skeleton w-12 h-10 mb-2" />
              <div className="skeleton w-16 h-4" />
            </div>
          ))}
        </div>
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center p-4 bg-card rounded-xl border border-border">
              <div className="skeleton w-6 h-6 rounded-full mr-3" />
              <div className="flex-1 skeleton h-5" />
              <div className="skeleton w-16 h-6 rounded-md" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderDashboardSkeleton = () => (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <div className="skeleton w-32 h-8 mb-2" />
          <div className="skeleton w-48 h-4" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="p-5 bg-card rounded-xl border border-border">
              <div className="skeleton w-24 h-3 mb-2" />
              <div className="skeleton w-32 h-8" />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 bg-card rounded-xl border border-border">
            <div className="skeleton w-32 h-5 mb-4" />
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="skeleton w-20 h-8 rounded-lg" />
              ))}
            </div>
          </div>
          <div className="p-6 bg-card rounded-xl border border-border">
            <div className="skeleton w-24 h-5 mb-4" />
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="skeleton w-6 h-6 rounded-full" />
                  <div className="flex-1 skeleton h-4" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSettingsSkeleton = () => (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="skeleton w-24 h-8 mb-2" />
        <div className="skeleton w-64 h-4" />
      </div>
      <div className="border-b border-gray-200 mb-6">
        <div className="flex gap-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton w-24 h-10" />
          ))}
        </div>
      </div>
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white shadow-sm border border-gray-200 rounded-xl p-6">
            <div className="skeleton w-32 h-6 mb-4" />
            <div className="skeleton w-full h-12" />
          </div>
        ))}
      </div>
    </div>
  );

  const skeletons = {
    chat: renderChatSkeleton,
    documents: renderDocumentsSkeleton,
    tasks: renderTasksSkeleton,
    dashboard: renderDashboardSkeleton,
    settings: renderSettingsSkeleton,
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full"
    >
      {skeletons[type]()}
    </motion.div>
  );
}

export function CardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="p-4 bg-card rounded-xl border border-border"
        >
          <div className="flex items-center gap-3">
            <div className="skeleton w-10 h-10 rounded-lg" />
            <div className="flex-1">
              <div className="skeleton w-1/2 h-4 mb-2" />
              <div className="skeleton w-1/3 h-3" />
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
