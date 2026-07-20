import type { ReactNode } from "react";

import styles from "./ErrorState.module.css";

export function ErrorState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className={styles.wrapper} role="alert">
      <span className={styles.icon} aria-hidden="true">
        ⚠️
      </span>
      <div>
        <p className={styles.title}>{title}</p>
        <p className={styles.body}>{body}</p>
      </div>
      {action}
    </div>
  );
}
