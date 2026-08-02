import type { ReactNode } from "react";

interface InlineAlertProps {
  children: ReactNode;
  role?: "alert" | "status";
  as?: "div" | "p";
  className?: string;
}

export function InlineAlert({
  children,
  role = "alert",
  as: Tag = "div",
  className,
}: InlineAlertProps) {
  const classes = className ? `player-alert ${className}` : "player-alert";

  return (
    <Tag className={classes} role={role}>
      {children}
    </Tag>
  );
}
