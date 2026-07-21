export type SignalDirection = "buy" | "sell";

export type Timeframe = "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1" | "W1";

export const TIMEFRAMES: Timeframe[] = [
  "M1",
  "M5",
  "M15",
  "M30",
  "H1",
  "H4",
  "D1",
  "W1",
];

export type Signal = {
  id: string;
  pair: string;
  direction: SignalDirection;
  entry_price: number;
  stop_loss: number;
  target_price: number;
  timeframe: Timeframe;
  created_at: string;
  updated_at: string;
  created_by: string | null;
};
