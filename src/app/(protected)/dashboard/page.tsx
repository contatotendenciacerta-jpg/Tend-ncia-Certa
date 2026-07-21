import { createClient } from "@/lib/supabase/server";
import SignalCard from "@/components/SignalCard";
import type { Signal } from "@/lib/types";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: signals } = await supabase
    .from("signals")
    .select("*")
    .order("created_at", { ascending: false })
    .returns<Signal[]>();

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-semibold">Sinais de Forex</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Mais recentes primeiro. Atualizado por Tendência Certa.
      </p>

      {!signals || signals.length === 0 ? (
        <p className="mt-8 text-zinc-500">Nenhum sinal publicado ainda.</p>
      ) : (
        <ul className="mt-6 flex flex-col gap-4">
          {signals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </ul>
      )}
    </div>
  );
}
