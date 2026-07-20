import type {
  CurrentUser,
  MySubscription,
  Signal,
  SubscriptionTier,
} from "@/lib/types";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export class ApiNetworkError extends Error {
  constructor(cause: unknown) {
    super("network_error");
    this.name = "ApiNetworkError";
    this.cause = cause;
  }
}

interface ApiFetchOptions {
  method?: string;
  body?: unknown;
  accessToken?: string;
}

async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { method = "GET", body, accessToken } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
  } catch (cause) {
    throw new ApiNetworkError(cause);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = (await response.json()) as { detail?: unknown };
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      // body wasn't JSON - keep statusText
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function login(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/auth/login", { method: "POST", body: { email, password } });
}

export function register(name: string, email: string, password: string): Promise<CurrentUser> {
  return apiFetch<CurrentUser>("/auth/register", { method: "POST", body: { name, email, password } });
}

export function getMe(accessToken: string): Promise<CurrentUser> {
  return apiFetch<CurrentUser>("/auth/me", { accessToken });
}

export function getPublicTiers(): Promise<SubscriptionTier[]> {
  return apiFetch<SubscriptionTier[]>("/subscription-tiers");
}

export function getSignals(accessToken: string): Promise<Signal[]> {
  return apiFetch<Signal[]>("/signals", { accessToken });
}

export function getMySubscription(accessToken: string): Promise<MySubscription> {
  return apiFetch<MySubscription>("/me/subscription", { accessToken });
}
