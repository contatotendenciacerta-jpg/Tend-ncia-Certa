import type { ReactNode } from "react";

import { Card } from "@/components/ui/Card";

import styles from "./EmptyState.module.css";

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <Card className={styles.wrapper}>
      <span className={styles.icon} aria-hidden="true">
        📭
      </span>
      <p className={styles.title}>{title}</p>
      <p className={styles.body}>{body}</p>
      {action && <div className={styles.cta}>{action}</div>}
    </Card>
  );
}
