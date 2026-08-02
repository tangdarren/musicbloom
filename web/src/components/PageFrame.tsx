import type { ReactNode } from "react";

interface PageFrameProps {
  children: ReactNode;
  className?: string;
}

export function PageFrame({ children, className }: PageFrameProps) {
  const classes = className ? `page ${className}` : "page";

  return <section className={classes}>{children}</section>;
}
