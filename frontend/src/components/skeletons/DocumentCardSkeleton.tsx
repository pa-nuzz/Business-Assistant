'use client';

export function DocumentCardSkeleton() {
  return (
    <div className="animate-pulse rounded-[var(--radius-lg)] bg-[var(--bg-elevated)] p-4 space-y-3">
      <div className="h-4 w-3/4 bg-[var(--bg-subtle)] rounded" />
      <div className="h-3 w-1/2 bg-[var(--bg-subtle)] rounded" />
      <div className="flex gap-2">
        <div className="h-5 w-12 bg-[var(--bg-subtle)] rounded-full" />
        <div className="h-5 w-16 bg-[var(--bg-subtle)] rounded-full" />
      </div>
    </div>
  );
}
