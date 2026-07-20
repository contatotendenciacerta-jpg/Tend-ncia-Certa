import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { RegisterForm } from "@/components/auth/RegisterForm";
import styles from "@/components/auth/AuthLayout.module.css";
import { Card } from "@/components/ui/Card";
import { Footer } from "@/components/layout/Footer";
import { PublicHeader } from "@/components/layout/PublicHeader";

export default async function RegisterPage() {
  const t = await getTranslations("auth.register");
  const tErrors = await getTranslations("errors");

  return (
    <>
      <PublicHeader />
      <main className={styles.wrapper}>
        <Card className={styles.card}>
          <h1 className={styles.title}>{t("title")}</h1>
          <p className={styles.subtitle}>{t("subtitle")}</p>

          <RegisterForm
            messages={{
              nameLabel: t("nameLabel"),
              emailLabel: t("emailLabel"),
              passwordLabel: t("passwordLabel"),
              passwordHint: t("passwordHint"),
              submit: t("submit"),
              submitting: t("submitting"),
              emailTakenError: t("errors.emailTaken"),
              genericError: t("errors.generic"),
              networkError: tErrors("network.body"),
            }}
          />

          <p className={styles.footer}>
            {t("hasAccount")}{" "}
            <Link href="/login" className={styles.footerLink}>
              {t("signIn")}
            </Link>
          </p>
        </Card>
      </main>
      <Footer />
    </>
  );
}
