import { NextResponse, type NextRequest } from "next/server";

import { ApiError, ApiNetworkError, login, register } from "@/lib/api";
import { setAuthCookies } from "@/lib/auth-cookies";

export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => null)) as {
    name?: string;
    email?: string;
    password?: string;
  } | null;

  if (!body?.name || !body?.email || !body?.password) {
    return NextResponse.json({ error: "invalid_request" }, { status: 400 });
  }

  try {
    await register(body.name, body.email, body.password);
  } catch (error) {
    if (error instanceof ApiError) {
      const status = error.status === 409 ? 409 : 502;
      const code = error.status === 409 ? "email_taken" : "unknown";
      return NextResponse.json({ error: code }, { status });
    }
    if (error instanceof ApiNetworkError) {
      return NextResponse.json({ error: "network_error" }, { status: 503 });
    }
    return NextResponse.json({ error: "unknown" }, { status: 500 });
  }

  try {
    const tokens = await login(body.email, body.password);
    await setAuthCookies(tokens.access_token, tokens.refresh_token);
    return NextResponse.json({ ok: true });
  } catch {
    // Account created but the immediate auto-login failed (e.g. a transient
    // network blip) - the user can still sign in manually with what they
    // just typed, so this is not treated as a registration failure.
    return NextResponse.json({ ok: true, requiresManualLogin: true });
  }
}
