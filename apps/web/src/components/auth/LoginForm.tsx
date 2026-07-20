"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";

import styles from "./AuthLayout.module.css";

interface Messages {
  emailLabel: string;
  passwordLabel: string;
  submit: string;
  submitting: string;
  invalidCredentialsError: string;
  genericError: string;
  networkError: string;
}

export function LoginForm({ messages }: { messages: Messages }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        router.push("/dashboard");
        router.refresh();
        return;
      }

      const data = (await response.json().catch(() => null)) as { error?: string } | null;
      if (data?.error === "invalid_credentials") {
        setError(messages.invalidCredentialsError);
      } else if (data?.error === "network_error") {
        setError(messages.networkError);
      } else {
        setError(messages.genericError);
      }
    } catch {
      setError(messages.networkError);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <div className={styles.field}>
        <label className={styles.label} htmlFor="email">
          {messages.emailLabel}
        </label>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          className={styles.input}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="password">
          {messages.passwordLabel}
        </label>
        <input
          id="password"
          type="password"
          required
          autoComplete="current-password"
          className={styles.input}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </div>

      <div className={styles.submit}>
        <Button type="submit" disabled={isSubmitting} fullWidth>
          {isSubmitting ? messages.submitting : messages.submit}
        </Button>
      </div>
    </form>
  );
}
