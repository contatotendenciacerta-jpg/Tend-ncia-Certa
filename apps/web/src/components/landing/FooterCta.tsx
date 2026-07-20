import { getTranslations } from "next-intl/server";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

import styles from "./FooterCta.module.css";

export async function FooterCta() {
  const t = await getTranslations("landing.footerCta");

  return (
    <section className={`container ${styles.section}`}>
      <Card className={styles.card}>
        <h2 className={styles.title}>{t("title")}</h2>
        <p className={styles.subtitle}>{t("subtitle")}</p>
        <div className={styles.cta}>
          <Button kind="link" href="/register">{t("cta")}</Button>
        </div>
      </Card>
    </section>
  );
}
