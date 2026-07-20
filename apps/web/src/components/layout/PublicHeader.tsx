import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { Button } from "@/components/ui/Button";

import styles from "./Header.module.css";

export async function PublicHeader() {
  const t = await getTranslations("common");

  return (
    <header className={styles.header}>
      <div className={`container ${styles.inner}`}>
        <Link href="/" className={styles.logo}>
          <span className={styles.logoMark} aria-hidden="true" />
          {t("appName")}
        </Link>
        <nav className={styles.nav}>
          <Link href="/login" className={styles.navLink}>
            {t("nav.login")}
          </Link>
          <Button kind="link" href="/register">{t("nav.register")}</Button>
        </nav>
      </div>
    </header>
  );
}
