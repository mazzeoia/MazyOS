"""AI analysis layer with a deterministic fallback."""
from __future__ import annotations

import os
from typing import Iterable

from .rules import summarize_kpis


def fallback_analysis(rows: Iterable[dict], alerts: list[dict]) -> str:
    rows = list(rows)
    kpis = summarize_kpis(rows)
    red = [a for a in alerts if a.get("severity") == "vermelho"]
    yellow = [a for a in alerts if a.get("severity") == "amarelo"]

    lines = [
        "Diagnostico rapido:",
        f"Investimento: R$ {kpis['spend']:.2f}. Leads: {kpis['leads']}. CPL medio: R$ {kpis['cpl']:.2f}.",
    ]
    if red:
        lines.append(f"Tem {len(red)} ponto(s) critico(s) queimando dinheiro. Prioridade: pausar ou revisar agora.")
    elif yellow:
        lines.append(f"Nao tem desperdicio grave, mas existem {len(yellow)} alerta(s) para otimizar criativo, publico ou copy.")
    else:
        lines.append("Nao apareceu alerta critico nas regras atuais. Acompanhe a consistencia dos leads antes de escalar.")

    if kpis["leads"] == 0 and kpis["spend"] > 0:
        lines.append("Atencao: estamos olhando lead de WhatsApp/formulario. Sem conversao registrada, a leitura e de trafego, nao de venda.")

    lines.append("Proxima acao: resolva primeiro o que gastou sem lead, depois mexa em CTR, frequencia e CPL.")
    return "\n".join(lines)


def generate_campaign_ideas(client: dict, rows: Iterable[dict], alerts: list[dict]) -> str:
    objective = client.get("objective") or "gerar leads pelo WhatsApp/formulario"
    niche = client.get("niche") or "negocio local"
    return (
        f"Ideias de teste para {client.get('name', 'cliente')} ({niche}):\n"
        f"1. Criar campanha de fundo de funil com promessa direta ligada a: {objective}.\n"
        "2. Testar 3 criativos: prova social, dor do cliente e oferta objetiva.\n"
        "3. Separar publico frio de remarketing para nao misturar leitura de performance.\n"
        "4. No Google, priorizar termos com intencao de compra e negativar buscas informacionais.\n"
        "5. No Meta/Instagram, trocar criativo antes de aumentar verba quando a frequencia passar do limite."
    )


def ai_analysis(client: dict, rows: Iterable[dict], alerts: list[dict]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback_analysis(rows, alerts)

    try:
        from openai import OpenAI

        kpis = summarize_kpis(rows)
        client_api = OpenAI(api_key=api_key)
        prompt = (
            "Voce e analista de trafego da Creative Agencia Marketing. "
            "Escreva em portugues brasileiro simples, direto e util. "
            "Nao invente numeros. Explique o que fazer hoje.\n\n"
            f"Cliente: {dict(client)}\nKPIs: {kpis}\nAlertas: {alerts[:20]}"
        )
        response = client_api.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            input=prompt,
        )
        return response.output_text
    except Exception as exc:
        return fallback_analysis(rows, alerts) + f"\n\nIA externa indisponivel: {exc}"
