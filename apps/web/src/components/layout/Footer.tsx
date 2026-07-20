import { getTranslations } from "next-intl/server";

import styles from "./Footer.module.css";

export async function Footer() {
  const t = await getTranslations("common");
  const year = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        <span className={styles.appName}>{t("appName")}</span>
        <span className={styles.tagline}>{t("footer.tagline")}</span>
        <span className={styles.rights}>
          © {year} {t("appName")} — {t("footer.rights")}
        </span>
      </div>
    </footer>
  );
}
