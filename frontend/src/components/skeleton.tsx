'use client';

interface SkeletonProps {
  width?: string;
  height?: string;
  className?: string;
  circle?: boolean;
  style?: React.CSSProperties;
}

export function Skeleton({ width = '100%', height = '20px', className = '', circle = false, style }: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius: circle ? '50%' : undefined,
        ...style,
      }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div style={{ padding: '20px', backgroundColor: 'var(--surface-0)', borderRadius: 'var(--r-lg)', border: '1px solid var(--surface-border)' }}>
      <Skeleton height="24px" width="60%" style={{ marginBottom: '12px' }} />
      <Skeleton height="16px" width="100%" style={{ marginBottom: '8px' }} />
      <Skeleton height="16px" width="80%" />
    </div>
  );
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} height="48px" />
      ))}
    </div>
  );
}
