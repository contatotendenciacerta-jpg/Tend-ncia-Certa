import { redirect } from "next/navigation";

import { clearAuthCookies, getAccessToken } from "@/lib/auth-cookies";

export async function requireAccessToken(): Promise<string> {
  const token = await getAccessToken();
  if (!token) {
    redirect("/login");
  }
  return token;
}

export async function redirectToLoginClearingSession(): Promise<never> {
  await clearAuthCookies();
  redirect("/login");
}
