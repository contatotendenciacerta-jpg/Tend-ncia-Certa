import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { LoginForm } from "@/components/auth/LoginForm";
import styles from "@/components/auth/AuthLayout.module.css";
import { Card } from "@/components/ui/Card";
import { Footer } from "@/components/layout/Footer";
import { PublicHeader } from "@/components/layout/PublicHeader";

export default async function LoginPage() {
  const t = await getTranslations("auth.login");
  const tErrors = await getTranslations("errors");

  return (
    <>
      <PublicHeader />
      <main className={styles.wrapper}>
        <Card className={styles.card}>
          <h1 className={styles.title}>{t("title")}</h1>
          <p className={styles.subtitle}>{t("subtitle")}</p>

          <LoginForm
            messages={{
              emailLabel: t("emailLabel"),
              passwordLabel: t("passwordLabel"),
              submit: t("submit"),
              submitting: t("submitting"),
              invalidCredentialsError: t("errors.invalidCredentials"),
              genericError: t("errors.generic"),
              networkError: tErrors("network.body"),
            }}
          />

          <p className={styles.footer}>
            {t("noAccount")}{" "}
            <Link href="/register" className={styles.footerLink}>
              {t("createAccount")}
            </Link>
          </p>
        </Card>
      </main>
      <Footer />
    </>
  );
}
