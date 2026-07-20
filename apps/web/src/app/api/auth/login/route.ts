import { NextResponse, type NextRequest } from "next/server";

import { ApiError, ApiNetworkError, login } from "@/lib/api";
import { setAuthCookies } from "@/lib/auth-cookies";

export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => null)) as { email?: string; password?: string } | null;

  if (!body?.email || !body?.password) {
    return NextResponse.json({ error: "invalid_request" }, { status: 400 });
  }

  try {
    const tokens = await login(body.email, body.password);
    await setAuthCookies(tokens.access_token, tokens.refresh_token);
    return NextResponse.json({ ok: true });
  } catch (error) {
    if (error instanceof ApiError) {
      const status = error.status === 401 ? 401 : 502;
      const code = error.status === 401 ? "invalid_credentials" : "unknown";
      return NextResponse.json({ error: code }, { status });
    }
    if (error instanceof ApiNetworkError) {
      return NextResponse.json({ error: "network_error" }, { status: 503 });
    }
    return NextResponse.json({ error: "unknown" }, { status: 500 });
  }
}
