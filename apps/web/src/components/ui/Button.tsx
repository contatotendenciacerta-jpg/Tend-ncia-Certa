import Link from "next/link";
import type { ReactNode } from "react";

import styles from "./Button.module.css";

type Variant = "primary" | "secondary" | "ghost";

interface BaseProps {
  variant?: Variant;
  fullWidth?: boolean;
  children: ReactNode;
}

interface ButtonAsButton extends BaseProps {
  kind?: "button";
  type?: "button" | "submit";
  onClick?: () => void;
  disabled?: boolean;
}

interface ButtonAsLink extends BaseProps {
  kind: "link";
  href: string;
}

type ButtonProps = ButtonAsButton | ButtonAsLink;

function buildClassName(variant: Variant, fullWidth?: boolean) {
  return [styles.button, styles[variant], fullWidth ? styles.fullWidth : ""].filter(Boolean).join(" ");
}

export function Button(props: ButtonProps) {
  const { variant = "primary", fullWidth, children } = props;
  const className = buildClassName(variant, fullWidth);

  if (props.kind === "link") {
    return (
      <Link href={props.href} className={className}>
        {children}
      </Link>
    );
  }

  return (
    <button
      type={props.type ?? "button"}
      className={className}
      onClick={props.onClick}
      disabled={props.disabled}
    >
      {children}
    </button>
  );
}
