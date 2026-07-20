# Deploy — Tendência Certa

Passo a passo para publicar o backend no Railway e o frontend na Vercel a
partir deste repositório. Ordem importa: o backend precisa existir antes
do frontend (para saber a URL da API), e o CORS só pode ser fechado
depois que a Vercel gerar a URL do frontend.

**Stripe e Mercado Pago são opcionais no primeiro deploy.** A API sobe
normalmente sem essas variáveis — só os endpoints `/billing/stripe/*` e
`/billing/mercadopago/*` retornam `503` ("pagamento ainda não
configurado") até você configurar. Para testar o produto sem pagamento
de verdade, use o endpoint de concessão manual de assinatura (seção 2).
Configurar Stripe/Mercado Pago de verdade é a seção 5, feita quando
quiser.

---

## 1. Backend na Railway

1. **railway.app → New Project → Deploy from GitHub repo** → selecione
   `contatotendenciacerta-jpg/tend-ncia-certa`.
2. Como é um monorepo, abra as **Settings** do serviço criado e defina
   **Root Directory** = `apps/api`. A Railway vai então encontrar o
   `Dockerfile` e o `railway.json` que já estão nessa pasta (build via
   Docker, roda `alembic upgrade head` antes do `uvicorn` a cada boot).
3. **Adicione um Postgres**: no mesmo projeto, **New → Database → Add
   PostgreSQL**.
4. Na aba **Variables** do serviço da API, configure só o essencial para
   o primeiro deploy (tabela completa na seção 4):
   - `DATABASE_URL` — **não** cole o valor bruto que a Railway gera para
     o Postgres. Ele vem como `postgresql://...` (driver psycopg2), mas
     o projeto usa **psycopg3**. Duas formas de resolver:
     - **Referência (recomendado, se atualiza sozinho)**:
       ```
       postgresql+psycopg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
       ```
       (troque `Postgres` pelo nome exato do serviço de banco, visível na
       aba Variables dele, caso você tenha renomeado)
     - **Manual (mais simples)**: copie o `DATABASE_URL` que a Railway
       gerou para o Postgres e cole como valor, só trocando o começo de
       `postgresql://` para `postgresql+psycopg://`.
   - `JWT_SECRET_KEY` — gere com `openssl rand -hex 32` no seu terminal.
   - `CORS_ORIGINS` — deixe `["http://localhost:3000"]` por enquanto;
     atualiza na seção 4 depois que a Vercel existir.
   - **Não precisa** definir `STRIPE_*` / `MERCADOPAGO_*` agora.
5. Deploy. Depois de subir, vá em **Settings → Networking → Generate
   Domain** para obter a URL pública (algo como
   `https://tendencia-certa-api-production.up.railway.app`).
6. Confirme abrindo `https://<sua-url>/docs` — deve abrir o Swagger UI.

## 2. Seed de dados de teste

Com o serviço no ar, rode o script de seed uma vez (ele é idempotente —
pode rodar de novo sem duplicar nada):

- Pelo painel: abra o serviço → aba do deployment ativo → **Shell** (ou
  o botão de terminal) e rode:
  ```
  python scripts/seed_demo_data.py
  ```
- Ou, se instalar o Railway CLI localmente e linkar o projeto:
  ```
  railway run python scripts/seed_demo_data.py
  ```

Isso cria os 3 tiers (Básico/Pro/VIP), um mercado cripto com 2 ativos
(BTCUSDT, ETHUSDT), um usuário admin, um assinante demo com plano Pro
ativo, e 2 sinais de exemplo. As credenciais aparecem no output do
script:

```
Admin login:  admin@tendenciacerta.com / admin12345
Demo login:   demo@tendenciacerta.com / demo12345
```

Troque as duas senhas assim que confirmar o acesso.

### Testar planos sem Stripe/Mercado Pago

O seed já deixa o usuário demo com um plano Pro ativo. Para testar outro
tier, ou dar acesso a outro usuário sem passar pelo checkout, use (como
admin, via `/docs` ou `curl`):

```
POST /admin/users/{user_id}/grant-subscription
{"tier_id": "<id de um tier>", "duration_days": 30}
```

Isso ativa a assinatura na hora, sem cobrar nada e sem depender de
Stripe/Mercado Pago — registrada com `payment_provider = manual` para
não se confundir com pagamento de verdade. É só para teste; não é uma
funcionalidade exposta ao produto.

## 3. Frontend na Vercel

1. **vercel.com → Add New → Project** → importe o mesmo repositório
   GitHub.
2. Em "Configure Project", defina **Root Directory** = `apps/web`. A
   Vercel detecta Next.js automaticamente — não precisa mexer em build
   command.
3. Em **Environment Variables**, adicione:
   - `API_BASE_URL` = a URL do Railway obtida no passo 1.6 (ex:
     `https://tendencia-certa-api-production.up.railway.app`, **sem**
     barra no final)
4. Deploy. A Vercel te dá uma URL tipo
   `https://tendencia-certa-web.vercel.app`.

## 4. Fechar o CORS

Volte na Railway, na aba Variables do serviço da API, e atualize:

```
CORS_ORIGINS=["https://tendencia-certa-web.vercel.app"]
```

(troque pela URL real que a Vercel gerou; mantenha os colchetes e aspas
— é lido como JSON). Se você tiver múltiplas origens (ex: um domínio
próprio depois), é só listar todas no array. Redeploy/restart o serviço
da API pra aplicar.

Neste ponto você já tem o produto no ar, testável de ponta a ponta
(cadastro, login, dashboard, conta) sem nenhuma configuração de
pagamento.

---

## 5. Configurar pagamento de verdade (Stripe / Mercado Pago) — quando quiser

Nenhuma dessas eu posso inventar por você — vêm de um serviço externo ou
precisam ser geradas localmente por você para nunca aparecer em texto
compartilhado. Enquanto não configurar, `/billing/stripe/*` e
`/billing/mercadopago/*` respondem `503`; todo o resto do produto
continua funcionando normalmente.

| Variável | Onde | De onde vem |
|---|---|---|
| `STRIPE_API_KEY` | Railway (API) | Sua chave secreta em [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys) (comece com a de teste, `sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Railway (API) | Gerado pelo Stripe ao criar um webhook endpoint apontando para `https://<url-da-api>/billing/stripe/webhook` |
| `MERCADOPAGO_ACCESS_TOKEN` | Railway (API) | Painel de credenciais do Mercado Pago (Access Token de teste ou produção) |
| `MERCADOPAGO_WEBHOOK_SECRET` | Railway (API) | Gerado ao configurar a notificação/webhook no painel do Mercado Pago apontando para `https://<url-da-api>/billing/mercadopago/webhook` |

Depois de configurar as quatro, redeploy/restart o serviço da API — os
endpoints de billing passam a funcionar sem mais nenhuma mudança de
código.

### Variáveis que já têm um default razoável (mexa só se quiser)

- `JWT_ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (15),
  `REFRESH_TOKEN_EXPIRE_DAYS` (30)
- `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` / `MERCADOPAGO_SUCCESS_URL` /
  `MERCADOPAGO_FAILURE_URL` / `MERCADOPAGO_PENDING_URL` — hoje não há
  telas de checkout no frontend ainda, então esses redirects não são
  exercitados de verdade. Quando o checkout for implementado, aponte-os
  para páginas reais no domínio da Vercel (por ora podem continuar
  apontando pro `/account`).
- `REDIS_URL` — nada na API usa Redis ainda (é usado pelo `signal-engine`,
  que ainda não roda em produção). Não precisa provisionar um Redis na
  Railway agora.

### Não é preciso preencher manualmente

- `DATABASE_URL` do lado do **plugin** Postgres (a própria Railway
  gera) — só a variável do **serviço da API** precisa da correção de
  esquema acima.

---

## Resumo — variáveis do primeiro deploy

| Variável | Onde | De onde vem |
|---|---|---|
| `DATABASE_URL` | Railway (API) | Gerada pelo plugin Postgres — só ajuste o esquema para `postgresql+psycopg://` (seção 1) |
| `JWT_SECRET_KEY` | Railway (API) | **Gere você**: rode `openssl rand -hex 32` no seu terminal e cole o resultado |
| `CORS_ORIGINS` | Railway (API) | `["http://localhost:3000"]` no início; URL da Vercel depois (seção 4) |
| `API_BASE_URL` | Vercel (web) | URL pública gerada pelo Railway (seção 1.5) |

`STRIPE_*` e `MERCADOPAGO_*` ficam para a seção 5, quando quiser ativar
pagamento de verdade.
