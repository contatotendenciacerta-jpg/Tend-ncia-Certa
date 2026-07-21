import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import Header from "@/components/Header";

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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

  return (
    <div className="flex min-h-screen flex-col">
      <Header email={user.email ?? ""} isAdmin={profile?.is_admin ?? false} />
      <main className="flex-1">{children}</main>
    </div>
  );
}
