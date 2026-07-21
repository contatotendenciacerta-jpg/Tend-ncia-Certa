import type { Signal } from "@/lib/types";

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function SignalCard({ signal }: { signal: Signal }) {
  const isBuy = signal.direction === "buy";

  return (
    <li
      className={`rounded-lg border p-4 ${
        isBuy
          ? "border-green-600/30 bg-green-600/5"
          : "border-red-600/30 bg-red-600/5"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-lg font-semibold">{signal.pair}</span>
        <span
          className={`rounded px-2 py-0.5 text-xs font-bold uppercase text-white ${
            isBuy ? "bg-green-700" : "bg-red-700"
          }`}
        >
          {isBuy ? "Compra" : "Venda"}
        </span>
      </div>

      <dl className="mt-3 grid grid-cols-3 gap-2 text-sm">
        <div>
          <dt className="text-zinc-500">Entrada</dt>
          <dd className="font-mono">{signal.entry_price}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Stop</dt>
          <dd className="font-mono">{signal.stop_loss}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Alvo</dt>
          <dd className="font-mono">{signal.target_price}</dd>
        </div>
      </dl>

      <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
        <span className="rounded bg-zinc-200 px-1.5 py-0.5 font-medium dark:bg-zinc-800">
          {signal.timeframe}
        </span>
        <time dateTime={signal.created_at}>{formatDateTime(signal.created_at)}</time>
      </div>
    </li>
  );
}
