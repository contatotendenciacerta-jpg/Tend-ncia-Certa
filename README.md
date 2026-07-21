# Tendência Certa

MVP de plataforma de sinais de Forex. Cadastro gratuito, sinais publicados
manualmente por um admin, PWA instalável no celular.

- **Stack**: Next.js (App Router) + Supabase (auth + banco) + Vercel (deploy)
- **Escopo**: só Forex, sem pagamento, sem múltiplos mercados, sem algoritmo
  automático — tudo isso fica para depois.

## 1. Configurar o Supabase

1. Crie um projeto em [supabase.com](https://supabase.com) (plano gratuito).
2. Vá em **SQL Editor > New query**, cole o conteúdo de
   [`supabase/schema.sql`](./supabase/schema.sql) e rode. Isso cria:
   - `profiles` (com a flag `is_admin`), populada automaticamente a cada
     cadastro;
   - `signals` (par, direção, entrada, stop, alvo, timeframe);
   - as políticas de RLS (usuários logados leem todos os sinais; só admins
     criam/editam/apagam).
3. Em **Project Settings > API**, copie:
   - **Project URL** → vai virar `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public key** → vai virar `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. (Opcional, recomendado para o MVP) Em **Authentication > Providers >
   Email**, desative "Confirm email" para que o cadastro libere acesso na
   hora, sem precisar clicar em link de e-mail. Se preferir manter a
   confirmação por e-mail, o app já tem uma rota pronta em `/auth/confirm`
   para lidar com o link — só garanta que o **Site URL** em
   **Authentication > URL Configuration** aponte para a URL do seu deploy.

### Virar admin

1. Cadastre-se normalmente pelo app em `/register`, com o e-mail que você
   vai usar como admin.
2. No Supabase: **Table Editor > profiles**, ache a linha com seu e-mail e
   mude `is_admin` para `true`.
3. Você agora tem acesso a `/admin`.

## 2. Variáveis de ambiente

Copie `.env.example` para `.env.local` e preencha:

```bash
cp .env.example .env.local
```

| Variável | De onde vem |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase > Project Settings > API > Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase > Project Settings > API > anon public key |
| `NEXT_PUBLIC_SITE_URL` | URL onde o app está rodando (`http://localhost:3000` local; a URL da Vercel em produção) |

## 3. Rodar localmente

```bash
npm install
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000).

## 4. Deploy na Vercel

1. Importe o repositório na Vercel.
2. Em **Settings > Environment Variables**, adicione as três variáveis da
   tabela acima (use a URL final da Vercel em `NEXT_PUBLIC_SITE_URL`).
3. Deploy. A Vercel detecta Next.js automaticamente, sem configuração
   extra.
4. Se você desativou a confirmação de e-mail, está pronto. Se manteve
   ativada, atualize o **Site URL** em Supabase > Authentication > URL
   Configuration para a URL de produção.

## Telas

- `/` — landing pública
- `/login`, `/register` — autenticação via Supabase Auth
- `/dashboard` — lista de sinais (requer login), mais recentes primeiro
- `/admin` — criar/editar/apagar sinais (requer `is_admin = true`)

## PWA

O app tem `manifest.webmanifest` (gerado por `src/app/manifest.ts`) e um
service worker (`public/sw.js`) registrado no layout. No celular, abra o
site e use "Adicionar à tela inicial" (Android/Chrome) ou "Adicionar à
Tela de Início" (iOS/Safari) para instalar. Depois da primeira visita
online, a última tela de sinais carregada fica disponível offline.
