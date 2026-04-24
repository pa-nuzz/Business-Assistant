'use client';

export function ChatSkeleton() {
  return (
    <div className="flex h-full bg-[var(--bg-base)]">
      {/* Sidebar Skeleton */}
      <div className="w-64 border-r border-[var(--border-default)] p-4 space-y-4">
        <div className="h-8 w-32 bg-[var(--bg-elevated)] rounded" />
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-[var(--bg-elevated)] rounded" />
          ))}
        </div>
      </div>
      
      {/* Chat Area Skeleton */}
      <div className="flex-1 flex flex-col p-4 space-y-4">
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-full bg-[var(--bg-elevated)]" />
          <div className="h-16 w-3/4 bg-[var(--bg-elevated)] rounded-[var(--radius-md)]" />
        </div>
        <div className="flex gap-3 justify-end">
          <div className="h-12 w-1/2 bg-[var(--brand-primary)] rounded-[var(--radius-md)]" />
        </div>
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-full bg-[var(--bg-elevated)]" />
          <div className="h-24 w-2/3 bg-[var(--bg-elevated)] rounded-[var(--radius-md)]" />
        </div>
      </div>
    </div>
  );
}
