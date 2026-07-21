import { TIMEFRAMES, type Signal } from "@/lib/types";

export default function SignalForm({
  action,
  signal,
  submitLabel,
}: {
  action: (formData: FormData) => void;
  signal?: Signal;
  submitLabel: string;
}) {
  return (
    <form action={action} className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <div className="col-span-2 flex flex-col gap-1 sm:col-span-1">
        <label htmlFor="pair" className="text-sm font-medium">
          Par
        </label>
        <input
          id="pair"
          name="pair"
          type="text"
          placeholder="EUR/USD"
          required
          defaultValue={signal?.pair}
          className="rounded-md border border-zinc-300 px-3 py-2 text-sm uppercase dark:border-zinc-700 dark:bg-zinc-900"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="direction" className="text-sm font-medium">
          Direção
        </label>
        <select
          id="direction"
          name="direction"
          required
          defaultValue={signal?.direction ?? "buy"}
          className="rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          <option value="buy">Compra</option>
          <option value="sell">Venda</option>
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="timeframe" className="text-sm font-medium">
          Timeframe
        </label>
        <select
          id="timeframe"
          name="timeframe"
          required
          defaultValue={signal?.timeframe ?? "H1"}
          className="rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          {TIMEFRAMES.map((tf) => (
            <option key={tf} value={tf}>
              {tf}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="entry_price" className="text-sm font-medium">
          Entrada
        </label>
        <input
          id="entry_price"
          name="entry_price"
          type="number"
          step="any"
          required
          defaultValue={signal?.entry_price}
          className="rounded-md border border-zinc-300 px-3 py-2 text-sm font-mono dark:border-zinc-700 dark:bg-zinc-900"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="stop_loss" className="text-sm font-medium">
          Stop loss
        </label>
        <input
          id="stop_loss"
          name="stop_loss"
          type="number"
          step="any"
          required
          defaultValue={signal?.stop_loss}
          className="rounded-md border border-zinc-300 px-3 py-2 text-sm font-mono dark:border-zinc-700 dark:bg-zinc-900"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="target_price" className="text-sm font-medium">
          Alvo
        </label>
        <input
          id="target_price"
          name="target_price"
          type="number"
          step="any"
          required
          defaultValue={signal?.target_price}
          className="rounded-md border border-zinc-300 px-3 py-2 text-sm font-mono dark:border-zinc-700 dark:bg-zinc-900"
        />
      </div>

      <div className="col-span-2 sm:col-span-3">
        <button
          type="submit"
          className="rounded-md bg-green-700 px-4 py-2 text-sm font-semibold text-white hover:bg-green-800"
        >
          {submitLabel}
        </button>
      </div>
    </form>
  );
}
