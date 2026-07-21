import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import SignalForm from "@/components/SignalForm";
import DeleteSignalButton from "@/components/DeleteSignalButton";
import { createSignal, deleteSignal } from "./actions";
import type { Signal } from "@/lib/types";

export default async function AdminPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("is_admin")
    .eq("id", user.id)
    .single();

  if (!profile?.is_admin) {
    redirect("/dashboard");
  }

  const { data: signals } = await supabase
    .from("signals")
    .select("*")
    .order("created_at", { ascending: false })
    .returns<Signal[]>();

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-semibold">Admin — Sinais</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Criar, editar e apagar sinais de Forex.
      </p>

      {error ? (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      ) : null}

      <section className="mt-6 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-lg font-semibold">Novo sinal</h2>
        <div className="mt-4">
          <SignalForm action={createSignal} submitLabel="Publicar sinal" />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold">Sinais publicados</h2>
        {!signals || signals.length === 0 ? (
          <p className="mt-4 text-zinc-500">Nenhum sinal ainda.</p>
        ) : (
          <ul className="mt-4 divide-y divide-zinc-200 dark:divide-zinc-800">
            {signals.map((signal) => (
              <li
                key={signal.id}
                className="flex items-center justify-between gap-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-bold uppercase text-white ${
                      signal.direction === "buy" ? "bg-green-700" : "bg-red-700"
                    }`}
                  >
                    {signal.direction === "buy" ? "Compra" : "Venda"}
                  </span>
                  <span className="font-medium">{signal.pair}</span>
                  <span className="text-sm text-zinc-500">
                    {signal.timeframe}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href={`/admin/${signal.id}`}
                    className="text-sm text-green-700 hover:underline dark:text-green-400"
                  >
                    Editar
                  </Link>
                  <form action={deleteSignal.bind(null, signal.id)}>
                    <DeleteSignalButton />
                  </form>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
