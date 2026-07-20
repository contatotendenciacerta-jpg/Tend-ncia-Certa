import { getTranslations } from "next-intl/server";

import { EmptyState } from "@/components/dashboard/EmptyState";
import { SignalCard } from "@/components/dashboard/SignalCard";
import { ErrorState } from "@/components/feedback/ErrorState";
import { AppHeader } from "@/components/layout/AppHeader";
import { Button } from "@/components/ui/Button";
import { ApiError, getMySubscription, getSignals } from "@/lib/api";
import { redirectToLoginClearingSession, requireAccessToken } from "@/lib/require-auth";

import styles from "./page.module.css";

export default async function DashboardPage() {
  const token = await requireAccessToken();
  const t = await getTranslations("signals");
  const tErrors = await getTranslations("errors");

  let signals: Awaited<ReturnType<typeof getSignals>> = [];
  let hasActiveSubscription = false;
  let networkError = false;

  try {
    signals = await getSignals(token);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      await redirectToLoginClearingSession();
    }
    networkError = true;
  }

  if (!networkError && signals.length === 0) {
    try {
      const subscription = await getMySubscription(token);
      hasActiveSubscription = subscription.has_active_subscription;
    } catch {
      // Best-effort only: if this secondary call fails, fall back to the
      // generic "no signals yet" message instead of the "no plan" one.
    }
  }

  return (
    <>
      <AppHeader active="dashboard" />
      <main className={`container ${styles.main}`}>
        <div className={styles.header}>
          <h1 className={styles.title}>{t("title")}</h1>
          <p className={styles.subtitle}>{t("subtitle")}</p>
        </div>

        {networkError && <ErrorState title={tErrors("network.title")} body={tErrors("network.body")} />}

        {!networkError && signals.length === 0 && !hasActiveSubscription && (
          <EmptyState
            title={t("empty.noSubscriptionTitle")}
            body={t("empty.noSubscriptionBody")}
            action={
              <Button kind="link" href="/#planos">
                {t("empty.cta")}
              </Button>
            }
          />
        )}

        {!networkError && signals.length === 0 && hasActiveSubscription && (
          <EmptyState title={t("empty.withSubscriptionTitle")} body={t("empty.withSubscriptionBody")} />
        )}

        {!networkError && signals.length > 0 && (
          <div className={styles.grid}>
            {signals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
          </div>
        )}
      </main>
    </>
  );
}
