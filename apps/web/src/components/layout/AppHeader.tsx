import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { LogoutButton } from "./LogoutButton";
import styles from "./Header.module.css";

export async function AppHeader({ active }: { active: "dashboard" | "account" }) {
  const t = await getTranslations("common");

  return (
    <header className={styles.header}>
      <div className={`container ${styles.inner}`}>
        <Link href="/dashboard" className={styles.logo}>
          <span className={styles.logoMark} aria-hidden="true" />
          {t("appName")}
        </Link>
        <nav className={styles.nav}>
          <Link
            href="/dashboard"
            className={`${styles.navLink} ${active === "dashboard" ? styles.navLinkActive : ""}`}
          >
            {t("nav.dashboard")}
          </Link>
          <Link
            href="/account"
            className={`${styles.navLink} ${active === "account" ? styles.navLinkActive : ""}`}
          >
            {t("nav.account")}
          </Link>
          <LogoutButton label={t("nav.logout")} />
        </nav>
      </div>
    </header>
  );
}
