import { getTranslations } from "next-intl/server";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { SubscriptionTier } from "@/lib/types";

import styles from "./TierCard.module.css";

function formatPrice(priceCents: number, currency: string) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(priceCents / 100);
}

export async function TierCard({ tier }: { tier: SubscriptionTier }) {
  const [t, tTiers, tMarkets] = await Promise.all([
    getTranslations("landing.tiers"),
    getTranslations("subscription.tierNames"),
    getTranslations("markets"),
  ]);

  const isVip = tier.code === "vip";
  const isHighlighted = tier.code === "pro";
  const cardClassName = isVip ? styles.vipCard : isHighlighted ? styles.highlighted : "";

  const marketsLabel = tier.markets_allowed.map((code) => tMarkets(code)).join(", ");
  const delayLabel =
    tier.signal_delay_minutes > 0
      ? t("featureDelayMinutes", { minutes: tier.signal_delay_minutes })
      : t("featureDelayRealtime");
  const maxSignalsLabel =
    tier.max_active_signals_visible === null
      ? t("featureMaxSignalsUnlimited")
      : String(tier.max_active_signals_visible);

  return (
    <Card className={`${styles.card} ${cardClassName}`}>
      <div className={styles.badgeRow}>
        {isVip && <Badge tone="vip">VIP</Badge>}
        {isHighlighted && !isVip && <Badge tone="accent">★</Badge>}
      </div>
      <span className={styles.tierName}>{tTiers(tier.code)}</span>
      <div className={styles.priceRow}>
        <span className={styles.price}>{formatPrice(tier.price_cents, tier.currency)}</span>
        <span className={styles.interval}>
          {tier.billing_interval === "monthly" ? t("perMonth") : t("perYear")}
        </span>
      </div>

      <ul className={styles.features}>
        <li className={styles.feature}>
          <span className={styles.featureLabel}>{t("featureMarkets")}</span>
          <span className={styles.featureValue}>{marketsLabel}</span>
        </li>
        <li className={styles.feature}>
          <span className={styles.featureLabel}>{t("featureDelay")}</span>
          <span className={styles.featureValue}>{delayLabel}</span>
        </li>
        <li className={styles.feature}>
          <span className={styles.featureLabel}>{t("featureMaxSignals")}</span>
          <span className={styles.featureValue}>{maxSignalsLabel}</span>
        </li>
        {tier.allows_vip_only_signals && (
          <li className={styles.feature}>
            <span className={styles.featureLabel}>{t("featureVipSignals")}</span>
            <span className={styles.featureValue}>✓</span>
          </li>
        )}
        {tier.push_notifications && (
          <li className={styles.feature}>
            <span className={styles.featureLabel}>{t("featurePush")}</span>
            <span className={styles.featureValue}>✓</span>
          </li>
        )}
      </ul>

      <div className={styles.cta}>
        <Button kind="link" href="/register" variant={isVip || isHighlighted ? "primary" : "secondary"} fullWidth>
          {t("cta")}
        </Button>
      </div>
    </Card>
  );
}
