import { ReactNode } from 'react';

interface PageWrapperProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

const maxWidthClasses = {
  sm: 'max-w-2xl',
  md: 'max-w-4xl',
  lg: 'max-w-5xl',
  xl: 'max-w-7xl',
  '2xl': 'max-w-[1600px]',
  full: 'max-w-full',
};

const paddingClasses = {
  none: '',
  sm: 'px-4 sm:px-6',
  md: 'px-6 sm:px-8',
  lg: 'px-6 sm:px-8 lg:px-12',
  xl: 'px-6 sm:px-8 lg:px-12 xl:px-16',
};

/**
 * PageWrapper - Consistent page layout wrapper
 * Use this on every app page for consistent spacing and max-width
 */
export function PageWrapper({
  children,
  className = '',
  maxWidth = 'lg',
  padding = 'md',
}: PageWrapperProps) {
  return (
    <div className={`min-h-screen bg-[var(--bg-base)] ${className}`}>
      <div className={`${maxWidthClasses[maxWidth]} mx-auto ${paddingClasses[padding]} py-8`}>
        {children}
      </div>
    </div>
  );
}

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}

/**
 * PageHeader - Consistent page header pattern
 */
export function PageHeader({
  title,
  description,
  actions,
  className = '',
}: PageHeaderProps) {
  return (
    <div className={`mb-8 ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-2xl font-semibold text-[var(--text-primary)] tracking-tight">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-sm text-[var(--text-tertiary)]">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}

interface SectionProps {
  children: ReactNode;
  title?: string;
  description?: string;
  className?: string;
}

/**
 * Section - Consistent section spacing
 */
export function Section({
  children,
  title,
  description,
  className = '',
}: SectionProps) {
  return (
    <section className={`mb-8 ${className}`}>
      {(title || description) && (
        <div className="mb-4">
          {title && (
            <h2 className="text-lg font-medium text-[var(--text-primary)]">
              {title}
            </h2>
          )}
          {description && (
            <p className="mt-1 text-sm text-[var(--text-tertiary)]">
              {description}
            </p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}

interface GridProps {
  children: ReactNode;
  columns?: 1 | 2 | 3 | 4 | 'auto';
  gap?: 'sm' | 'md' | 'lg';
  className?: string;
}

const gridColumns = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 sm:grid-cols-2',
  3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  auto: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5',
};

const gapClasses = {
  sm: 'gap-3',
  md: 'gap-4 sm:gap-6',
  lg: 'gap-6 sm:gap-8',
};

/**
 * Grid - Responsive grid layout
 */
export function Grid({
  children,
  columns = 'auto',
  gap = 'md',
  className = '',
}: GridProps) {
  return (
    <div className={`grid ${gridColumns[columns]} ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  );
}