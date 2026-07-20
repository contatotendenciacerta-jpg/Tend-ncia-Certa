import { getTranslations } from "next-intl/server";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { formatDecimal } from "@/lib/format";
import type { Signal } from "@/lib/types";

import styles from "./SignalCard.module.css";

export async function SignalCard({ signal }: { signal: Signal }) {
  const [t, tMarkets] = await Promise.all([getTranslations("signals"), getTranslations("markets")]);

  const isBuy = signal.direction === "buy";
  const sortedTargets = [...signal.targets].sort((a, b) => a.order - b.order);

  return (
    <Card className={styles.card}>
      <div className={styles.top}>
        <div className={styles.assetBlock}>
          <span className={styles.symbol}>{signal.asset.symbol}</span>
          <div className={styles.marketRow}>
            <span className={styles.market}>{tMarkets(signal.asset.market.code)}</span>
          </div>
        </div>
        <div className={styles.badges}>
          <Badge tone={isBuy ? "buy" : "sell"}>{t(`direction.${signal.direction}`)}</Badge>
          <Badge tone="neutral">{t(`confidence.${signal.confidence_level}`)}</Badge>
        </div>
      </div>

      <div className={styles.grid}>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>{t("fields.entry")}</span>
          <span className={styles.metricValue}>{formatDecimal(signal.entry_price)}</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>{t("fields.stop")}</span>
          <span className={styles.metricValue}>{formatDecimal(signal.stop_loss)}</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>{t("fields.timeframe")}</span>
          <span className={styles.metricValue}>{signal.timeframe}</span>
        </div>
      </div>

      <div className={styles.metric}>
        <span className={styles.metricLabel}>{t("fields.targets")}</span>
        <div className={styles.targets}>
          {sortedTargets.map((target) => (
            <span key={target.id} className={styles.targetChip}>
              TP{target.order} · {formatDecimal(target.target_price)}
            </span>
          ))}
        </div>
      </div>
    </Card>
  );
}
