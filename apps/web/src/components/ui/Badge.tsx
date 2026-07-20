import type { ReactNode } from "react";

import styles from "./Badge.module.css";

type BadgeTone = "buy" | "sell" | "neutral" | "accent" | "vip";

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: ReactNode }) {
  return <span className={`${styles.badge} ${styles[tone]}`}>{children}</span>;
}
