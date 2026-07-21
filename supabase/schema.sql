-- Tendência Certa — schema inicial
-- Rode este arquivo inteiro uma vez no SQL Editor do seu projeto Supabase
-- (Project > SQL Editor > New query > cole tudo > Run).

-- 1) Perfis -------------------------------------------------------------
-- Guarda o e-mail e a flag de admin de cada usuário. É criado
-- automaticamente (via trigger abaixo) sempre que alguém se cadastra.
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  is_admin boolean not null default false,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can view their own profile"
  on public.profiles for select
  to authenticated
  using (id = auth.uid());

-- Cria um profile automaticamente quando um usuário se cadastra.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 2) Sinais ---------------------------------------------------------------
create table if not exists public.signals (
  id uuid primary key default gen_random_uuid(),
  pair text not null,
  direction text not null check (direction in ('buy', 'sell')),
  entry_price numeric not null,
  stop_loss numeric not null,
  target_price numeric not null,
  timeframe text not null,
  created_by uuid references auth.users (id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.signals enable row level security;

-- Qualquer usuário cadastrado (logado) pode ver todos os sinais.
create policy "Authenticated users can view signals"
  on public.signals for select
  to authenticated
  using (true);

-- Só admins podem criar/editar/apagar sinais.
create policy "Admins can insert signals"
  on public.signals for insert
  to authenticated
  with check (
    exists (
      select 1 from public.profiles
      where profiles.id = auth.uid() and profiles.is_admin = true
    )
  );

create policy "Admins can update signals"
  on public.signals for update
  to authenticated
  using (
    exists (
      select 1 from public.profiles
      where profiles.id = auth.uid() and profiles.is_admin = true
    )
  )
  with check (
    exists (
      select 1 from public.profiles
      where profiles.id = auth.uid() and profiles.is_admin = true
    )
  );

create policy "Admins can delete signals"
  on public.signals for delete
  to authenticated
  using (
    exists (
      select 1 from public.profiles
      where profiles.id = auth.uid() and profiles.is_admin = true
    )
  );

-- Mantém updated_at em dia a cada edição.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_signals_updated_at on public.signals;
create trigger set_signals_updated_at
  before update on public.signals
  for each row execute procedure public.set_updated_at();

-- 3) Depois de rodar este script -----------------------------------------
-- 1. Cadastre-se normalmente pelo app (/register) com o e-mail que você
--    vai usar como admin.
-- 2. No Supabase: Table Editor > profiles > ache a linha com seu e-mail >
--    edite a coluna is_admin para true.
-- 3. Você agora tem acesso a /admin.
