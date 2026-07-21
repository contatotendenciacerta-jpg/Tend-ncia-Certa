import Link from "next/link";
import { logout } from "@/lib/actions/auth";

export default function Header({
  email,
  isAdmin,
}: {
  email: string;
  isAdmin: boolean;
}) {
  return (
    <header className="border-b border-zinc-200 dark:border-zinc-800">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
        <Link href="/dashboard" className="font-semibold">
          Tendência Certa
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="hover:underline">
            Sinais
          </Link>
          {isAdmin ? (
            <Link href="/admin" className="hover:underline">
              Admin
            </Link>
          ) : null}
          <span className="hidden text-zinc-500 sm:inline">{email}</span>
          <form action={logout}>
            <button type="submit" className="text-zinc-500 hover:underline">
              Sair
            </button>
          </form>
        </nav>
      </div>
    </header>
  );
}
