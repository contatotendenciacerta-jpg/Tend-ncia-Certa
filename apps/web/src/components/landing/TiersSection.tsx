import { getTranslations } from "next-intl/server";

import { ErrorState } from "@/components/feedback/ErrorState";
import { getPublicTiers } from "@/lib/api";

import { TierCard } from "./TierCard";
import styles from "./TiersSection.module.css";

export async function TiersSection() {
  const t = await getTranslations("landing.tiers");

  let tiers: Awaited<ReturnType<typeof getPublicTiers>> = [];
  let loadFailed = false;

  try {
    tiers = await getPublicTiers();
  } catch {
    loadFailed = true;
  }

  return (
    <section id="planos" className={`container ${styles.section}`}>
      <div className={styles.header}>
        <h2 className={styles.title}>{t("title")}</h2>
        <p className={styles.subtitle}>{t("subtitle")}</p>
      </div>

      {loadFailed && <ErrorState title={t("loadError")} body="" />}

      {!loadFailed && tiers.length === 0 && <p className={styles.empty}>{t("empty")}</p>}

      {!loadFailed && tiers.length > 0 && (
        <div className={styles.grid}>
          {tiers.map((tier) => (
            <TierCard key={tier.id} tier={tier} />
          ))}
        </div>
      )}
    </section>
  );
}
