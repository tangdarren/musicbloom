import type { ElementType, ReactNode } from "react";

interface PageIntroProps {
  eyebrow?: string;
  title: ReactNode;
  titleAs?: "h1" | "h2";
  titleId?: string;
  lede?: ReactNode;
  as?: "div" | "header";
  className?: string;
}

export function PageIntro({
  eyebrow,
  title,
  titleAs = "h1",
  titleId,
  lede,
  as,
  className,
}: PageIntroProps) {
  const TitleTag = titleAs as ElementType;
  const content = (
    <>
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <TitleTag id={titleId}>{title}</TitleTag>
      {lede ? <p className="lede">{lede}</p> : null}
    </>
  );

  if (as == null && className == null) {
    return content;
  }

  const Wrapper = as ?? "div";
  return <Wrapper className={className}>{content}</Wrapper>;
}
