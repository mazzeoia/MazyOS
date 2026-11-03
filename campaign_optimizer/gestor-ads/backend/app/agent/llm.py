# app/agent/llm.py
from __future__ import annotations

import json
import logging

import anthropic

from app.agent.tools import (
    ToolContext,
    aprovar_campanha,
    consultar_metricas,
    criar_campanha,
    listar_contas,
    localizacao_por_raio,
    pausar_campanha,
    propor_campanha,
    selecionar_conta,
)

logger = logging.getLogger(__name__)

MODEL_HAIKU = "claude-haiku-4-5"
MODEL_SONNET = "claude-sonnet-5"

_STRATEGY_KEYWORDS = (
    "campanha",
    "estratégia",
    "estrategia",
    "criar",
    "orçamento",
    "orcamento",
    "verba",
    "público",
    "publico",
    "ajusta",
    "ajustar",
)

SYSTEM_PROMPT = """Você é o gestor de tráfego pago do usuário, operando por chat.
Você tem acesso real à conta de anúncio dele pela Meta Marketing API através das
ferramentas disponíveis. Responda em português brasileiro, direto, sem enrolação —
mensagens curtas, é chat, não e-mail.

Regras rígidas:
- Toda campanha é criada com status PAUSED. Ative somente após confirmação explícita.
- Peça aprovação explícita antes de criar qualquer campanha.
- Fluxo de campanha, sempre nesta ordem: `propor_campanha` gera o rascunho e você
  apresenta a estratégia; o usuário confirma explicitamente ("pode criar",
  "aprovado", "sim"); só então você chama `aprovar_campanha` com o draft_id e,
  logo em seguida, `criar_campanha` com o mesmo draft_id. Sem confirmação
  explícita do usuário, nunca chame `aprovar_campanha`.
- Nunca invente métrica, resultado ou histórico — chame a ferramenta correspondente.
- Se o nível técnico do usuário for leigo, traduza toda métrica para consequência
  prática, nunca use sigla sem explicar. Se for avançado, use os termos técnicos
  normalmente (CTR, CPM, CPA, CPL, CBO, ABO).
"""

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "listar_contas",
        "description": "Lista as contas de anúncio Meta já conectadas para este usuário.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "selecionar_conta",
        "description": "Seleciona a conta de anúncio ativa para esta conversa, por número da lista ou nome.",
        "input_schema": {
            "type": "object",
            "properties": {"conta": {"type": "string", "description": "número ou nome da conta"}},
            "required": ["conta"],
        },
    },
    {
        "name": "propor_campanha",
        "description": "Gera uma proposta de estratégia de campanha justificada, para o usuário aprovar antes de criar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "produto": {"type": "string"},
                "objetivo": {"type": "string"},
                "verba_total": {"type": "number"},
                "dias": {"type": "integer"},
                "publico_alvo": {"type": "string"},
                "destino_lead": {"type": "string"},
                "marca": {"type": "string"},
            },
            "required": ["produto", "objetivo", "verba_total", "dias", "publico_alvo", "destino_lead", "marca"],
        },
    },
    {
        "name": "aprovar_campanha",
        "description": (
            "Registra a aprovação explícita do usuário para um rascunho de campanha. "
            "Chame somente depois de o usuário confirmar em palavras. Passo obrigatório antes de criar_campanha."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"draft_id": {"type": "string"}},
            "required": ["draft_id"],
        },
    },
    {
        "name": "criar_campanha",
        "description": "Cria a campanha de verdade na Meta, sempre em PAUSED. Exige um draft já aprovado pelo usuário.",
        "input_schema": {
            "type": "object",
            "properties": {"draft_id": {"type": "string"}},
            "required": ["draft_id"],
        },
    },
    {
        "name": "consultar_metricas",
        "description": "Consulta as métricas atuais da conta de anúncio selecionada.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "pausar_campanha",
        "description": "Pausa uma campanha existente na Meta.",
        "input_schema": {
            "type": "object",
            "properties": {"campanha_id": {"type": "string"}},
            "required": ["campanha_id"],
        },
    },
    {
        "name": "localizacao_por_raio",
        "description": "Monta a segmentação por raio a partir de uma coordenada já extraída de um pin ou link do Maps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "raio_km": {"type": "number"},
            },
            "required": ["latitude", "longitude", "raio_km"],
        },
    },
]
# Cache the (static) tool schema between turns of the same conversation.
TOOL_DEFINITIONS[-1]["cache_control"] = {"type": "ephemeral"}


def classify_intent(text: str) -> str:
    """Cheap keyword heuristic — no extra LLM call. Anything that smells
    like campaign strategy work goes to Sonnet; everything else (simple
    questions, confirmations) goes to the cheaper Haiku model."""
    lowered = text.lower()
    if any(keyword in lowered for keyword in _STRATEGY_KEYWORDS):
        return "estrategia"
    return "simples"


async def dispatch_tool(name: str, tool_input: dict, ctx: ToolContext, meta_client) -> dict:
    if name == "listar_contas":
        return await listar_contas(ctx)
    if name == "selecionar_conta":
        return await selecionar_conta(ctx, conta=tool_input["conta"])
    if name == "propor_campanha":
        return await propor_campanha(ctx, **tool_input)
    if name == "aprovar_campanha":
        return await aprovar_campanha(ctx, draft_id=tool_input["draft_id"])
    if name == "criar_campanha":
        return await criar_campanha(ctx, meta_client, draft_id=tool_input["draft_id"])
    if name == "consultar_metricas":
        return await consultar_metricas(ctx, meta_client)
    if name == "pausar_campanha":
        return await pausar_campanha(ctx, meta_client, campanha_id=tool_input["campanha_id"])
    if name == "localizacao_por_raio":
        return localizacao_por_raio(**tool_input)
    raise ValueError(f"Tool desconhecida: {name}")


async def run_agent_turn(
    *,
    ctx: ToolContext,
    meta_client,
    resumo_memoria: str,
    memoria_negocio: dict,
    historico: list[dict],
    mensagem_atual: str,
    nivel_tecnico: str,
    anthropic_api_key: str,
    anthropic_workspace_id: str,
) -> dict:
    """One turn of the agent loop: builds context, routes to Haiku/Sonnet,
    runs the tool-use loop until Claude returns a final text answer."""
    model = MODEL_SONNET if classify_intent(mensagem_atual) == "estrategia" else MODEL_HAIKU

    headers = {}
    if anthropic_workspace_id:
        headers["anthropic-workspace-id"] = anthropic_workspace_id
    client = anthropic.AsyncAnthropic(api_key=anthropic_api_key, default_headers=headers)

    context_note = (
        f"Nível técnico: {nivel_tecnico}. Resumo da conversa: {resumo_memoria or 'nenhum ainda'}. "
        f"Memória de negócio: {memoria_negocio or 'nenhuma ainda'}."
    )
    messages = [
        {"role": "user", "content": context_note},
        *historico,
        {"role": "user", "content": mensagem_atual},
    ]

    total_input = 0
    total_output = 0

    for _ in range(5):  # hard cap on tool-use round-trips per turn
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens

        if response.stop_reason != "tool_use":
            text = next((b.text for b in response.content if getattr(b, "type", "") == "text"), "")
            return {
                "resposta": text,
                "tokens_input": total_input,
                "tokens_output": total_output,
                "modelo_usado": model,
            }

        tool_block = next(b for b in response.content if getattr(b, "type", "") == "tool_use")
        try:
            tool_result = await dispatch_tool(tool_block.name, tool_block.input, ctx, meta_client)
            tool_content = json.dumps(tool_result, ensure_ascii=False, default=str)
        except Exception as exc:
            logger.warning("Tool %s failed: %s", tool_block.name, exc)
            tool_content = f"Erro: {exc}"

        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": tool_content}],
            }
        )

    return {
        "resposta": "Deixa eu processar isso com mais calma, já te chamo.",
        "tokens_input": total_input,
        "tokens_output": total_output,
        "modelo_usado": model,
    }
