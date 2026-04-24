'use client';

export function TaskCardSkeleton() {
  return (
    <div className="animate-pulse rounded-[var(--radius-md)] bg-[var(--bg-elevated)] p-4 space-y-3">
      <div className="flex justify-between items-start">
        <div className="h-4 w-2/3 bg-[var(--bg-subtle)] rounded" />
        <div className="h-5 w-14 bg-[var(--bg-subtle)] rounded-full" />
      </div>
      <div className="h-3 w-1/3 bg-[var(--bg-subtle)] rounded" />
      <div className="flex gap-2 pt-2">
        <div className="h-4 w-8 bg-[var(--bg-subtle)] rounded-full" />
        <div className="h-4 w-8 bg-[var(--bg-subtle)] rounded-full" />
      </div>
    </div>
  );
}
