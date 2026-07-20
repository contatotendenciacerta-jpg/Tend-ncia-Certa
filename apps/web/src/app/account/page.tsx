import { getTranslations } from "next-intl/server";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { AppHeader } from "@/components/layout/AppHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ApiError, getMySubscription } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { redirectToLoginClearingSession, requireAccessToken } from "@/lib/require-auth";

import styles from "./page.module.css";

export default async function AccountPage() {
  const token = await requireAccessToken();
  const t = await getTranslations("account");
  const tTiers = await getTranslations("subscription.tierNames");
  const tErrors = await getTranslations("errors");

  let subscription: Awaited<ReturnType<typeof getMySubscription>> | null = null;
  let networkError = false;

  try {
    subscription = await getMySubscription(token);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      await redirectToLoginClearingSession();
    }
    networkError = true;
  }

  return (
    <>
      <AppHeader active="account" />
      <main className={`container ${styles.main}`}>
        <div className={styles.header}>
          <h1 className={styles.title}>{t("title")}</h1>
          <p className={styles.subtitle}>{t("subtitle")}</p>
        </div>

        {networkError && <ErrorState title={tErrors("network.title")} body={tErrors("network.body")} />}

        {!networkError && subscription && !subscription.has_active_subscription && (
          <EmptyState
            title={t("noSubscription.title")}
            body={t("noSubscription.body")}
            action={
              <Button kind="link" href="/#planos">
                {t("noSubscription.cta")}
              </Button>
            }
          />
        )}

        {!networkError && subscription?.has_active_subscription && subscription.tier && (
          <Card className={styles.card}>
            <div className={styles.row}>
              <span className={styles.label}>{t("currentPlan")}</span>
              <Badge tone={subscription.status === "active" ? "buy" : "neutral"}>
                {t(`status.${subscription.status}`)}
              </Badge>
            </div>
            <span className={styles.planName}>{tTiers(subscription.tier.code)}</span>

            {subscription.current_period_end && (
              <p className={styles.meta}>
                {t("renewsAt", { date: formatDate(subscription.current_period_end) })}
              </p>
            )}

            {subscription.pending_tier && subscription.current_period_end && (
              <p className={styles.pending}>
                {t("pendingDowngrade", {
                  tier: tTiers(subscription.pending_tier.code),
                  date: formatDate(subscription.current_period_end),
                })}
              </p>
            )}

            <div className={styles.cta}>
              <Button kind="link" href="/#planos" variant="secondary">
                {t("changePlan")}
              </Button>
            </div>
          </Card>
        )}
      </main>
    </>
  );
}
