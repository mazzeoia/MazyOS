# Gestor Ads — Fase 3a: Agente Conversacional (Telegram + WhatsApp)

> Design spec do agente conversacional que cria, ativa, monitora e otimiza campanhas de
> Meta Ads via chat (Telegram e WhatsApp), consumindo o core channel-agnostic já construído
> na Fase 1 do Gestor Ads. Baseado no briefing original em
> `Documents/Trafego Clientes/creative media/gestor whatsapp/prompt-saas-gestor-whatsapp.md`.

## 1. Visão geral

O Gestor Ads hoje tem um backend FastAPI + Supabase em produção (`ads.creativeagenciamkt.com.br`)
com auth, conexão Meta (OAuth), leitura+escrita real na Marketing API, rules engine, KPI
aggregator, análise por IA e auditoria — tudo desenhado desde a Fase 1 para ser
**channel-agnostic**: o `core/` nunca sabe se quem chamou foi o dashboard web ou um agente
de chat.

A Fase 3a entrega esse agente de chat: uma pessoa conversa em linguagem natural (texto ou
áudio) pelo Telegram ou WhatsApp, e o agente propõe, cria e gerencia campanhas de verdade na
conta de anúncio dela, usando o mesmo `core/` do dashboard.

### Escopo desta fase

**Entra:**
- Onboarding via chat (OAuth Meta, seleção de conta, nível técnico)
- Criação de campanha (objetivo tráfego e clique-para-WhatsApp)
- Localização por raio (pin do WhatsApp/Telegram ou link do Google Maps)
- Relatório sob demanda, em texto, adaptado ao nível técnico
- Transcrição de áudio (Whisper API)
- Adaptadores de canal: **Telegram** (Bot API oficial) e **Evolution API** (WhatsApp via QR
  Code, rotulado experimental)
- Roteamento de modelo (Haiku/Sonnet) + prompt caching, para custo de LLM sob controle

**Não entra (fases seguintes):**
- WhatsApp Cloud API oficial — aguarda o App Review da Meta (Access Verification em
  análise); entra como canal de produção assim que aprovado
- Lead Ads nativo, públicos lookalike/personalizados
- Alertas automáticos (jobs agendados) — **Fase 3b**, spec própria
- Billing por conta (Stripe/Asaas) — **Fase 4**, spec própria
- Otimização proativa (agente sugere sem ser perguntado), painel multi-conta numa conversa,
  relatório semanal automático

### Modo de lançamento

**Dogfooding** — uso interno da agência (Lima + clientes atuais do Gestor Ads), sem
gating de assinatura. Billing fica pra Fase 4, quando o produto for aberto pra terceiros.

### Princípios

- **Reaproveitar, nunca duplicar** o `core/` da Fase 1 (rules, Meta client, naming, auditoria,
  TokenManager). O agente é um consumidor novo desse core, não uma reimplementação.
- **Canal é um detalhe de transporte.** O agente e o core recebem texto/mídia normalizado;
  nunca sabem se veio do Telegram, Evolution ou (no futuro) WhatsApp Cloud oficial.
- **Segurança de execução no código, não só no prompt.** Regras rígidas do documento original
  (sempre criar em PAUSED, exigir aprovação explícita antes de criar campanha, nunca inventar
  métrica) são checks de código nas tools, não apenas instrução de system prompt.
- **Custo de LLM instrumentado desde o dia 1** — tokens gastos por conta, por mensagem.

---

## 2. Arquitetura

Novo processo Python (`whatsapp-agent`), container Docker próprio no mesmo
`docker-compose.yml` da VPS (`creative_ads_agent`), separado do container do backend web
(`creative_ads_backend`). Importa o `core/` da Fase 1 como biblioteca — zero duplicação de
lógica de negócio.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Telegram   │────▶│                  │────▶│  Claude (LLM)   │
│  Bot API    │     │  Agent Service   │     │  Haiku/Sonnet   │
├─────────────┤     │  (novo container)│◀────│  + function     │
│  Evolution  │────▶│                  │     │    calling      │
│  (QR/beta)  │     │  - Channel       │     └─────────────────┘
└─────────────┘     │    adapters      │
                     │  - Conversation  │     ┌─────────────────┐
  (WA Cloud entra    │    state         │────▶│  Whisper API    │
   quando aprovado)  │  - Tool router   │     │  (áudio→texto)  │
                     └────────┬─────────┘     └─────────────────┘
                              │ importa como lib
                     ┌────────▼─────────┐
                     │  core/ (Fase 1)  │
                     │  rules, meta     │
                     │  client, naming, │
                     │  audit           │
                     └────────┬─────────┘
                              │
                     ┌────────▼─────────┐
                     │    Supabase      │
                     └──────────────────┘
```

**Por que container separado:** chamadas de LLM e transcrição de áudio são mais lentas e
mais instáveis que o resto da API. Se rodassem no mesmo processo do dashboard web, um pico
de uso no chat poderia deixar o dashboard lento ou fora do ar junto. Isolar o processo custa
pouco a mais e protege o produto principal.

### Interface `ChannelAdapter`

Cada canal implementa a mesma interface:

```python
class ChannelAdapter(Protocol):
    async def receive_webhook(self, payload: dict) -> IncomingMessage: ...
    async def send_text(self, chat_id: str, text: str) -> None: ...
    async def download_media(self, media_ref: str) -> bytes: ...
```

`IncomingMessage` normaliza texto, áudio (bytes brutos, a transcrever), imagem/documento e
localização (lat/lng já extraído, seja de pin nativo ou link do Google Maps) — o agente
nunca lida com o formato específico do Telegram ou da Evolution API diretamente.

Implementações desta fase: `TelegramAdapter` (Bot API, webhook oficial), `EvolutionAdapter`
(via instância Evolution API já rodando no VPS, container `evolution-go`).

### Processamento assíncrono

Webhook confirma recebimento em <1s (exigência do Telegram/WhatsApp para não reenviar a
mensma mensagem) e processa a resposta em background via `asyncio` (fila em memória — sem
Redis/BullMQ nesta fase, dado o volume baixo do modo dogfooding). Se o volume crescer o
suficiente pra justificar, migrar pra uma fila persistente vira decisão de uma fase futura.

---

## 3. Modelo de dados (tabelas novas + reaproveitadas)

Reaproveita `meta_connections`, `ad_accounts`, `audit_log` e **`profiles.nivel_tecnico`**
(já existe desde a Fase 1 — um campo por usuário, não duplicamos por conversa). A tabela
`campaign_drafts` **já existe** também (`migrations/001_initial_schema.sql`, colunas
`owner_id`, `ad_account_id`, `payload` JSONB, `status`, `meta_campaign_id`, `erro_detalhes`)
e é reaproveitada como está, só ganha uma coluna nova pra ligar com a conversa de origem.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID REFERENCES ad_accounts(id) ON DELETE SET NULL,
    channel TEXT NOT NULL CHECK (channel IN ('telegram', 'evolution', 'whatsapp_cloud')),
    channel_user_id TEXT NOT NULL,       -- chat_id (Telegram) ou telefone E.164 (WhatsApp)
    resumo_memoria TEXT NOT NULL DEFAULT '',
    memoria_negocio JSONB NOT NULL DEFAULT '{}',  -- nicho, ticket, região, públicos, criativos
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (channel, channel_user_id)
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    papel TEXT NOT NULL CHECK (papel IN ('user', 'assistant', 'tool')),
    conteudo TEXT NOT NULL DEFAULT '',
    media_url TEXT,
    transcricao TEXT,
    modelo_usado TEXT,             -- 'claude-haiku-4-5' | 'claude-sonnet-5'
    tokens_input INTEGER NOT NULL DEFAULT 0,
    tokens_output INTEGER NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_conversation ON messages (conversation_id, criado_em);

-- campaign_drafts JÁ EXISTE — só adiciona a ligação com a conversa de origem.
-- Continua nullable: drafts criados pelo dashboard web não têm conversation_id.
ALTER TABLE campaign_drafts
    ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL;
```

Nível técnico do usuário mora em `profiles.nivel_tecnico` (`leigo`/`avancado`), atualizado no
onboarding do chat igual seria pelo dashboard — um valor só, independente do canal.

`conversations` é por **canal**, não por pessoa — o mesmo usuário pode falar pelo Telegram e
pelo WhatsApp com `conversation_id` diferentes, ambos ligados ao mesmo `owner_id`/
`ad_account_id`. Compartilhar `memoria_negocio` entre canais da mesma pessoa é uma decisão de
produto que pode vir depois — o schema já permite (via `owner_id`), a Fase 3a não implementa
esse cruzamento automaticamente.

RLS: mesma política de `owner_id = auth.uid()` usada nas outras tabelas do projeto.

---

## 4. Loop do agente

Por mensagem recebida:

1. **Webhook normaliza** via `ChannelAdapter` → grava em `messages` (áudio passa por Whisper
   API antes, texto vira `transcricao`).
2. **Monta contexto pro Claude**: system prompt (com `cache_control`, cacheado entre turnos),
   `resumo_memoria` + `memoria_negocio` da conversa, últimas ~5 mensagens, e só as **tools
   relevantes ao estado atual** (ex.: durante onboarding só `listar_contas`/`selecionar_conta`;
   depois de conectado, `propor_campanha`, `criar_campanha`, `consultar_metricas`,
   `pausar_campanha`).
3. **Roteamento de modelo**: uma classificação leve da intenção decide o modelo — perguntas
   simples/confirmações vão pro Haiku 4.5; propor ou ajustar estratégia de campanha (que exige
   raciocínio de verdade) vai pro Sonnet 5.
4. **Claude decide**: responde direto, ou chama uma tool. Cada tool é uma função Python fina
   que chama o `core/` existente — ex.: `criar_campanha()` chama `meta.client.create_campaign()`
   + `core.naming` + grava em `audit_log`, sempre com a campanha em `PAUSED`.
5. **Resultado da tool volta pro Claude**, que formula a resposta final adaptada ao
   `nivel_tecnico` da conversa.
6. **Envia pela `ChannelAdapter`** de origem; atualiza `resumo_memoria` se necessário; grava
   tokens gastos em `messages` (`tokens_input`/`tokens_output`/`modelo_usado`).

### Regras rígidas como checks de código

- `criar_campanha()` recusa (erro tratado e explicado) se não existir um `campaign_draft` com
  `status='aprovado'` vinculado à conversa — não confia no LLM lembrar de pedir aprovação.
- Toda campanha é criada com `status=PAUSED` na Meta API, sempre — não é uma instrução de
  prompt, é um argumento fixo na chamada da tool.
- Nomenclatura (`[MARCA] | objetivo | público | AAAAMMDD-HHMM`) é aplicada pelo `core.naming`
  já existente, não gerada livremente pelo LLM.
- Localização por raio: tool dedicada que aceita pin do canal ou link do Google Maps, extrai
  lat/lng, e monta `custom_locations` — a extração de coordenada não passa pelo LLM (evita
  erro de parsing por texto livre).

---

## 5. Onboarding

1. Usuário manda a primeira mensagem no Telegram ou WhatsApp (Evolution) → agente cria
   `conversations` nova, gera link de OAuth Meta com `state` assinado carregando o
   `conversation_id` (não só `user_id`, para saber a qual conversa responder no callback).
2. Callback do OAuth (endpoint já existente, reaproveitado) salva a conexão e notifica a
   conversa certa com a lista de contas de anúncio encontradas.
3. Usuário escolhe a conta por número ou nome — o agente desambigua quando há nomes parecidos.
4. Agente pergunta o nível técnico (`leigo`/`avancado`) → grava em `profiles.nivel_tecnico`
   (se já estiver preenchido de uma sessão anterior no dashboard web, pula essa pergunta).
5. A partir daqui, criação de campanha segue o loop da Seção 4.

---

## 6. Custo de LLM

- **Prompt caching (Anthropic `cache_control`)** no system prompt e no schema de tools —
  maior economia, já que ambos são praticamente estáticos entre turnos da mesma conversa.
- **Roteamento Haiku/Sonnet** conforme Seção 4.
- **Memória resumida**, nunca histórico completo reenviado.
- **Tools sob demanda**, só as relevantes ao estado da conversa.
- **Instrumentação por conta desde o dia 1** — `tokens_input`/`tokens_output`/`modelo_usado`
  gravados em cada linha de `messages`, permitindo depois somar custo real por
  `ad_account_id` via `conversation_id`.

---

## 7. Erros e limites

| Situação | Comportamento |
|---|---|
| Falha na Meta API (rate limit, token expirado) | Agente informa a falha de forma honesta (adaptada ao nível técnico), nunca inventa resultado; tenta de novo com backoff quando aplicável |
| Falha de transcrição de áudio | Pede pra repetir em texto |
| Sessão do Evolution (QR) cair | Alerta interno pro admin (Lima), não fica em silêncio — o canal é rotulado experimental justamente por esse risco |
| Timeout do LLM | Responde algo como "deixa eu processar isso, já te chamo" e reprocessa em background |
| Tool chamada sem pré-requisito (ex.: criar campanha sem draft aprovado) | Erro tratado, mensagem explicando o que falta — nunca falha silenciosa |

---

## 8. Segurança e conformidade

- Reaproveita tudo que a Fase 1 já implementa: tokens criptografados (Fernet), auditoria de
  toda escrita na Marketing API, RLS por `owner_id`.
- O Evolution API (WhatsApp via QR) é explicitamente **rotulado como experimental** no
  produto — risco real de banimento de número por uso de biblioteca não-oficial, sem
  templates aprovados. Usuários devem estar cientes antes de optar por esse modo.
- Telegram Bot API é 100% oficial — usado como canal primário de validação por não ter esse
  risco.
- WhatsApp Cloud API oficial entra como canal de produção assim que o App Review (em
  andamento, Access Verification em análise) for aprovado — sem mudança de arquitetura, só
  mais um `ChannelAdapter`.

---

## 9. O que não entra nesta fase

| Item | Fase |
|---|---|
| WhatsApp Cloud API oficial (canal) | 3a-extensão, pós App Review |
| Alertas automáticos (jobs: criativo reprovado, conta suspensa, sem resultado, saldo baixo) | 3b |
| Billing por conta (Stripe/Asaas) | 4 |
| Lead Ads nativo, públicos lookalike/personalizados | Futuro |
| Otimização proativa, painel multi-conta numa conversa, relatório semanal automático | Futuro |
| Adaptador Telegram/Evolution como biblioteca reaproveitável por outros produtos | Não planejado |
