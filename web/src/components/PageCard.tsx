import type { ReactNode } from "react";

import { PageFrame } from "./PageFrame";
import { PageIntro } from "./PageIntro";

interface PageCardProps {
  eyebrow?: string;
  title: string;
  lede?: string;
  children?: ReactNode;
}

export function PageCard({ eyebrow, title, lede, children }: PageCardProps) {
  return (
    <PageFrame>
      <article className="card page-card">
        <PageIntro eyebrow={eyebrow} title={title} lede={lede} />
        {children}
      </article>
    </PageFrame>
  );
}
