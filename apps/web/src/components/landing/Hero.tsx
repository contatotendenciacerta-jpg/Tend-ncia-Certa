import { getTranslations } from "next-intl/server";

import { Button } from "@/components/ui/Button";

import styles from "./Hero.module.css";

export async function Hero() {
  const t = await getTranslations("landing.hero");

  return (
    <section className={`container ${styles.hero}`}>
      <span className={styles.eyebrow}>{t("eyebrow")}</span>
      <h1 className={styles.title}>{t("title")}</h1>
      <p className={styles.subtitle}>{t("subtitle")}</p>
      <div className={styles.actions}>
        <Button kind="link" href="/register">{t("ctaPrimary")}</Button>
        <Button kind="link" href="/login" variant="secondary">
          {t("ctaSecondary")}
        </Button>
      </div>
    </section>
  );
}
