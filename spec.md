# Tendência Certa — Especificação Técnica (v1)

> Documento de planejamento. Nenhum código foi escrito ainda — este spec serve
> para alinhamento antes da implementação.

---

## 1. Modelo de Dados

Entidades principais e seus relacionamentos. Chaves primárias `id` são UUID.

### 1.1 `User`
| Campo | Tipo | Descrição |
|---|---|---|
| id | uuid | PK |
| email | string, unique | login |
| password_hash | string | hash (bcrypt/argon2) |
| name | string | |
| phone | string, nullable | para notificações WhatsApp/SMS futuras |
| role | enum: `admin`, `subscriber` | admin acessa o painel de criação manual de sinais |
| locale | string (`pt-BR`, `en`, `es`) | idioma preferido do usuário, default `pt-BR` |
| status | enum: `active`, `suspended`, `deleted` | |
| email_verified_at | timestamp, nullable | |
| created_at / updated_at | timestamp | |

### 1.2 `SubscriptionTier`
Catálogo de planos (não é por usuário — é a definição do produto).

| Campo | Tipo | Descrição |
|---|---|---|
| id | uuid | PK |
| code | enum: `basic`, `pro`, `vip` | identificador estável usado no código |
| name_i18n_key | string | chave de tradução do nome exibido (não string fixa) |
| price_cents | int | preço em centavos |
| currency | string | `BRL` (futuro: multi-moeda) |
| billing_interval | enum: `monthly`, `yearly` | |
| markets_allowed | string[] | quais mercados o tier libera (`crypto`, `forex`, `b3`) |
| signal_delay_minutes | int | atraso de entrega para não-tempo-real (0 = tempo real) |
| max_active_signals_visible | int, nullable | limite de sinais simultâneos visíveis, null = ilimitado |
| allows_vip_only_signals | bool | acesso a sinais marcados como exclusivos |
| push_notifications | bool | recebe push em tempo real |
| is_active | bool | plano pode ser contratado atualmente |

### 1.3 `Subscription`
Assinatura de um usuário a um tier, com histórico de mudanças.

| Campo | Tipo | Descrição |
|---|---|---|
| id | uuid | PK |
| user_id | uuid → User | |
| tier_id | uuid → SubscriptionTier | |
| status | enum: `trialing`, `active`, `past_due`, `canceled`, `expired` | |
| payment_provider | enum: `stripe`, `mercadopago`, `pagarme` | ver seção de arquitetura |
| external_subscription_id | string | id no provedor de pagamento |
| current_period_start / current_period_end | timestamp | |
| cancel_at_period_end | bool | |
| created_at / updated_at | timestamp | |

### 1.4 `Payment` (histórico de cobranças, para suporte/financeiro)
| Campo | Tipo |
|---|---|
| id | uuid |
| subscription_id | uuid → Subscription |
| amount_cents | int |
| currency | string |
| status | enum: `paid`, `failed`, `refunded`, `pending` |
| provider_reference | string |
| paid_at | timestamp, nullable |

### 1.5 `Market`
Mercado suportado (cripto, forex, ações/B3). Cadastro simples e estável.

| Campo | Tipo |
|---|---|
| id | uuid |
| code | enum: `crypto`, `forex`, `b3` |
| name_i18n_key | string |
| is_active | bool |

### 1.6 `Asset`
Ativo negociável dentro de um mercado (ex: BTC/USDT, EUR/USD, PETR4).

| Campo | Tipo |
|---|---|
| id | uuid |
| market_id | uuid → Market |
| symbol | string (ex: `BTCUSDT`, `EURUSD`, `PETR4`) |
| display_name | string |
| is_active | bool |

### 1.7 `Signal`
A entidade central do produto.

| Campo | Tipo | Descrição |
|---|---|---|
| id | uuid | PK |
| asset_id | uuid → Asset | |
| direction | enum: `buy`, `sell` | compra/venda |
| entry_price | numeric | |
| stop_loss | numeric | |
| timeframe | enum: `M1,M5,M15,M30,H1,H4,D1,W1` | |
| confidence_level | enum: `low`, `medium`, `high` (ou 1–5) | |
| source | enum: `manual`, `algorithm` | |
| created_by_admin_id | uuid → User, nullable | preenchido quando `source = manual` |
| algorithm_name | string, nullable | preenchido quando `source = algorithm` |
| visibility_tier | enum: `basic`, `pro`, `vip` | tier mínimo que enxerga o sinal (regra de gating) |
| status | enum: `pending`, `active`, `hit_target`, `hit_stop`, `expired`, `canceled` | ciclo de vida |
| notes | text, nullable | racional do sinal — texto livre do admin |
| published_at | timestamp, nullable | quando liberado (permite agendar) |
| closed_at | timestamp, nullable | |
| created_at / updated_at | timestamp | |

### 1.8 `SignalTarget`
Um sinal pode ter múltiplos alvos (TP1, TP2, TP3).

| Campo | Tipo |
|---|---|
| id | uuid |
| signal_id | uuid → Signal |
| order | int (1, 2, 3…) |
| target_price | numeric |
| hit_at | timestamp, nullable |

### 1.9 `Device` (para push mobile)
| Campo | Tipo |
|---|---|
| id | uuid |
| user_id | uuid → User |
| platform | enum: `ios`, `android`, `web` |
| push_token | string (token Expo/FCM) |
| last_seen_at | timestamp |

### 1.10 Nota sobre conteúdo multilíngue de dados (não só de UI)
Textos fixos de interface são resolvidos por arquivos de tradução (seção 4).
Mas `Signal.notes` é texto livre digitado pelo admin em português. **Decisão
para v1: `notes` fica em um único idioma (o do admin) e não é traduzido
automaticamente.** Se no futuro for necessário localizar o racional do sinal,
criar uma tabela `SignalTranslation (signal_id, locale, notes)` — o modelo já
foi desenhado para permitir essa extensão sem migração destrutiva.

---

## 2. Tiers de Assinatura

| Recurso | Basic | Pro | VIP |
|---|---|---|---|
| Mercados liberados | 1 (cripto) | Cripto + Forex + B3 | Cripto + Forex + B3 |
| Atraso de entrega do sinal | 30 min | Tempo real | Tempo real |
| Sinais simultâneos visíveis | até 5 | ilimitado | ilimitado |
| Sinais exclusivos VIP | não | não | sim |
| Notificação push em tempo real | não | sim | sim |
| Nível de confiança exibido | não | sim | sim |
| Alvos múltiplos (TP2/TP3) | só TP1 | todos | todos |
| Suporte | comunidade | prioritário | 1:1 |
| Preço sugerido | R$ | R$$ | R$$$ |

Regras de negócio derivadas do modelo:
- Gating de mercado e de atraso são resolvidos no backend (a API nunca envia
  ao cliente um sinal que o tier do usuário não deveria ver ainda).
- `visibility_tier` no `Signal` define o piso: um sinal `vip` nunca aparece
  para `basic`/`pro`, mesmo após o delay.
- Upgrade de tier é imediato, com cobrança proporcional (proration) do
  período restante do ciclo atual.
- Downgrade de tier só entra em vigor no início do próximo ciclo — o
  usuário mantém acesso ao tier atual até o fim do período já pago.

---

## 3. Arquitetura Geral

### 3.1 Stack proposta
- **Backend**: Python + FastAPI, para a API principal (usuários,
  assinaturas, sinais, autenticação, billing).
- **Motor de sinais (`signal-engine`)**: serviço Python **separado** desde
  o MVP, dedicado a rodar os algoritmos geradores de sinal. Mesma
  linguagem do backend (reaproveita bibliotecas de dados/ML), porém
  isolado como processo próprio — não roda dentro do FastAPI da API
  principal. Comunica-se com ela via fila Redis (publica sinais gerados)
  e/ou chamada a uma API interna de escrita, mantendo o acoplamento baixo
  e permitindo escalar/reiniciar os algoritmos de forma independente.
- **Banco de dados**: PostgreSQL (dados relacionais: usuários, assinaturas,
  sinais — todos com integridade referencial importante).
- **Fila/jobs assíncronos**: Redis + Celery (ou RQ) no backend principal
  para disparo de notificações push e fechamento de sinais (checagem de
  stop/alvo atingido). O mesmo Redis também serve de canal de comunicação
  com o `signal-engine`.
- **Web app**: Next.js (App Router), SSR para páginas públicas (landing,
  pricing) e CSR para o dashboard autenticado.
- **App mobile**: React Native via Expo, consumindo a mesma API REST.
- **Painel admin**: rotas protegidas dentro do próprio Next.js (role
  `admin`), reaproveitando componentes e a mesma API — evita construir um
  segundo frontend na v1.
- **Autenticação**: JWT (access token curto + refresh token), mesmo
  mecanismo para web e mobile.
- **Pagamentos**: Stripe **e** Mercado Pago/Pagar.me integrados em
  conjunto — Stripe para cartão internacional, Mercado Pago/Pagar.me para
  PIX e boleto no mercado brasileiro. O campo `payment_provider` em
  `Subscription` já identifica qual gateway processou cada assinatura.
- **Entrega em tempo real**: WebSocket (ou SSE) para push de sinais no
  dashboard web; Expo Push Notifications / FCM para mobile.
- **Infra**: Docker Compose em dev; **Railway** (ou Render/Fly.io) para o
  MVP — custo baixo e deploy simples para múltiplos serviços (API +
  signal-engine + Postgres + Redis). Migração para AWS fica em aberto para
  quando houver necessidade real de escalar.
- **CI/CD**: GitHub Actions (lint, testes, build).

### 3.2 Estrutura de repositório sugerida (monorepo)
```
/apps
  /api            -> FastAPI (backend principal: usuários, assinaturas, sinais, billing)
  /signal-engine  -> serviço Python separado com os algoritmos geradores de sinal
  /web            -> Next.js (site público + dashboard + admin UI)
  /mobile         -> Expo React Native
/packages
  /i18n           -> arquivos de tradução compartilhados (ver seção 4)
  /shared-types   -> tipos/contratos compartilhados entre web e mobile (gerados a partir do schema da API)
```

### 3.3 Fluxo de um sinal
1. Sinal é criado (admin via painel, ou pelo `signal-engine` via fila
   Redis/API interna) → grava `Signal` com `status = pending` e
   `published_at` definido.
2. Job de publicação libera o sinal (`status = active`) respeitando o
   `signal_delay_minutes` de cada tier — ou seja, o *mesmo* sinal pode
   já estar visível para VIP/Pro e ainda em delay para Basic.
3. API filtra sinais retornados por `visibility_tier` + delay conforme o
   tier do usuário autenticado.
4. Job de monitoramento de preço fecha o sinal (`hit_target`/`hit_stop`)
   e dispara notificação push para quem tem o sinal salvo/favoritado.

---

## 4. Estratégia de i18n

Objetivo: nascer em `pt-BR`, permitir adicionar `en`/`es` depois **sem
reescrever telas** — ou seja, nenhum texto literal em componentes desde o
primeiro commit.

### 4.1 Bibliotecas
- **Web (Next.js)**: [`next-intl`](https://next-intl-docs.vercel.app/) —
  integração nativa com App Router, suporta ICU message format
  (plural/gênero/interpolação) e roteamento por locale (`/pt-BR/...`,
  `/en/...`).
- **Mobile (Expo)**: `i18next` + `react-i18next` + `expo-localization`
  (detecta idioma do dispositivo como fallback inicial).
- Ambos usam o **mesmo formato de arquivo de tradução** (JSON com ICU),
  o que permite reaproveitar os arquivos de `packages/i18n` em web e
  mobile sem duplicar conteúdo.

### 4.2 Organização dos arquivos de tradução
Por **domínio/feature**, não por tela — evita duplicação quando uma
mesma string aparece em telas diferentes:

```
packages/i18n/
  locales/
    pt-BR/
      common.json       # botões, labels genéricos, ações
      auth.json         # login, cadastro, recuperação de senha
      subscription.json # planos, tiers, checkout, billing
      signals.json       # tudo relacionado a sinais (ativo, direção, alvo...)
      markets.json        # nomes de mercados/ativos exibidos
      admin.json         # painel administrativo
      errors.json         # mensagens de erro/validação
      notifications.json  # push/email
    en/
      (mesmos arquivos, mesma estrutura de chaves)
    es/
      (mesmos arquivos, mesma estrutura de chaves)
```

Regra: toda chave nova é criada primeiro em `pt-BR`; os outros locales
podem ficar com fallback em `pt-BR` até serem traduzidos (next-intl e
i18next suportam fallback de locale nativamente) — assim `en`/`es` podem
ser adicionados de forma incremental, sem bloquear a v1.

### 4.3 Regras de uso desde o primeiro componente
- Nenhuma string literal em JSX/TSX. Sempre `t('signals.direction.buy')`
  ou equivalente.
- Nomes de mercado/ativo/tier no banco (`name_i18n_key`) armazenam a
  **chave**, não o texto — o texto renderizado vem sempre do arquivo de
  tradução do locale ativo.
- Números, moeda e datas nunca formatados manualmente — usar `Intl`
  (via `next-intl`/`i18next`) para respeitar formato local (ex:
  `R$ 1.234,56` vs `$1,234.56`).
- Pluralização/gênero via ICU (`{count, plural, one {...} other {...}}`),
  suportado pelas duas libs escolhidas.
- Lint: adicionar `eslint-plugin-i18next` (ou regra equivalente) para
  barrar strings literais em componentes já na v1 — evita dívida técnica
  de retrabalho futuro.

### 4.4 Locale do usuário
- `User.locale` é persistido no backend e é a fonte de verdade quando o
  usuário está autenticado (sincroniza entre web e mobile).
- Para visitante não autenticado: detecta via `Accept-Language`
  (web) / locale do dispositivo (mobile), com **fallback para `pt-BR`**.
- Troca de idioma é uma preferência de perfil, refletida imediatamente
  na UI sem exigir reload de app/deploy.

### 4.5 Conteúdo gerado no backend (notificações/e-mails)
Push e e-mails são dedicados por sinal e precisam respeitar o idioma do
destinatário. Backend não deve montar strings direto: envia um **código de
mensagem + parâmetros** (ex: `signal.new_target_hit`, `{asset, target}`)
para o serviço de notificação, que resolve o texto final usando os mesmos
arquivos de `packages/i18n` (ou espelho em formato compatível com Python,
ex: `gettext`/Babel lendo o mesmo JSON). Isso mantém uma única fonte de
verdade de tradução entre frontend e backend.

---

## 5. Decisões Registradas (2026-07-20)
1. **Pagamento**: Stripe e Mercado Pago/Pagar.me integrados juntos —
   Stripe para cartão internacional, Mercado Pago/Pagar.me para PIX e
   boleto no Brasil.
2. **Motor de sinais**: serviço separado (`signal-engine`) desde o MVP,
   comunicação com a API principal via fila Redis e/ou API interna — não
   roda dentro do processo do backend FastAPI.
3. **Upgrade/downgrade de tier**: upgrade é imediato com cobrança
   proporcional (proration); downgrade só entra em vigor no fim do ciclo
   já pago.
4. **Hospedagem do MVP**: Railway (ou Render/Fly.io); migração para AWS
   fica em aberto para quando houver necessidade real de escalar.
