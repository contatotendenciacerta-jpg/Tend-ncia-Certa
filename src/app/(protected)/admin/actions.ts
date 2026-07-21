"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import type { SignalDirection, Timeframe } from "@/lib/types";

type SignalInput = {
  pair: string;
  direction: SignalDirection;
  entry_price: number;
  stop_loss: number;
  target_price: number;
  timeframe: Timeframe;
};

function parseSignalForm(formData: FormData): SignalInput {
  return {
    pair: String(formData.get("pair") ?? "").trim().toUpperCase(),
    direction: formData.get("direction") as SignalDirection,
    entry_price: Number(formData.get("entry_price")),
    stop_loss: Number(formData.get("stop_loss")),
    target_price: Number(formData.get("target_price")),
    timeframe: formData.get("timeframe") as Timeframe,
  };
}

export async function createSignal(formData: FormData) {
  const supabase = await createClient();
  const input = parseSignalForm(formData);

  const { error } = await supabase.from("signals").insert(input);

  if (error) {
    redirect(`/admin?error=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/admin");
  revalidatePath("/dashboard");
  redirect("/admin");
}

export async function updateSignal(id: string, formData: FormData) {
  const supabase = await createClient();
  const input = parseSignalForm(formData);

  const { error } = await supabase.from("signals").update(input).eq("id", id);

  if (error) {
    redirect(`/admin/${id}?error=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/admin");
  revalidatePath("/dashboard");
  redirect("/admin");
}

export async function deleteSignal(id: string) {
  const supabase = await createClient();
  await supabase.from("signals").delete().eq("id", id);

  revalidatePath("/admin");
  revalidatePath("/dashboard");
}
