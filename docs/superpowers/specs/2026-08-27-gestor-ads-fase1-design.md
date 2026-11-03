# Gestor Ads — Fase 1: Backend Foundation

> Design spec do backend unificado que serve o Campaign Optimizer (web) e o Gestor de Tráfego via WhatsApp (SaaS).
>
> Deploy: `ads.creativeagenciamkt.com.br`

---

## 1. Visão geral

Dois produtos, um backend:

1. **Campaign Optimizer** — dashboard web para análise, otimização e gestão de campanhas (evolução do Streamlit atual).
2. **Gestor de Tráfego via WhatsApp** — SaaS que permite criar, ativar, monitorar e otimizar campanhas de Meta Ads conversando por WhatsApp.

A Fase 1 entrega a fundação: auth, conexão Meta, leitura+escrita na Marketing API, engine de regras, análise IA e auditoria. Sem frontend web (Fase 2) e sem agente WhatsApp (Fase 3).

### Princípios

- **Multi-tenant desde o dia 1** — Supabase RLS com `user_id = auth.uid()` em toda tabela.
- **Campanha sempre PAUSED** — criação em rascunho, aprovação explícita, ativação separada.
- **Advantage+ desligado por padrão** — segmentação automática só se o usuário pedir.
- **Fallback determinístico** — se a IA falhar, a análise funciona sem ela.
- **Core channel-agnostic** — regras, KPIs e nomenclatura são os mesmos para web e WhatsApp.

---

## 2. Stack e infraestrutura

| Camada | Escolha | Motivo |
|--------|---------|--------|
| Backend | Python 3.12 + FastAPI | Equipe de 3 pessoas, velocidade de entrega, ecossistema de dados |
| Banco | Supabase (PostgreSQL + RLS + Auth + Storage) | Auth pronto, RLS nativo, Storage para criativos |
| HTTP client | httpx (async) | Suporte a async para chamadas Meta em paralelo |
| LLM | Claude Sonnet 5 (Anthropic SDK) | Substituindo OpenAI do código atual, melhor custo-benefício |
| Criptografia | cryptography (Fernet) | Tokens Meta criptografados em repouso |
| Testes | pytest + respx | Mock de chamadas HTTP, sem depender de API real |
| Lint | ruff | Rápido, unifica linter + formatter |
| Deploy | Railway ou Render | SSL automático, deploy por push, escala vertical |
| CI | GitHub Actions | pytest + ruff → deploy automático se verde |
| Domínio | `ads.creativeagenciamkt.com.br` | CNAME para o provider de deploy |

### Dependências principais (pyproject.toml)

```
fastapi >= 0.115
uvicorn[standard] >= 0.32
httpx >= 0.28
supabase >= 2.12
anthropic >= 0.45
cryptography >= 44.0
pydantic >= 2.10
python-jose[cryptography] >= 3.3
python-multipart >= 0.0.18
pydantic-settings >= 2.7
ruff >= 0.8 (dev)
pytest >= 8.3 (dev)
respx >= 0.22 (dev)
```

---

## 3. Estrutura do projeto

```
gestor-ads/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, middlewares, exception handlers
│   │   ├── config.py            # Settings via pydantic-settings (env vars)
│   │   ├── dependencies.py      # get_current_user, get_supabase, get_meta_client
│   │   │
│   │   ├── auth/
│   │   │   ├── router.py        # POST /register, /login, /meta/login, /meta/callback
│   │   │   ├── meta_oauth.py    # OAuth Meta: gera URL, troca code, estende token
│   │   │   └── models.py        # Pydantic schemas de auth
│   │   │
│   │   ├── meta/
│   │   │   ├── router.py        # GET /accounts, /campaigns, POST /sync, /drafts, etc.
│   │   │   ├── client.py        # MetaAdsClient — leitura e escrita na Graph API
│   │   │   ├── schemas.py       # Pydantic schemas de campanhas, insights, etc.
│   │   │   ├── token_manager.py # Encrypt, decrypt, extend, refresh, revoke
│   │   │   └── rate_limiter.py  # Controle de rate limit por conta
│   │   │
│   │   ├── core/
│   │   │   ├── rules.py         # Engine de regras (migrado + expandido)
│   │   │   ├── analysis.py      # Análise IA com Claude + fallback determinístico
│   │   │   ├── kpis.py          # Agregador de KPIs
│   │   │   └── naming.py        # Nomenclatura padronizada
│   │   │
│   │   ├── clients/
│   │   │   ├── router.py        # CRUD de contas e criativos
│   │   │   └── schemas.py
│   │   │
│   │   └── shared/
│   │       ├── audit.py         # Decorator @audit_write + query de logs
│   │       ├── crypto.py        # Fernet wrapper (encrypt_token, decrypt_token)
│   │       └── exceptions.py    # Hierarquia de erros padronizada
│   │
│   ├── migrations/              # SQL migrations (Supabase CLI)
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
│
├── web/                         # Fase 2 — Next.js (vazio por ora)
└── docs/superpowers/specs/      # Este documento
```

---

## 4. Modelo de dados (Supabase)

### 4.1 Tabelas

```sql
-- Extensão para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. profiles — estende auth.users
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    telefone_e164 TEXT,
    nivel_tecnico TEXT NOT NULL DEFAULT 'avancado'
        CHECK (nivel_tecnico IN ('leigo', 'avancado')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. meta_connections — tokens OAuth criptografados
CREATE TABLE meta_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meta_user_id TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    is_valid BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, meta_user_id)
);

-- 3. ad_accounts — contas de anúncio vinculadas
CREATE TABLE ad_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    connection_id UUID NOT NULL REFERENCES meta_connections(id) ON DELETE CASCADE,
    act_id TEXT NOT NULL,
    nome TEXT NOT NULL DEFAULT '',
    business_id TEXT,
    moeda TEXT NOT NULL DEFAULT 'BRL',
    fuso TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    -- thresholds configuráveis por conta (migrados do campaign_optimizer)
    target_cpl REAL DEFAULT 0,
    waste_limit REAL DEFAULT 100,
    min_ctr REAL DEFAULT 0.8,
    max_frequency REAL DEFAULT 3.0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, act_id)
);

-- 4. campaigns — campanhas confirmadas no Meta
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meta_campaign_id TEXT NOT NULL,
    nome TEXT NOT NULL,
    objetivo TEXT,
    status TEXT NOT NULL DEFAULT 'PAUSED',
    verba_diaria REAL,
    verba_total REAL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(ad_account_id, meta_campaign_id)
);

-- 5. campaign_metrics — métricas diárias por campanha
CREATE TABLE campaign_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    data DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    cpc REAL DEFAULT 0,
    cpm REAL DEFAULT 0,
    frequency REAL DEFAULT 0,
    spend REAL DEFAULT 0,
    leads INTEGER DEFAULT 0,
    cpl REAL DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    raw_json JSONB DEFAULT '{}',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(campaign_id, data)
);

-- 6. campaign_drafts — rascunhos antes de enviar ao Meta
CREATE TABLE campaign_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    payload JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'rascunho'
        CHECK (status IN ('rascunho', 'aprovado', 'publicando', 'criado', 'erro')),
    meta_campaign_id TEXT,
    erro_detalhes TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. creatives — criativos (imagem/vídeo) armazenados
CREATE TABLE creatives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('image', 'video')),
    storage_path TEXT NOT NULL,
    meta_hash TEXT,
    meta_video_id TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 8. audit_log — log de toda escrita na Marketing API
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    acao TEXT NOT NULL,
    entidade TEXT NOT NULL,
    entidade_id TEXT,
    request JSONB DEFAULT '{}',
    response JSONB DEFAULT '{}',
    origem TEXT NOT NULL DEFAULT 'api',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4.2 Row Level Security (RLS)

Toda tabela tem a mesma policy base:

```sql
ALTER TABLE <tabela> ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário vê só seus dados" ON <tabela>
    FOR ALL USING (user_id = auth.uid());
```

Para `campaign_metrics`, o `user_id` é redundante (poderia fazer join com campaigns), mas está na tabela para que a policy funcione direto sem join — performance e simplicidade.

### 4.3 Trigger de profiles

```sql
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, nome)
    VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'nome', ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

---

## 5. Autenticação e OAuth Meta

### 5.1 Auth Supabase

Registro e login via Supabase Auth (email + senha). O backend valida o JWT do Supabase em cada request:

```python
# app/dependencies.py
async def get_current_user(
    authorization: str = Header(...),
    supabase: Client = Depends(get_supabase),
) -> User:
    token = authorization.replace("Bearer ", "")
    user = supabase.auth.get_user(token)
    if not user:
        raise TokenInvalidError()
    return User(id=user.user.id, email=user.user.email)
```

### 5.2 OAuth Meta — fluxo completo

```
1. Frontend chama GET /api/auth/meta/login
2. Backend gera state JWT (user_id + timestamp + nonce) e retorna URL:
   https://www.facebook.com/v23.0/dialog/oauth
     ?client_id={META_APP_ID}
     &redirect_uri={META_REDIRECT_URI}
     &scope=ads_management,ads_read,business_management,pages_show_list
     &state={state_jwt}

3. Usuário autoriza no Meta, redireciona para:
   GET /api/auth/meta/callback?code=xxx&state=yyy

4. Backend:
   a. Valida state JWT (assinatura + expiração de 10 min)
   b. Troca code por short-lived token (POST oauth/access_token)
   c. Troca short-lived por long-lived token (60 dias)
   d. Criptografa com Fernet e salva em meta_connections
   e. Lista ad accounts via /me/adaccounts e salva em ad_accounts
   f. Redireciona para o frontend com sucesso
```

### 5.3 TokenManager

```python
class TokenManager:
    def __init__(self, fernet_key: str):
        self.fernet = Fernet(fernet_key.encode())

    def encrypt(self, token: str) -> str:
        """Criptografa token para armazenamento."""

    def decrypt(self, encrypted: str) -> str:
        """Descriptografa para uso em chamadas API."""

    async def exchange_code(self, code: str) -> TokenPair:
        """code → short-lived → long-lived token."""

    async def extend_token(self, short_lived: str) -> TokenPair:
        """Short-lived → long-lived (60 dias)."""

    async def refresh_if_needed(self, connection_id: str) -> str:
        """Se token vence em < 7 dias, estende automaticamente.
           Se falhar, marca is_valid=false."""

    async def revoke(self, connection_id: str) -> None:
        """Revoga token no Meta e remove do banco."""
```

**Segurança:**
- `FERNET_KEY` vive apenas no env do backend — nunca no Supabase, nunca no frontend.
- Token descriptografado existe apenas em memória durante a chamada API.
- Nenhum endpoint retorna o token descriptografado.

---

## 6. Meta Ads Client

### 6.1 Classe principal

Evolução do `MetaAdsConnector` atual (que é read-only, usa `requests` sync e token de env var) para um client multi-tenant, async, com read+write.

```python
class MetaAdsClient:
    """Client para Meta Marketing API v23.0 — leitura e escrita."""

    BASE = "https://graph.facebook.com/v23.0"

    def __init__(
        self,
        access_token: str,       # já descriptografado
        act_id: str,             # formato act_123456
        rate_limiter: RateLimiter,
    ):
        self.token = access_token
        self.act_id = act_id
        self.limiter = rate_limiter
        self.http = httpx.AsyncClient(timeout=30)

    # === LEITURA ===

    async def get_account_info(self) -> dict:
        """Retorna id, name, account_status, currency, timezone_name."""

    async def list_campaigns(self, limit: int = 200) -> list[dict]:
        """Lista campanhas com paginação automática (max 10 páginas).
           Campos: id, name, objective, status, daily_budget, lifetime_budget."""

    async def get_insights(
        self,
        object_id: str,
        date_preset: str = "last_7d",
        level: str = "campaign",
    ) -> list[dict]:
        """Puxa métricas agregadas.
           Campos: impressions, reach, clicks, ctr, cpc, cpm, spend,
                   frequency, actions, cost_per_action_type.
           Extrai leads de actions usando _extract_metric (mantido do código atual)."""

    async def list_adsets(self, campaign_id: str) -> list[dict]:
    async def list_ads(self, adset_id: str) -> list[dict]:

    # === ESCRITA (todas logadas via @audit_write) ===

    @audit_write(action="create_campaign", entity="campaign")
    async def create_campaign(self, payload: CampaignCreatePayload) -> dict:
        """Cria campanha sempre com status=PAUSED.
           Advantage+ targeting desabilitado por padrão."""

    @audit_write(action="create_adset", entity="adset")
    async def create_adset(self, campaign_id: str, payload: AdSetPayload) -> dict:

    @audit_write(action="create_ad", entity="ad")
    async def create_ad(self, adset_id: str, creative_id: str, payload: AdPayload) -> dict:

    @audit_write(action="upload_image", entity="creative")
    async def upload_image(self, file_bytes: bytes, filename: str) -> dict:
        """Upload via POST /{act_id}/adimages. Retorna hash."""

    @audit_write(action="update_status", entity="campaign")
    async def update_status(self, entity_id: str, status: str) -> dict:
        """Altera status (ACTIVE, PAUSED). Usado para ativar após aprovação."""

    # === INTERNO ===

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Wrapper que:
           1. Checa rate limiter antes de chamar
           2. Faz a request com httpx
           3. Lê header X-Business-Use-Case-Usage e atualiza limiter
           4. Se erro 4/17 (rate limit), levanta MetaRateLimitError
           5. Se erro genérico, levanta MetaAPIError com code+subcode
        """

    @staticmethod
    def _extract_metric(items: list[dict] | None, match_terms: tuple[str, ...]) -> float:
        """Mantido do MetaAdsConnector atual.
           Percorre actions/cost_per_action_type procurando termos como
           'messaging_conversation_started', 'lead', 'contact', 'omni_lead'."""
```

### 6.2 Migração do código atual

| Código atual (`campaign_optimizer`) | Código novo (`gestor-ads`) | Mudança |
|-------------------------------------|---------------------------|---------|
| `MetaAdsConnector.validate()` | `MetaAdsClient.get_account_info()` | Token vem do banco, não de env var |
| `MetaAdsConnector.fetch_campaign_snapshot()` | `MetaAdsClient.get_insights()` + `list_campaigns()` | Async, paginação separada, rate limit |
| `MetaAdsConnector._extract_metric()` | `MetaAdsClient._extract_metric()` | Mantido igual — lógica comprovada |
| `BaseAdsConnector.pause_entity()` (dry-run) | `MetaAdsClient.update_status()` | Execução real via API, com auditoria |
| Token de `os.getenv("META_ACCESS_TOKEN")` | Token descriptografado por `TokenManager` | Multi-tenant, criptografado |

### 6.3 Rate Limiter

```python
class RateLimiter:
    """Controla rate limit por conta de anúncio, usando
       o header X-Business-Use-Case-Usage da Graph API."""

    def __init__(self):
        self._usage: dict[str, AccountUsage] = {}

    def update_from_header(self, act_id: str, header_value: str) -> None:
        """Parseia o header JSON e atualiza o estado da conta."""

    def check(self, act_id: str) -> RateLimitStatus:
        """
        Retorna:
        - OK: usage < 75%, pode chamar
        - THROTTLE: 75-95%, esperar throttle_seconds antes de chamar
        - BLOCKED: > 95%, não chamar, levanta MetaRateLimitError
        """

    @property
    def throttle_seconds(self) -> int:
        """Tempo de espera sugerido quando em THROTTLE."""
```

### 6.4 Auditoria

```python
# app/shared/audit.py

def audit_write(action: str, entity: str):
    """Decorator para métodos de escrita do MetaAdsClient.

    Antes de chamar o Meta:
    - Registra request payload no audit_log com status 'pending'

    Depois:
    - Atualiza com response e status 'success' ou 'error'
    - Inclui user_id, ação, entidade, entity_id, timestamps

    Exemplo de log:
    {
        user_id: "uuid-do-usuario",
        acao: "create_campaign",
        entidade: "campaign",
        entidade_id: "123456789",
        request: {"name": "[FORTEC]...", "objective": "OUTCOME_LEADS", ...},
        response: {"id": "123456789"},
        origem: "api"
    }
    """
```

---

## 7. Core compartilhado

O core contém a lógica de negócio que tanto o dashboard web (Fase 2) quanto o agente WhatsApp (Fase 3) consomem. Funções puras: recebem dados, retornam resultado.

### 7.1 Rules Engine

Migrado de `campaign_optimizer/core/rules.py`, expandido para multi-tenant e com novas regras.

```python
# app/core/rules.py

@dataclass
class RuleResult:
    severity: str           # 'vermelho' | 'amarelo' | 'verde'
    rule_name: str          # 'gasto_sem_lead', 'cpl_alto'...
    action: str             # 'pausar', 'revisar', 'escalar', 'trocar_criativo_ou_copy'
    campaign: str
    entity_level: str       # 'campaign' | 'adset' | 'ad'
    entity_name: str
    reason: str             # explicação em PT-BR
    should_pause: bool
    meta_entity_id: str | None = None  # para ação direta via API

@dataclass
class AccountThresholds:
    """Configurável por ad_account — não mais hardcoded."""
    target_cpl: float = 0
    waste_limit: float = 100
    min_ctr: float = 0.8
    max_frequency: float = 3.0

def evaluate(
    metrics: list[dict],
    thresholds: AccountThresholds,
) -> list[RuleResult]:
    """Roda todas as regras e retorna resultados ordenados por severidade."""
```

**Regras da Fase 1:**

| # | Regra | Severidade | Condição | Ação | Origem |
|---|-------|-----------|----------|------|--------|
| 1 | `gasto_sem_lead` | 🔴 vermelho | spend ≥ waste_limit E leads = 0 | pausar | migrada do code atual |
| 2 | `cpl_acima_meta` | 🟡 amarelo | leads > 0 E cpl > target_cpl × 1.3 | revisar | migrada (threshold com margem 30%) |
| 3 | `ctr_baixo` | 🟡 amarelo | ctr > 0 E ctr < min_ctr | trocar_criativo_ou_copy | migrada |
| 4 | `frequencia_alta` | 🟡 amarelo | frequency > max_frequency | trocar_criativo_ou_publico | migrada |
| 5 | `sem_impressao` | 🔴 vermelho | spend > 0 E impressions = 0 | revisar_conta | nova |
| 6 | `criativo_reprovado` | 🔴 vermelho | effective_status = DISAPPROVED | trocar_criativo | nova |

Diferença do código atual: os thresholds vêm de `ad_accounts` (banco), não de `client` dict. O resultado inclui `meta_entity_id` para que o frontend ou agente possa executar a ação via API.

### 7.2 KPI Aggregator

Migrado de `campaign_optimizer/core/rules.py` (`summarize_kpis`), expandido:

```python
# app/core/kpis.py

@dataclass
class KPISummary:
    total_spend: float
    total_leads: int
    total_clicks: int
    total_impressions: int
    cpl_medio: float
    cpc_medio: float
    ctr_medio: float
    melhor_campanha: str | None    # menor CPL com volume relevante
    pior_campanha: str | None      # maior CPL ou gasto sem lead
    tendencia: str                 # 'subindo' | 'estavel' | 'caindo'

def summarize_kpis(metrics: list[dict]) -> KPISummary:
    """Agrega métricas do período.
       Lógica base mantida do código atual (spend, leads, clicks, impressions → CPL, CPC, CTR).
       Adicionado: melhor/pior campanha e tendência (comparando 1ª e 2ª metade do período)."""
```

### 7.3 Análise IA

Migrado de `campaign_optimizer/core/ai.py`, trocando OpenAI por Claude:

```python
# app/core/analysis.py

async def analyze_performance(
    metrics: list[dict],
    thresholds: AccountThresholds,
    nivel_tecnico: str = 'avancado',
    model: str = 'claude-sonnet-5',
) -> AnalysisResult:
    """
    1. Roda evaluate() para ter os fatos (regras objetivas)
    2. Agrega KPIs via summarize_kpis()
    3. Envia contexto + regras para Claude
    4. Retorna: resumo, recomendações, ações sugeridas

    O nivel_tecnico muda apenas o prompt — mesma análise, linguagem diferente:
    - avancado: "CTR de 0,8% abaixo do piso de 1,2%. Criativos com fadiga."
    - leigo: "De cada 1.000 pessoas que veem seu anúncio, só 8 clicam.
              Precisamos de uma imagem ou vídeo mais chamativo."
    """

async def generate_campaign_strategy(
    briefing: CampaignBriefing,
    account_history: list[dict] | None,
    nivel_tecnico: str = 'avancado',
) -> CampaignStrategy:
    """
    Gera estratégia completa com justificativa:
    - Verba diária × período (ex: R$50/dia × 20 dias > R$33/dia × 30 dias
      porque abaixo de certo diário o algoritmo demora a sair do aprendizado)
    - CBO ou ABO, nº de conjuntos
    - Público sugerido (geo + raio, idade, gênero, segmentação)
    - Copy sugerida (primary text, headline, description)
    - Fase de teste (primeiros ~7 dias) vs fase de otimização
    """

def fallback_analysis(metrics: list[dict], alerts: list[dict]) -> str:
    """Análise determinística quando Claude falhar.
       Mantida do código atual com ajustes de formatação.
       Prioriza: gasto sem lead > CTR > frequência > CPL."""
```

**Migração da IA:**
- OpenAI (`gpt-5-mini`) → Anthropic (`claude-sonnet-5`)
- `client_api.responses.create()` → `anthropic.messages.create()`
- Prompt base mantido: "analista de tráfego da Creative Agência Marketing"
- Fallback determinístico mantido na íntegra — funciona sem API key

### 7.4 Nomenclatura

```python
# app/core/naming.py

def campaign_name(marca: str, objetivo: str, publico: str) -> str:
    """[MARCA] | objetivo | publico | AAAAMMDD-HHMM

    Exemplo:
    [FORTEC] | leads-whatsapp | sp-25-45-imoveis | 20260827-1430
    """

def adset_name(marca: str, segmento: str) -> str:
    """[MARCA] | segmento | AAAAMMDD-HHMM"""

def ad_name(marca: str, criativo: str) -> str:
    """[MARCA] | criativo-desc | AAAAMMDD-HHMM"""
```

O timestamp evita ambiguidade quando o usuário sobe campanhas parecidas no mesmo dia.

### 7.5 Diagrama do core

```
┌──────────────┐     ┌──────────────┐
│  Dashboard   │     │   WhatsApp   │
│  (REST API)  │     │   (Agent)    │
│  Fase 2      │     │   Fase 3     │
└──────┬───────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                │
       ┌────────▼────────┐
       │     CORE        │
       │  rules.py       │
       │  analysis.py    │
       │  kpis.py        │
       │  naming.py      │
       └────────┬────────┘
                │
       ┌────────▼────────┐
       │  META CLIENT    │
       │  client.py      │
       │  token_manager  │
       │  rate_limiter   │
       └─────────────────┘
```

O core nunca sabe se quem chamou foi o web ou o WhatsApp. Recebe dados, retorna resultado.

---

## 8. Fluxo de Sync (Meta → Supabase)

### 8.1 POST /api/campaigns/sync

```
1. Busca token da meta_connection do usuário
   → Token expirado? refresh_if_needed()
   → Token inválido (is_valid=false)? retorna 401 com "Reconecte sua conta"

2. Lista campanhas da conta via API
   → Rate limit > 75%? throttle (sleep + retry)
   → Rate limit > 95%? aborta com MetaRateLimitError

3. Para cada campanha:
   a. Upsert em campaigns (meta_campaign_id como chave de dedup)
   b. Fetch insights (date_preset do request, default last_7d)
   c. Upsert em campaign_metrics (UNIQUE campaign_id+data previne duplicata)
   d. Extrai leads de actions usando _extract_metric() — mesma lógica
      do MetaAdsConnector atual: procura "messaging_conversation_started",
      "lead", "contact", "omni_lead"

4. Retorna resumo:
   {
     "campaigns_synced": 8,
     "metrics_upserted": 56,
     "errors": [
       {"campaign": "...", "error": "Campaign deleted on Meta"}
     ]
   }
```

**Sync parcial:** Se 8 de 10 campanhas sincronizam e 2 falham, o sync retorna sucesso com a lista de erros — nunca falha tudo por causa de uma campanha.

### 8.2 Fluxo de criação (drafts → campaigns)

```
1. POST /api/campaigns/drafts
   → Cria rascunho em campaign_drafts (status: 'rascunho')
   → Valida payload: objetivo, verba, nome, público
   → Se inválido: retorna 422 com detalhes

2. PATCH /api/campaigns/drafts/{id}
   → Atualiza payload do rascunho

3. POST /api/campaigns/drafts/{id}/publish
   → Muda status para 'publicando'
   → Chama MetaAdsClient.create_campaign() com status=PAUSED
   → Se sucesso: status='criado', salva meta_campaign_id, cria em campaigns
   → Se erro: status='erro', salva erro_detalhes

4. POST /api/campaigns/{id}/activate
   → Só funciona se status atual = PAUSED
   → Chama MetaAdsClient.update_status(ACTIVE)
   → Logado no audit_log
```

---

## 9. API Endpoints — Fase 1

### Auth

| Método | Rota | Ação |
|--------|------|------|
| POST | `/api/auth/register` | Cria conta (Supabase Auth) |
| POST | `/api/auth/login` | Login, retorna JWT |
| GET | `/api/auth/meta/login` | Retorna URL OAuth Meta com state JWT |
| GET | `/api/auth/meta/callback` | Troca code, salva token, lista contas |

### Contas

| Método | Rota | Ação |
|--------|------|------|
| GET | `/api/accounts` | Lista ad_accounts do usuário |
| GET | `/api/accounts/{act_id}` | Detalhe de uma conta |

### Campanhas

| Método | Rota | Ação |
|--------|------|------|
| GET | `/api/campaigns` | Lista campanhas (filtro por conta) |
| GET | `/api/campaigns/{id}/insights` | Métricas de uma campanha |
| POST | `/api/campaigns/sync` | Sincroniza campanhas + métricas do Meta |
| POST | `/api/campaigns/drafts` | Cria rascunho |
| PATCH | `/api/campaigns/drafts/{id}` | Atualiza rascunho |
| POST | `/api/campaigns/drafts/{id}/publish` | Envia rascunho ao Meta (cria em PAUSED) |
| POST | `/api/campaigns/{id}/activate` | Ativa campanha (PAUSED → ACTIVE) |
| POST | `/api/campaigns/{id}/pause` | Pausa campanha (ACTIVE → PAUSED) |

### Análise

| Método | Rota | Ação |
|--------|------|------|
| POST | `/api/analysis/evaluate` | Roda rules engine, retorna alertas |
| POST | `/api/analysis/summary` | Análise IA + KPIs + recomendações |

### Criativos

| Método | Rota | Ação |
|--------|------|------|
| POST | `/api/creatives/upload` | Upload imagem/vídeo (Supabase Storage) |
| GET | `/api/creatives` | Lista criativos do usuário |

### Auditoria

| Método | Rota | Ação |
|--------|------|------|
| GET | `/api/audit-log` | Histórico de ações (filtro por período e entidade) |

---

## 10. Error handling

### 10.1 Hierarquia de exceções

```python
class AppError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    detail: str = "Erro interno"

class MetaAPIError(AppError):
    status_code = 502
    error_code = "META_API_ERROR"

class MetaRateLimitError(MetaAPIError):
    status_code = 429
    error_code = "META_RATE_LIMIT"

class TokenExpiredError(AppError):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    detail = "Token Meta expirado. Reconecte sua conta."

class TokenInvalidError(AppError):
    status_code = 401
    error_code = "TOKEN_INVALID"

class DraftValidationError(AppError):
    status_code = 422
    error_code = "DRAFT_INVALID"

class CampaignSafetyError(AppError):
    status_code = 403
    error_code = "SAFETY_BLOCK"
    detail = "Ação bloqueada por regra de segurança."
```

### 10.2 Resposta padronizada

```json
{
  "error": "META_RATE_LIMIT",
  "detail": "Limite de requisições atingido para esta conta. Tente em 5 minutos.",
  "meta": {
    "retry_after_seconds": 300,
    "account": "act_123456"
  }
}
```

O exception handler global do FastAPI captura `AppError` e retorna JSON padronizado. Erros inesperados viram `INTERNAL_ERROR` com log completo no servidor, sem vazar stack trace para o cliente.

---

## 11. Testes

### 11.1 Estrutura

```
tests/
├── unit/
│   ├── test_rules.py          # evaluate() com cenários fixos
│   ├── test_kpis.py           # summarize_kpis()
│   ├── test_naming.py         # padrão de nomenclatura
│   ├── test_token_manager.py  # encrypt/decrypt/extend
│   └── test_crypto.py         # Fernet round-trip
├── integration/
│   ├── test_meta_client.py    # mock da Graph API (httpx + respx)
│   ├── test_sync_flow.py      # sync completo com DB de teste
│   └── test_auth_flow.py      # OAuth redirect + callback
└── conftest.py                # fixtures: supabase test client, fake tokens
```

### 11.2 Princípios

| Camada | O que testa | Mock de quê |
|--------|------------|-------------|
| Unit (core/) | Lógica pura — funções recebem dados, retornam resultado | Nada |
| Unit (meta/) | TokenManager, rate limiter | Nada — lógica interna |
| Integration | Fluxos completos | Graph API (respx), Supabase (client de teste) |

### 11.3 Cobertura mínima

- `core/`: 80%
- `meta/`: 70%
- `routers/`: 60%

O `conftest.py` cria um Supabase client apontando para branch de preview com RLS habilitado — os testes rodam com as mesmas policies de produção.

---

## 12. Deploy e infraestrutura

### 12.1 Domínio

```
ads.creativeagenciamkt.com.br  CNAME  <app>.railway.app (ou render)
```

Roteamento por fase:

```
Fase 1: ads.creativeagenciamkt.com.br/api/*  → FastAPI
Fase 2: ads.creativeagenciamkt.com.br/*      → Next.js (proxy /api/* → FastAPI)
```

### 12.2 Variáveis de ambiente

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...

# Meta
META_APP_ID=123456
META_APP_SECRET=abc...
META_REDIRECT_URI=https://ads.creativeagenciamkt.com.br/api/auth/meta/callback

# Segurança
FERNET_KEY=base64...
JWT_SECRET=...

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# App
ENVIRONMENT=production
LOG_LEVEL=info
CORS_ORIGINS=["https://ads.creativeagenciamkt.com.br"]
```

### 12.3 CI/CD

```
push main → GitHub Actions
  ├── pytest (com Supabase de teste)
  ├── ruff check + ruff format --check
  ├── se tudo verde → deploy automático
  └── se falhar → notifica, sem deploy
```

### 12.4 Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 13. Segurança e conformidade

- **Tokens criptografados** — Fernet em repouso, chave em env var do backend.
- **Audit log** — toda escrita na Marketing API é logada com request, response, user_id e timestamp.
- **Rate limiting** — respeita limites da Graph API por conta via `X-Business-Use-Case-Usage`.
- **Campanha PAUSED** — criação sempre em pausa, ativação requer confirmação explícita.
- **Advantage+ off** — segmentação automática desabilitada por padrão.
- **RLS** — isolamento de dados por usuário no banco.
- **CORS** — apenas `ads.creativeagenciamkt.com.br` permitido em produção.
- **LGPD** — consentimento no registro, exclusão de dados a pedido (delete cascade via `auth.users`).

---

## 14. O que NÃO entra na Fase 1

| Item | Fase |
|------|------|
| Frontend web (Next.js) | 2 |
| Agente WhatsApp (Cloud API) | 3 |
| Billing por conta (Stripe/Asaas) | 4 |
| Google Ads | 2+ |
| Lead Ads (formulário nativo) | 3 |
| Públicos lookalike/personalizados | 3 |
| Otimização proativa (agente sugere sem ser perguntado) | 3 |
| Painel multi-conta em uma conversa | 3 |
| Relatório semanal automático por template | 3 |

---

## 15. Migração do código atual

Resumo do que é migrado, descartado ou substituído:

| Arquivo atual | Destino | Status |
|--------------|---------|--------|
| `core/rules.py` → `evaluate_rows()` | `app/core/rules.py` → `evaluate()` | Migrado + expandido |
| `core/rules.py` → `summarize_kpis()` | `app/core/kpis.py` → `summarize_kpis()` | Migrado + expandido |
| `core/rules.py` → `RuleResult` | `app/core/rules.py` → `RuleResult` | Migrado (+ `meta_entity_id`) |
| `core/ai.py` → `fallback_analysis()` | `app/core/analysis.py` → `fallback_analysis()` | Mantido (ajustes menores) |
| `core/ai.py` → `ai_analysis()` | `app/core/analysis.py` → `analyze_performance()` | OpenAI → Claude |
| `core/ai.py` → `generate_campaign_ideas()` | `app/core/analysis.py` → `generate_campaign_strategy()` | Expandido (estratégia completa) |
| `connectors/meta_ads.py` → `_extract_metric()` | `app/meta/client.py` → `_extract_metric()` | Mantido na íntegra |
| `connectors/meta_ads.py` → `validate()` | `app/meta/client.py` → `get_account_info()` | Simplificado |
| `connectors/meta_ads.py` → `fetch_campaign_snapshot()` | `app/meta/client.py` → `get_insights()` + `list_campaigns()` | Async, paginação separada |
| `connectors/base.py` → `pause_entity()` | `app/meta/client.py` → `update_status()` | Execução real (não mais dry-run) |
| `core/database.py` | Descartado | Supabase substitui SQLite |
| `app.py` (Streamlit) | Descartado | Next.js na Fase 2 |
| `PRODUCT_BLUEPRINT.md` | Referência | Vision mantida, implementação adaptada |
