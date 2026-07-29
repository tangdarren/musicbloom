import type { ReactNode } from "react";

interface PageCardProps {
  eyebrow?: string;
  title: string;
  lede?: string;
  children?: ReactNode;
}

export function PageCard({ eyebrow, title, lede, children }: PageCardProps) {
  return (
    <section className="page">
      <article className="card page-card">
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {lede ? <p className="lede">{lede}</p> : null}
        {children}
      </article>
    </section>
  );
}
