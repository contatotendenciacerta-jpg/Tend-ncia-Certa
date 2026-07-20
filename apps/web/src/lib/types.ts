export type MarketCode = "crypto" | "forex" | "b3";
export type TierCode = "basic" | "pro" | "vip";
export type BillingInterval = "monthly" | "yearly";

export interface SubscriptionTier {
  id: string;
  code: TierCode;
  name_i18n_key: string;
  price_cents: number;
  currency: string;
  billing_interval: BillingInterval;
  markets_allowed: MarketCode[];
  signal_delay_minutes: number;
  max_active_signals_visible: number | null;
  allows_vip_only_signals: boolean;
  push_notifications: boolean;
  is_active: boolean;
}

export type SubscriptionStatus = "trialing" | "active" | "past_due" | "canceled" | "expired";

export interface MySubscription {
  has_active_subscription: boolean;
  tier: SubscriptionTier | null;
  status: SubscriptionStatus | null;
  current_period_end: string | null;
  pending_tier: SubscriptionTier | null;
}

export type SignalDirection = "buy" | "sell";
export type SignalTimeframe = "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1" | "W1";
export type ConfidenceLevel = "low" | "medium" | "high";
export type SignalStatus = "pending" | "active" | "hit_target" | "hit_stop" | "expired" | "canceled";

export interface SignalTarget {
  id: string;
  order: number;
  target_price: string;
  hit_at: string | null;
}

export interface MarketSummary {
  code: MarketCode;
  name_i18n_key: string;
}

export interface AssetSummary {
  id: string;
  symbol: string;
  display_name: string;
  market: MarketSummary;
}

export interface Signal {
  id: string;
  asset_id: string;
  asset: AssetSummary;
  direction: SignalDirection;
  entry_price: string;
  stop_loss: string;
  timeframe: SignalTimeframe;
  confidence_level: ConfidenceLevel;
  status: SignalStatus;
  notes: string | null;
  published_at: string | null;
  closed_at: string | null;
  targets: SignalTarget[];
}

export interface CurrentUser {
  id: string;
  email: string;
  name: string;
  role: "admin" | "subscriber";
  locale: string;
  status: "active" | "suspended" | "deleted";
  created_at: string;
}
