'use client';

export function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="h-8 w-48 bg-[var(--bg-elevated)] rounded animate-pulse" />
        <div className="h-10 w-32 bg-[var(--bg-elevated)] rounded animate-pulse" />
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="animate-pulse rounded-[var(--radius-lg)] bg-[var(--bg-elevated)] p-6 space-y-3">
            <div className="h-4 w-24 bg-[var(--bg-subtle)] rounded" />
            <div className="h-8 w-16 bg-[var(--bg-subtle)] rounded" />
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="h-6 w-32 bg-[var(--bg-elevated)] rounded animate-pulse" />
          <div className="animate-pulse rounded-[var(--radius-lg)] bg-[var(--bg-elevated)] p-6 h-64" />
        </div>
        <div className="space-y-4">
          <div className="h-6 w-24 bg-[var(--bg-elevated)] rounded animate-pulse" />
          <div className="animate-pulse rounded-[var(--radius-lg)] bg-[var(--bg-elevated)] p-4 h-48 space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-[var(--bg-subtle)] rounded" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
