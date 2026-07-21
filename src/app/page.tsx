import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-6">
        <span className="font-semibold">Tendência Certa</span>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/login" className="hover:underline">
            Entrar
          </Link>
          <Link
            href="/register"
            className="rounded-md bg-green-700 px-3 py-1.5 font-medium text-white hover:bg-green-800"
          >
            Cadastrar grátis
          </Link>
        </nav>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-16 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Sinais de Forex,{" "}
          <span className="text-green-700 dark:text-green-500">direto ao ponto</span>
        </h1>
        <p className="mt-4 max-w-xl text-lg text-zinc-600 dark:text-zinc-400">
          Cadastre-se grátis e acompanhe sinais de compra e venda no mercado de
          câmbio: par de moedas, entrada, stop loss e alvo, tudo em um só
          lugar.
        </p>
        <div className="mt-8 flex gap-4">
          <Link
            href="/register"
            className="rounded-md bg-green-700 px-6 py-3 font-semibold text-white hover:bg-green-800"
          >
            Criar conta grátis
          </Link>
          <Link
            href="/login"
            className="rounded-md border border-zinc-300 px-6 py-3 font-semibold hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            Já tenho conta
          </Link>
        </div>

        <dl className="mt-16 grid grid-cols-1 gap-6 text-left sm:grid-cols-3">
          <div>
            <dt className="font-semibold">Sinais manuais</dt>
            <dd className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Cada sinal é publicado manualmente, com par, direção, entrada,
              stop e alvo.
            </dd>
          </div>
          <div>
            <dt className="font-semibold">100% grátis por enquanto</dt>
            <dd className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Cadastro livre, sem cobrança nesta fase.
            </dd>
          </div>
          <div>
            <dt className="font-semibold">Instalável no celular</dt>
            <dd className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Adicione à tela inicial e acesse como um app.
            </dd>
          </div>
        </dl>
      </main>

      <footer className="mx-auto w-full max-w-3xl px-4 py-6 text-center text-xs text-zinc-500">
        Tendência Certa — sinais de Forex. Não é recomendação de investimento.
      </footer>
    </div>
  );
}
