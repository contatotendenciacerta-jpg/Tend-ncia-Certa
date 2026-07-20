import type { ReactNode } from "react";

import styles from "./Card.module.css";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={className ? `${styles.card} ${className}` : styles.card}>{children}</div>;
}
