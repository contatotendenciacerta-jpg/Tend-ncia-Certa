import Link from "next/link";
import { login } from "@/lib/actions/auth";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-sm flex-col justify-center px-6 py-12">
      <Link href="/" className="mb-8 text-sm text-zinc-500 hover:underline">
        ← Tendência Certa
      </Link>
      <h1 className="text-2xl font-semibold">Entrar</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Acesse sua conta para ver os sinais.
      </p>

      {error ? (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      ) : null}

      <form action={login} className="mt-6 flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="email" className="text-sm font-medium">
            E-mail
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            className="rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="password" className="text-sm font-medium">
            Senha
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            autoComplete="current-password"
            className="rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
        </div>
        <button
          type="submit"
          className="mt-2 rounded-md bg-green-700 px-4 py-2 text-sm font-semibold text-white hover:bg-green-800"
        >
          Entrar
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-500">
        Ainda não tem conta?{" "}
        <Link href="/register" className="font-medium text-green-700 hover:underline dark:text-green-400">
          Cadastre-se grátis
        </Link>
      </p>
    </div>
  );
}
