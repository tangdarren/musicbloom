import type { ReactNode } from "react";

interface EmptyStateProps {
  children: ReactNode;
  className?: string;
}

export function EmptyState({
  children,
  className = "muted",
}: EmptyStateProps) {
  return (
    <p className={className} role="status">
      {children}
    </p>
  );
}
