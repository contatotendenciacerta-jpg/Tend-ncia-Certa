import { notFound, redirect } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import SignalForm from "@/components/SignalForm";
import { updateSignal } from "../actions";
import type { Signal } from "@/lib/types";

export default async function EditSignalPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { id } = await params;
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

  const { data: signal } = await supabase
    .from("signals")
    .select("*")
    .eq("id", id)
    .single<Signal>();

  if (!signal) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Link href="/admin" className="text-sm text-zinc-500 hover:underline">
        ← Voltar
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">
        Editar sinal — {signal.pair}
      </h1>

      {error ? (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      ) : null}

      <div className="mt-6">
        <SignalForm
          action={updateSignal.bind(null, signal.id)}
          signal={signal}
          submitLabel="Salvar alterações"
        />
      </div>
    </div>
  );
}
