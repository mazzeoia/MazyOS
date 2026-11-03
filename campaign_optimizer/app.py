from __future__ import annotations

from datetime import timedelta
from html import escape
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from campaign_optimizer.connectors.google_ads import GoogleAdsConnector
from campaign_optimizer.connectors.meta_ads import MetaAdsConnector
from campaign_optimizer.core.ai import ai_analysis, generate_campaign_ideas
from campaign_optimizer.core.database import (
    fetch_action_logs,
    fetch_metrics,
    get_client,
    init_db,
    insert_metrics,
    list_clients,
    log_action,
    replace_metrics_for_source,
    upsert_client,
)
from campaign_optimizer.core.importers import read_csv
from campaign_optimizer.core.reports import generate_html_report, money
from campaign_optimizer.core.rules import evaluate_rows, summarize_kpis
from campaign_optimizer.core.settings import ENV_PATH, load_env_file, read_env_values, write_env_values
from campaign_optimizer.core.ui import (
    command_card,
    empty_product,
    inject_product_theme,
    logo_data_uri,
    page_header,
    section_heading,
)

st.set_page_config(page_title="Creative Media OS", page_icon="C", layout="wide")
load_env_file()
init_db()

st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at top left, rgba(255, 157, 0, 0.10), transparent 24%),
          radial-gradient(circle at top right, rgba(208, 0, 24, 0.08), transparent 20%),
          linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        color: #0f172a;
      }
      [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
      }
      [data-testid="stSidebarContent"] {
        background: linear-gradient(180deg, #ffffff 0%, #f6f7fb 100%);
      }
      .block-container {
        max-width: 1380px;
        padding-top: 1.2rem;
      }
      h1, h2, h3 {
        letter-spacing: 0;
        color: #0f172a;
      }
      div[data-testid="stMetric"] {
        background: rgba(255,255,255,.88);
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.06);
      }
      div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
      }
      .hero {
        background:
          radial-gradient(circle at top right, rgba(255, 122, 0, 0.12), transparent 26%),
          linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(226,232,240,.95);
        border-radius: 28px;
        padding: 28px;
        box-shadow: 0 28px 60px rgba(15, 23, 42, 0.08);
        margin-bottom: 18px;
      }
      .hero h1 {
        margin: 0 0 10px 0;
        font-size: 36px;
        line-height: 1.05;
      }
      .hero p {
        margin: 0;
        max-width: 920px;
        color: #475569;
        font-size: 15px;
        line-height: 1.6;
      }
      .brand-line {
        width: 180px;
        height: 6px;
        border-radius: 999px;
        background: linear-gradient(90deg, #ffd400 0%, #ff7a00 52%, #d00018 100%);
        margin-bottom: 18px;
      }
      .soft-card {
        background: rgba(255,255,255,.92);
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 20px;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.06);
      }
      .step-card {
        background: rgba(255,255,255,.96);
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 20px;
        min-height: 140px;
        box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
      }
      .step-index {
        width: 34px;
        height: 34px;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        color: #fff;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 14px;
      }
      .step-card strong {
        display: block;
        color: #0f172a;
        font-size: 18px;
        margin-bottom: 8px;
      }
      .step-card p {
        margin: 0;
        color: #64748b;
        line-height: 1.55;
      }
      .status-chip {
        display: inline-block;
        padding: 7px 11px;
        border-radius: 999px;
        border: 1px solid #d7dce4;
        background: #ffffff;
        color: #334155;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
      }
      .connector-card {
        background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
        border: 1px solid #e5e7eb;
        border-radius: 26px;
        padding: 22px;
        box-shadow: 0 24px 48px rgba(15, 23, 42, 0.06);
      }
      .connector-card.ok { border-left: 6px solid #22c55e; }
      .connector-card.warn { border-left: 6px solid #f59e0b; }
      .connector-card.locked { border-left: 6px solid #94a3b8; }
      .connector-card h3 {
        margin: 0 0 10px 0;
        font-size: 24px;
      }
      .connector-card p {
        margin: 0;
        color: #64748b;
        line-height: 1.55;
      }
      .summary-strip {
        margin-top: 12px;
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 18px;
        padding: 14px 16px;
        color: #9a3412;
      }
      .alert-red {
        border-left: 6px solid #d00018;
        background: #fff1f2;
        padding: 14px;
        border-radius: 18px;
        margin-bottom: 10px;
        color: #881337;
      }
      .alert-yellow {
        border-left: 6px solid #f59e0b;
        background: #fff8eb;
        padding: 14px;
        border-radius: 18px;
        margin-bottom: 10px;
        color: #92400e;
      }
      .muted {
        color: #64748b;
        font-size: 14px;
      }
      .sidebar-shell {
        padding: 12px 8px 18px 8px;
      }
      .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 10px 16px 10px;
      }
      .sidebar-logo {
        width: 42px;
        height: 42px;
        border-radius: 14px;
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 16px;
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.14);
      }
      .sidebar-brand strong {
        display: block;
        color: #0f172a;
        font-size: 18px;
        line-height: 1.1;
      }
      .sidebar-brand span {
        display: block;
        color: #64748b;
        font-size: 12px;
        margin-top: 4px;
      }
      .sidebar-spotlight {
        margin: 2px 6px 18px 6px;
        padding: 16px;
        border-radius: 20px;
        background: linear-gradient(145deg, #111827 0%, #1f2937 100%);
        box-shadow: 0 24px 36px rgba(15,23,42,.16);
      }
      .sidebar-spotlight strong {
        display: block;
        color: #fff !important;
        font-size: 14px;
        margin-bottom: 6px;
      }
      .sidebar-spotlight p {
        margin: 0;
        color: #e5e7eb !important;
        font-size: 13px;
        line-height: 1.45;
      }
      .sidebar-section {
        margin: 8px 0 16px 0;
      }
      .sidebar-label {
        padding: 0 12px 8px 12px;
        color: #64748b;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .08em;
        text-transform: uppercase;
      }
      .sidebar-link {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 13px 14px;
        margin: 4px 6px;
        border-radius: 16px;
        text-decoration: none;
        color: #334155;
        font-size: 15px;
        font-weight: 600;
        transition: all .18s ease;
      }
      .sidebar-link:hover {
        background: #edf2ff;
        color: #0f172a;
        transform: translateX(1px);
      }
      .sidebar-link.active {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: #fff;
        box-shadow: 0 16px 28px rgba(124,58,237,.24);
      }
      .sidebar-link .icon {
        width: 20px;
        height: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: rgba(255,255,255,.58);
        color: #334155;
        font-size: 14px;
        flex: 0 0 20px;
      }
      .sidebar-link.active .icon {
        background: rgba(255,255,255,.18);
        color: #fff;
      }
      .sidebar-divider {
        height: 1px;
        background: #e6e8ef;
        margin: 8px 12px 14px 12px;
      }
      .sidebar-footer {
        margin: 16px 6px 6px 6px;
        padding: 14px;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #e7eaf0;
      }
      .sidebar-footer strong {
        display: block;
        color: #0f172a;
        font-size: 13px;
        margin-bottom: 4px;
      }
      .sidebar-footer span {
        display: block;
        color: #64748b;
        font-size: 12px;
        line-height: 1.45;
      }
      @media (max-width: 900px) {
        .hero h1 { font-size: 30px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

inject_product_theme()

NAV_ITEMS = {
    "overview": {"label": "Visao geral", "icon": "&#9638;", "section": "main", "target": "overview"},
    "clients": {"label": "Clientes", "icon": "&#9673;", "section": "operation", "target": "clients"},
    "routine": {"label": "Central de acoes", "icon": "&#10003;", "section": "operation", "target": "routine"},
    "campaigns": {"label": "Campanhas", "icon": "&#9636;", "section": "operation", "target": "campaigns"},
    "reports": {"label": "Relatorios", "icon": "&#9776;", "section": "operation", "target": "reports"},
    "connections": {"label": "Integracoes", "icon": "&#8644;", "section": "config", "target": "connections"},
    "imports": {"label": "Fonte de dados", "icon": "&#8593;", "section": "config", "target": "imports"},
    "help": {"label": "Ajuda e suporte", "icon": "&#63;", "section": "config", "target": "help"},
}


def rows_to_df(rows) -> pd.DataFrame:
    return pd.DataFrame([dict(row) for row in rows])


def dict_client(row) -> dict:
    return dict(row) if row else {}


def select_client(label: str = "Cliente", key: str = "client_selector"):
    clients = list_clients()
    if not clients:
        st.warning("Cadastre um cliente primeiro. Isso libera dashboard, conexoes e relatorios.")
        return None, None
    labels = {f"{client['name']}": client["id"] for client in clients}
    selected = st.selectbox(label, list(labels.keys()), key=key)
    return labels[selected], dict_client(get_client(labels[selected]))


def render_header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-line'></div>", unsafe_allow_html=True)


def status_badge(text: str) -> None:
    st.markdown(f"<span class='status-chip'>{text}</span>", unsafe_allow_html=True)


def render_step(index: str, title: str, body: str) -> None:
    st.markdown(
        f"<div class='step-card'><div class='step-index'>{index}</div><strong>{title}</strong><p>{body}</p></div>",
        unsafe_allow_html=True,
    )


def render_alerts(alerts: list[dict], limit: int = 8) -> None:
    if not alerts:
        st.success("Sem alerta nas regras atuais.")
        return
    severity_order = {"vermelho": 0, "amarelo": 1}
    for alert in sorted(alerts, key=lambda item: severity_order.get(item.get("severity"), 9))[:limit]:
        css = "alert-red" if alert.get("severity") == "vermelho" else "alert-yellow"
        label = "Critico" if alert.get("severity") == "vermelho" else "Atencao"
        st.markdown(
            f"<div class='{css}'><strong>{label}: {alert.get('campaign')}</strong><br>"
            f"{alert.get('reason')}<br><span class='muted'>Acao: {alert.get('action')} | Canal: {alert.get('platform')}</span></div>",
            unsafe_allow_html=True,
        )


def format_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.rename(
        columns={
            "date": "Data",
            "platform": "Canal",
            "campaign": "Campanha",
            "ad_group": "Grupo/Conjunto",
            "ad_name": "Anuncio",
            "spend": "Gasto",
            "leads": "Leads",
            "cpl": "CPL",
            "ctr": "CTR",
            "cpc": "CPC",
            "cpm": "CPM",
            "frequency": "Frequencia",
        }
    )


def mask_secret(value: str) -> str:
    if not value:
        return "Nao preenchido"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def render_connector_card(title: str, description: str, result: dict, mode: str) -> None:
    if result["ok"]:
        css = "ok"
        status = "Conectado"
    elif mode == "coming_soon":
        css = "locked"
        status = "Em preparacao"
    else:
        css = "warn"
        status = "Configuracao pendente"
    missing = len(result.get("payload", {}).get("missing_env", []))
    st.markdown(
        f"<div class='connector-card {css}'><h3>{title}</h3><p>{description}</p>"
        f"<div style='margin-top:14px'><span class='status-chip'>Status: {status}</span>"
        f"<span class='status-chip'>Campos pendentes: {missing}</span></div></div>",
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    current = st.query_params.get("page", "overview")
    page = current if current in NAV_ITEMS else "overview"
    sections = {"main": "", "operation": "Operacao", "config": "Configuracao"}
    logo = logo_data_uri()
    logo_html = f"<img class='sidebar-logo-image' src='{logo}' alt='Creative Marketing'>" if logo else "<div class='sidebar-logo'>C</div>"

    html = [
        "<div class='sidebar-shell'>",
        f"<div class='sidebar-brand'>{logo_html}<div><strong>Creative Media OS</strong><span>Performance e automacao</span></div></div>",
        "<div class='sidebar-spotlight'><strong>IA sob controle</strong><p>O sistema analisa e recomenda. Acoes sensiveis continuam dependendo da sua aprovacao.</p></div>",
    ]
    for section_key, section_label in sections.items():
        html.append("<div class='sidebar-section'>")
        if section_label:
            html.append(f"<div class='sidebar-label'>{section_label}</div>")
        for key, item in NAV_ITEMS.items():
            if item["section"] != section_key:
                continue
            active = "active" if key == page else ""
            html.append(
                f"<a class='sidebar-link {active}' href='?page={key}'>"
                f"<span class='icon'>{item['icon']}</span><span>{item['label']}</span></a>"
            )
        html.append("</div>")
        if section_key != "config":
            html.append("<div class='sidebar-divider'></div>")
    html.append("<div class='sidebar-footer'><strong>Creative Marketing</strong><span>Ambiente da agencia | Versao de produto 0.2</span></div>")
    html.append("</div>")
    st.sidebar.markdown("".join(html), unsafe_allow_html=True)
    return NAV_ITEMS[page]["target"]


def split_period(rows: list[dict], days: int) -> tuple[list[dict], list[dict]]:
    if not rows:
        return [], []
    frame = pd.DataFrame(rows)
    parsed = pd.to_datetime(frame["date"], errors="coerce")
    if parsed.notna().sum() == 0:
        return rows, []
    anchor = parsed.max().normalize()
    current_start = anchor - timedelta(days=days - 1)
    previous_start = current_start - timedelta(days=days)
    current = frame.loc[(parsed >= current_start) & (parsed <= anchor)].drop(columns=[], errors="ignore")
    previous = frame.loc[(parsed >= previous_start) & (parsed < current_start)].drop(columns=[], errors="ignore")
    return current.to_dict("records"), previous.to_dict("records")


def delta_text(current: float, previous: float) -> str | None:
    if previous <= 0:
        return None
    return f"{((current - previous) / previous * 100):+.1f}%"


def render_overview() -> None:
    clients = [dict(client) for client in list_clients()]
    all_rows = [dict(row) for row in fetch_metrics()]
    page_header(
        "Sua operacao hoje",
        "Prioridades da carteira, investimento e resultados em uma leitura unica.",
        eyebrow="Creative Media OS | Agencia",
        sync_text="Dados locais atualizados",
    )

    if not clients:
        empty_product(
            "Prepare sua primeira conta",
            "Cadastre um cliente, defina a meta comercial e conecte a Meta. O painel passa a priorizar riscos e oportunidades automaticamente.",
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            render_step("1", "Contexto do cliente", "Objetivo, meta, orcamento e definicao de conversao.")
        with c2:
            render_step("2", "Conexao segura", "Conta de anuncios validada antes da primeira sincronizacao.")
        with c3:
            render_step("3", "Diagnostico inicial", "Riscos, desperdicios e proximas acoes em ordem de impacto.")
        return

    filter_left, filter_right = st.columns([2.4, 1])
    with filter_left:
        client_options = {"Toda a carteira": None, **{client["name"]: client["id"] for client in clients}}
        selected_name = st.selectbox("Escopo", list(client_options), label_visibility="collapsed")
    with filter_right:
        days = st.selectbox("Periodo", [7, 30, 90], index=1, format_func=lambda value: f"Ultimos {value} dias", label_visibility="collapsed")

    selected_id = client_options[selected_name]
    scope_rows = [row for row in all_rows if selected_id is None or row["client_id"] == selected_id]
    current_rows, previous_rows = split_period(scope_rows, days)
    current_kpis = summarize_kpis(current_rows)
    previous_kpis = summarize_kpis(previous_rows)

    current_alerts: list[dict] = []
    attention_clients: set[int] = set()
    for client in clients:
        if selected_id is not None and client["id"] != selected_id:
            continue
        client_rows = [row for row in current_rows if row["client_id"] == client["id"]]
        alerts = [item.to_dict() for item in evaluate_rows(client_rows, client, allow_pause=True)]
        for alert in alerts:
            alert["client_id"] = client["id"]
            alert["client_name"] = client["name"]
        current_alerts.extend(alerts)
        if alerts:
            attention_clients.add(client["id"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investimento", money(current_kpis["spend"]), delta_text(current_kpis["spend"], previous_kpis["spend"]))
    c2.metric("Leads gerados", current_kpis["leads"], delta_text(current_kpis["leads"], previous_kpis["leads"]))
    c3.metric(
        "CPL medio",
        money(current_kpis["cpl"]),
        delta_text(current_kpis["cpl"], previous_kpis["cpl"]),
        delta_color="inverse",
    )
    c4.metric("Contas em atencao", len(attention_clients), f"{len(current_alerts)} sinais ativos")

    section_heading("Prioridades de hoje", "A IA organiza a fila; voce mantem o controle das decisoes.")
    if current_alerts:
        severity_order = {"vermelho": 0, "amarelo": 1}
        priorities = sorted(current_alerts, key=lambda item: severity_order.get(item.get("severity"), 9))[:3]
        cols = st.columns(3)
        for col, alert in zip(cols, priorities):
            tone = "critical" if alert["severity"] == "vermelho" else "warning"
            with col:
                command_card(
                    "Acao imediata" if tone == "critical" else "Oportunidade de melhoria",
                    f"{alert['client_name']} | {alert['campaign']}",
                    alert["reason"],
                    f"Recomendacao: {alert['action'].replace('_', ' ')}",
                    tone=tone,
                )
    else:
        command_card(
            "Carteira monitorada",
            "Nenhum risco objetivo encontrado",
            "As regras atuais nao identificaram desperdicio, CPL alto, CTR baixo ou fadiga de frequencia.",
            "Continue acompanhando a qualidade dos leads antes de escalar.",
            tone="good",
        )

    left, right = st.columns([1.65, 1])
    with left:
        section_heading("Evolucao do investimento", "Leitura diaria do periodo selecionado.")
        if current_rows:
            chart = pd.DataFrame(current_rows)
            chart["date"] = pd.to_datetime(chart["date"], errors="coerce")
            chart = chart.dropna(subset=["date"]).groupby("date", as_index=True)[["spend", "leads"]].sum()
            st.line_chart(chart, width="stretch")
        else:
            empty_product("Sem dados neste periodo", "Sincronize a Meta ou selecione um periodo maior para visualizar a evolucao.")
    with right:
        section_heading("Leitura da IA", "Resumo executivo, sem linguagem tecnica.")
        if current_rows:
            analysis_client = next((client for client in clients if client["id"] == selected_id), {"name": "Carteira Creative"})
            brief = ai_analysis(analysis_client, current_rows, current_alerts)
            st.markdown(f"<div class='soft-card'><p style='white-space:pre-line;margin:0'>{escape(brief)}</p></div>", unsafe_allow_html=True)
        else:
            empty_product("Analise indisponivel", "Ainda nao existe volume de dados suficiente para uma recomendacao confiavel.")

    section_heading("Saude da carteira", "Contas ordenadas para facilitar a gestao diaria.")
    account_html: list[str] = []
    visible_clients = [client for client in clients if selected_id is None or client["id"] == selected_id]
    for client in visible_clients:
        client_rows = [row for row in current_rows if row["client_id"] == client["id"]]
        client_kpis = summarize_kpis(client_rows)
        alerts = [item.to_dict() for item in evaluate_rows(client_rows, client, allow_pause=True)]
        red_count = sum(1 for alert in alerts if alert["severity"] == "vermelho")
        if red_count:
            health_class, health_label = "critical", "Critica"
        elif alerts:
            health_class, health_label = "warning", "Atencao"
        else:
            health_class, health_label = "good", "Saudavel"
        budget = float(client.get("monthly_budget") or 0)
        pacing = min((client_kpis["spend"] / budget * 100), 100) if budget else 0
        target = float(client.get("target_cpl") or 0)
        target_text = money(target) if target else "Nao definida"
        account_html.append(
            "<div class='account-row'>"
            f"<div><div class='account-name'>{escape(client['name'])}</div><div class='account-sub'>{escape(client.get('niche') or 'Segmento nao informado')}</div></div>"
            f"<div class='account-value'><strong>{money(client_kpis['spend'])}</strong><div class='progress-track'><div class='progress-fill' style='width:{pacing:.0f}%'></div></div></div>"
            f"<div class='account-value'>{client_kpis['leads']} leads<br><span class='account-sub'>CPL {money(client_kpis['cpl'])}</span></div>"
            f"<div class='account-value'>Meta {target_text}<br><span class='account-sub'>{len(alerts)} sinal(is)</span></div>"
            f"<div><span class='health {health_class}'><span class='health-dot'></span>{health_label}</span></div>"
            "</div>"
        )
    st.markdown("".join(account_html), unsafe_allow_html=True)


def render_help() -> None:
    page_header(
        "Ajuda e suporte",
        "Encontre o caminho certo para conectar contas, interpretar alertas e operar o sistema com seguranca.",
        eyebrow="Suporte | Creative",
    )
    a, b, c = st.columns(3)
    with a:
        render_step("1", "Clientes", "Cadastre o cliente com objetivo, meta e limites antes de qualquer automacao.")
    with b:
        render_step("2", "Conexoes", "Conecte a Meta primeiro. Quando a conta valida, voce para de depender de export manual.")
    with c:
        render_step("3", "Rotina", "Use a rotina diaria para entender o que corrigir, o que pausar e o que testar.")
    st.markdown(
        "<div class='soft-card'><strong>Observacao</strong><p class='muted'>Google Ads continua no roadmap imediato. O foco agora e deixar Meta impecavel e a interface com cara de produto.</p></div>",
        unsafe_allow_html=True,
    )


def render_clients() -> None:
    page_header(
        "Clientes",
        "Centralize metas, orcamentos, canais e regras de cada operacao.",
        eyebrow="Operacao | Carteira",
    )
    clients = [dict(client) for client in list_clients()]
    portfolio_tab, form_tab = st.tabs(["Carteira", "Adicionar ou editar"])

    with portfolio_tab:
        if not clients:
            empty_product("Nenhum cliente cadastrado", "Abra a aba Adicionar ou editar para preparar a primeira operacao.")
        else:
            rows = [dict(row) for row in fetch_metrics()]
            current_rows, _ = split_period(rows, 30)
            total_budget = sum(float(client.get("monthly_budget") or 0) for client in clients)
            total_spend = summarize_kpis(current_rows)["spend"]
            configured = sum(1 for client in clients if client.get("target_cpl") and client.get("monthly_budget"))
            meta_accounts = sum(1 for client in clients if client.get("meta_account"))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Clientes ativos", len(clients))
            c2.metric("Orcamento monitorado", money(total_budget))
            c3.metric("Investido em 30 dias", money(total_spend))
            c4.metric("Contas configuradas", f"{configured}/{len(clients)}", f"{meta_accounts} com Meta vinculada")

            section_heading("Carteira da agencia", "Resultado, meta e qualidade da configuracao por cliente.")
            account_html: list[str] = []
            for client in clients:
                client_rows = [row for row in current_rows if row["client_id"] == client["id"]]
                kpis = summarize_kpis(client_rows)
                alerts = [item.to_dict() for item in evaluate_rows(client_rows, client, allow_pause=True)]
                red = any(alert["severity"] == "vermelho" for alert in alerts)
                if red:
                    health_class, health_label = "critical", "Critica"
                elif alerts:
                    health_class, health_label = "warning", "Atencao"
                elif client_rows:
                    health_class, health_label = "good", "Saudavel"
                else:
                    health_class, health_label = "warning", "Sem dados"
                budget = float(client.get("monthly_budget") or 0)
                pacing = min(kpis["spend"] / budget * 100, 100) if budget else 0
                target = float(client.get("target_cpl") or 0)
                account_html.append(
                    "<div class='account-row'>"
                    f"<div><div class='account-name'>{escape(client['name'])}</div><div class='account-sub'>{escape(client.get('channels') or 'Canais nao definidos')}</div></div>"
                    f"<div class='account-value'><strong>{money(kpis['spend'])}</strong><div class='progress-track'><div class='progress-fill' style='width:{pacing:.0f}%'></div></div></div>"
                    f"<div class='account-value'>{kpis['leads']} leads<br><span class='account-sub'>CPL {money(kpis['cpl'])}</span></div>"
                    f"<div class='account-value'>Meta {money(target) if target else 'Nao definida'}<br><span class='account-sub'>{len(alerts)} sinal(is)</span></div>"
                    f"<div><span class='health {health_class}'><span class='health-dot'></span>{health_label}</span></div>"
                    "</div>"
                )
            st.markdown("".join(account_html), unsafe_allow_html=True)

    with form_tab:
        edit_mode = st.radio("Acao", ["Novo cliente", "Editar cliente"], horizontal=True)
        selected_client: dict = {}
        if edit_mode == "Editar cliente" and clients:
            selected_name = st.selectbox("Cliente para editar", [client["name"] for client in clients])
            selected_client = next(client for client in clients if client["name"] == selected_name)
        elif edit_mode == "Editar cliente":
            st.info("Cadastre um cliente antes de usar a edicao.")

        channel_options = ["Meta Ads", "Instagram", "Google Ads"]
        saved_channels = [item.strip() for item in str(selected_client.get("channels") or "").split(",") if item.strip() in channel_options]
        defaults = saved_channels or (["Meta Ads", "Instagram"] if edit_mode == "Novo cliente" else [])
        with st.form("client_form"):
            section_heading("Contexto comercial", "Essas informacoes orientam a analise e as recomendacoes da IA.")
            left, right = st.columns(2)
            with left:
                name = st.text_input("Nome do cliente", value=str(selected_client.get("name") or ""), placeholder="Ex: Bruna Dantas Corretora")
                niche = st.text_input("Nicho", value=str(selected_client.get("niche") or ""), placeholder="Ex: imobiliario, clinica, educacao")
                objective = st.text_area(
                    "Objetivo principal",
                    value=str(selected_client.get("objective") or "Gerar leads qualificados pelo WhatsApp ou formulario"),
                )
                channels = st.multiselect("Canais ativos", channel_options, default=defaults)
            with right:
                monthly_budget = st.number_input("Orcamento mensal", min_value=0.0, value=float(selected_client.get("monthly_budget") or 0), step=100.0)
                target_cpl = st.number_input("Meta de CPL", min_value=0.0, value=float(selected_client.get("target_cpl") or 0), step=5.0)
                waste_limit = st.number_input(
                    "Limite de gasto sem lead",
                    min_value=0.0,
                    value=float(selected_client.get("waste_limit") or 100),
                    step=10.0,
                    help="Ao atingir este valor sem conversao, o sistema gera uma recomendacao de pausa.",
                )
                min_ctr = st.number_input("CTR minimo (%)", min_value=0.0, value=float(selected_client.get("min_ctr") or 0.8), step=0.1)
                max_frequency = st.number_input("Frequencia maxima no Meta", min_value=0.0, value=float(selected_client.get("max_frequency") or 3.0), step=0.1)

            section_heading("Contas e contexto", "Vinculos usados na sincronizacao e na leitura estrategica.")
            account_left, account_right = st.columns(2)
            with account_left:
                meta_account = st.text_input("Conta Meta Ads", value=str(selected_client.get("meta_account") or ""), placeholder="act_123456789")
                google_account = st.text_input("Conta Google Ads", value=str(selected_client.get("google_account") or ""), placeholder="123-456-7890")
            with account_right:
                links = st.text_area("Links importantes", value=str(selected_client.get("links") or ""), placeholder="Site, landing page, WhatsApp e formulario")
                notes = st.text_area("Contexto da operacao", value=str(selected_client.get("notes") or ""), placeholder="Oferta, publico, regioes, restricoes e historico")
            submitted = st.form_submit_button("Salvar cliente", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Informe o nome do cliente.")
                else:
                    client_id = upsert_client(
                        {
                            "name": name.strip(),
                            "niche": niche,
                            "objective": objective,
                            "channels": ", ".join(channels),
                            "monthly_budget": monthly_budget,
                            "target_cpl": target_cpl,
                            "waste_limit": waste_limit,
                            "min_ctr": min_ctr,
                            "max_frequency": max_frequency,
                            "meta_account": meta_account,
                            "google_account": google_account,
                            "links": links,
                            "notes": notes,
                        }
                    )
                    st.success(f"Cliente salvo com sucesso. ID {client_id}.")


def render_imports() -> None:
    page_header(
        "Fonte de dados",
        "Use a conexao automatica como fonte principal e arquivos apenas para auditorias ou contingencia.",
        eyebrow="Configuracao | Dados",
    )
    client_id, client = select_client("Cliente para importacao", key="import_client")
    if not client_id:
        return
    left, right = st.columns([1, 2])
    with left:
        platform = st.selectbox(
            "Canal do arquivo",
            ["meta_ads", "google_ads"],
            format_func=lambda item: "Meta/Instagram Ads" if item == "meta_ads" else "Google Ads",
        )
        uploaded = st.file_uploader("Arquivo CSV", type=["csv"])
        st.markdown("<p class='muted'>Use isso quando precisar auditar um export especifico ou quando a API ainda nao estiver pronta.</p>", unsafe_allow_html=True)
    with right:
        if uploaded:
            rows = read_csv(uploaded, platform=platform, source_file=uploaded.name)
            st.markdown(
                f"<div class='soft-card'><strong>{len(rows)} linha(s) reconhecida(s)</strong><p class='muted'>Confira a previa antes de salvar.</p></div>",
                unsafe_allow_html=True,
            )
            st.dataframe(format_df(pd.DataFrame(rows)).head(30), width="stretch")
            if st.button("Importar para o banco", type="primary"):
                count = insert_metrics(client_id, rows)
                st.success(f"{count} linha(s) importada(s) para {client['name']}.")
        else:
            st.info("Selecione um arquivo para ver a previa.")


def render_campaigns() -> None:
    page_header(
        "Campanhas",
        "Compare canais, encontre vencedores e investigue desperdicios sem abrir cada gerenciador de anuncios.",
        eyebrow="Operacao | Analise",
        sync_text="Leitura consolidada",
    )
    client_id, client = select_client("Cliente", key="campaign_client")
    if not client_id:
        return
    rows = [dict(row) for row in fetch_metrics(client_id)]
    if not rows:
        empty_product("Nenhuma campanha sincronizada", "Conecte a conta de anuncios ou importe um arquivo para iniciar a analise.")
        return

    filter_one, filter_two = st.columns([1.4, 1])
    platforms = sorted({row["platform"] for row in rows})
    with filter_one:
        selected_platform = st.selectbox(
            "Canal",
            ["all", *platforms],
            format_func=lambda value: "Todos os canais" if value == "all" else ("Meta Ads" if value == "meta_ads" else "Google Ads"),
        )
    with filter_two:
        days = st.selectbox("Periodo da analise", [7, 30, 90], index=1, format_func=lambda value: f"Ultimos {value} dias")

    filtered = [row for row in rows if selected_platform == "all" or row["platform"] == selected_platform]
    current, previous = split_period(filtered, days)
    kpis = summarize_kpis(current)
    previous_kpis = summarize_kpis(previous)
    alerts = [item.to_dict() for item in evaluate_rows(current, client, allow_pause=True)]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Investimento", money(kpis["spend"]), delta_text(kpis["spend"], previous_kpis["spend"]))
    c2.metric("Leads", kpis["leads"], delta_text(kpis["leads"], previous_kpis["leads"]))
    c3.metric("CPL", money(kpis["cpl"]), delta_text(kpis["cpl"], previous_kpis["cpl"]), delta_color="inverse")
    c4.metric("CTR", f"{kpis['ctr']:.2f}%")
    c5.metric("Alertas", len(alerts))

    tabs = st.tabs(["Desempenho", "Campanhas", "Criativos e anuncios", "Diagnostico"])
    with tabs[0]:
        section_heading("Distribuicao de resultado", "Investimento e leads por campanha.")
        campaign_df = pd.DataFrame(current)
        if not campaign_df.empty:
            ranking = campaign_df.groupby("campaign", as_index=False)[["spend", "leads"]].sum()
            ranking["cpl"] = ranking.apply(lambda row: row["spend"] / row["leads"] if row["leads"] else 0, axis=1)
            ranking = ranking.sort_values("spend", ascending=False).head(12)
            st.bar_chart(ranking.set_index("campaign")[["spend", "leads"]], width="stretch")
            st.dataframe(
                ranking.rename(columns={"campaign": "Campanha", "spend": "Investimento", "leads": "Leads", "cpl": "CPL"}),
                width="stretch",
                hide_index=True,
            )
    with tabs[1]:
        frame = format_df(pd.DataFrame(current))
        columns = [column for column in ["Data", "Canal", "Campanha", "Grupo/Conjunto", "Gasto", "Leads", "CPL", "CTR", "CPC", "Frequencia"] if column in frame.columns]
        st.dataframe(frame[columns], width="stretch", hide_index=True)
    with tabs[2]:
        creative_df = pd.DataFrame(current)
        creative_df = creative_df[creative_df["ad_name"].fillna("").astype(str).str.strip() != ""]
        if creative_df.empty:
            empty_product("Criativos ainda nao identificados", "Sincronize no nivel de anuncio para comparar pecas, fadiga e mensagens vencedoras.")
        else:
            creative = creative_df.groupby("ad_name", as_index=False)[["spend", "leads", "clicks", "impressions"]].sum()
            creative["cpl"] = creative.apply(lambda row: row["spend"] / row["leads"] if row["leads"] else 0, axis=1)
            creative["ctr"] = creative.apply(lambda row: row["clicks"] / row["impressions"] * 100 if row["impressions"] else 0, axis=1)
            st.dataframe(
                creative.sort_values(["leads", "spend"], ascending=[False, False]).rename(
                    columns={"ad_name": "Anuncio", "spend": "Investimento", "leads": "Leads", "cpl": "CPL", "ctr": "CTR"}
                ),
                width="stretch",
                hide_index=True,
            )
    with tabs[3]:
        render_alerts(alerts, limit=20)


def render_routine() -> None:
    page_header(
        "Central de acoes",
        "Recomendacoes priorizadas por risco, impacto e urgencia. Nenhuma mudanca sensivel acontece sem registro.",
        eyebrow="Operacao | IA assistida",
        sync_text="Modo seguro ativo",
    )
    client_id, client = select_client("Cliente da rotina", key="routine_client")
    if not client_id:
        return
    status_badge(f"Meta CPL: {money(float(client.get('target_cpl') or 0))}")
    status_badge(f"Pausa sem lead: {money(float(client.get('waste_limit') or 0))}")
    status_badge(f"CTR minimo: {float(client.get('min_ctr') or 0):.2f}%")

    rows = [dict(row) for row in fetch_metrics(client_id)]
    if not rows:
        st.info("Ainda nao ha dados para esse cliente. Conecte a Meta ou importe um arquivo.")
        return

    alerts = [item.to_dict() for item in evaluate_rows(rows, client, allow_pause=True)]
    analysis = ai_analysis(client, rows, alerts)
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("### Leitura do dia")
        st.markdown(f"<div class='soft-card'><pre>{analysis}</pre></div>", unsafe_allow_html=True)
        st.markdown("### Ideias de teste")
        st.markdown(f"<div class='soft-card'><pre>{generate_campaign_ideas(client, rows, alerts)}</pre></div>", unsafe_allow_html=True)
    with right:
        st.markdown("### Fila de acao")
        render_alerts(alerts)
        pause_alerts = [item for item in alerts if item.get("should_pause")]
        if pause_alerts:
            st.markdown("<p class='muted'>As pausas continuam em dry-run nesta fase. Primeiro leitura confiavel, depois automacao real.</p>", unsafe_allow_html=True)
            if st.button("Registrar pausas recomendadas", type="primary"):
                for alert in pause_alerts:
                    log_action(
                        {
                            "client_id": client_id,
                            "platform": alert["platform"],
                            "campaign": alert["campaign"],
                            "entity_level": alert["entity_level"],
                            "entity_name": alert["entity_name"],
                            "rule_name": alert["rule_name"],
                            "action": alert["action"],
                            "mode": "dry-run",
                            "reason": alert["reason"],
                        }
                    )
                st.success(f"{len(pause_alerts)} acao(oes) registradas em dry-run.")

    st.markdown("### Historico de acoes")
    logs_df = rows_to_df(fetch_action_logs(client_id))
    if logs_df.empty:
        st.caption("Nenhuma acao registrada ainda.")
    else:
        st.dataframe(logs_df, width="stretch")


def render_reports() -> None:
    page_header(
        "Relatorios",
        "Transforme dados, decisoes e trabalho executado em uma leitura clara para o cliente.",
        eyebrow="Operacao | Prestacao de contas",
    )
    client_id, client = select_client("Cliente do relatorio", key="report_client")
    if not client_id:
        return
    rows = [dict(row) for row in fetch_metrics(client_id)]
    if not rows:
        st.info("Ainda nao ha dados para esse cliente.")
        return

    alerts = [item.to_dict() for item in evaluate_rows(rows, client, allow_pause=True)]
    analysis = ai_analysis(client, rows, alerts)
    st.markdown("### Previa")
    render_alerts(alerts, limit=5)
    st.text(analysis)
    if st.button("Gerar relatorio HTML", type="primary"):
        path = generate_html_report(client, rows, alerts, analysis)
        st.success(f"Relatorio gerado em: {path}")
        st.download_button("Baixar HTML", path.read_bytes(), file_name=path.name, mime="text/html")


def render_meta_tab(env_values: dict[str, str]) -> None:
    connector = MetaAdsConnector()
    result = connector.validate().to_dict()
    render_connector_card(
        "Meta Ads e Instagram",
        "Essa e a conexao prioritaria. Quando ela entra, o sistema para de depender de CSV e vira um produto muito mais confiavel.",
        result,
        mode="active",
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Conectado" if result["ok"] else "Pendente")
    c2.metric("Token", "Preenchido" if env_values.get("META_ACCESS_TOKEN") else "Vazio")
    c3.metric("Conta", "Preenchida" if env_values.get("META_AD_ACCOUNT_ID") else "Vazia")

    if result["ok"] and result["payload"].get("account"):
        account = result["payload"]["account"]
        st.markdown(
            f"<div class='summary-strip'><strong>Conta validada:</strong> {account.get('name', '')} | "
            f"ID: {account.get('id', '')} | Moeda: {account.get('currency', '')} | Fuso: {account.get('timezone_name', '')}</div>",
            unsafe_allow_html=True,
        )
    elif result.get("message"):
        st.warning(result["message"])

    left, right = st.columns([1.05, 1])
    with left:
        with st.form("meta_config_form"):
            st.markdown("### Conectar Meta")
            meta_access_token = st.text_input(
                "Access token",
                value=env_values.get("META_ACCESS_TOKEN", ""),
                type="password",
                placeholder="Cole aqui o token da Meta",
            )
            meta_ad_account_id = st.text_input(
                "Conta de anuncios",
                value=env_values.get("META_AD_ACCOUNT_ID", ""),
                placeholder="act_123456789",
            )
            save_meta = st.form_submit_button("Salvar credenciais da Meta", type="primary")
            if save_meta:
                write_env_values(
                    {
                        "META_ACCESS_TOKEN": meta_access_token.strip(),
                        "META_AD_ACCOUNT_ID": meta_ad_account_id.strip(),
                    }
                )
                load_env_file()
                st.success("Credenciais da Meta salvas.")
                st.rerun()
    with right:
        st.markdown("### Fluxo visual")
        s1, s2, s3 = st.columns(3)
        with s1:
            render_step("1", "Criar app", "Use um app no Meta for Developers com Marketing API.")
        with s2:
            render_step("2", "Gerar token", "Use ads_read para leitura e ads_management para automacao futura.")
        with s3:
            render_step("3", "Validar", "Cole token e conta aqui. O sistema testa e informa se conectou.")
        st.markdown(f"<p class='muted'>Docs oficiais: {connector.docs_url}</p>", unsafe_allow_html=True)
        st.write(f"Token atual: {mask_secret(env_values.get('META_ACCESS_TOKEN', ''))}")
        st.write(f"Conta atual: {env_values.get('META_AD_ACCOUNT_ID', 'Nao preenchida')}")

    st.markdown("### Sincronizar ultimos 30 dias")
    client_id, client = select_client("Cliente que vai receber os dados da Meta", key="meta_sync_client")
    if client_id:
        st.markdown(
            f"<div class='soft-card'><strong>Cliente selecionado:</strong> {client['name']}<p class='muted'>O sistema substitui o snapshot anterior da Meta para esse cliente, evitando dado duplicado.</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("Puxar ultimos 30 dias da Meta", type="primary"):
            with st.spinner("Consultando Meta e montando snapshot..."):
                sync_result = connector.fetch_campaign_snapshot("last_30d", "adset").to_dict()
            if not sync_result["ok"]:
                st.error(sync_result["message"])
            else:
                rows = sync_result["payload"].get("rows", [])
                count = replace_metrics_for_source(client_id, "meta_ads", "meta_api_last_30d", rows)
                st.success(f"{count} linha(s) sincronizada(s) da Meta para {client['name']}.")
                if rows:
                    st.dataframe(format_df(pd.DataFrame(rows)).head(20), width="stretch")


def render_google_tab(env_values: dict[str, str]) -> None:
    connector = GoogleAdsConnector()
    result = connector.validate().to_dict()
    render_connector_card(
        "Google Ads",
        "A mesma experiencia premium da Meta vai entrar aqui. Nesta fase, o foco e preparar credenciais e deixar o fluxo pronto.",
        result,
        mode="coming_soon",
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Conectado" if result["ok"] else "Em configuracao")
    c2.metric("Developer token", "Preenchido" if env_values.get("GOOGLE_ADS_DEVELOPER_TOKEN") else "Vazio")
    c3.metric("Customer ID", "Preenchido" if env_values.get("GOOGLE_ADS_CUSTOMER_ID") else "Vazio")

    left, right = st.columns([1.05, 1])
    with left:
        with st.form("google_config_form"):
            st.markdown("### Preparar Google Ads")
            developer_token = st.text_input("Developer token", value=env_values.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""), type="password")
            client_id = st.text_input("Client ID", value=env_values.get("GOOGLE_ADS_CLIENT_ID", ""))
            client_secret = st.text_input("Client secret", value=env_values.get("GOOGLE_ADS_CLIENT_SECRET", ""), type="password")
            refresh_token = st.text_input("Refresh token", value=env_values.get("GOOGLE_ADS_REFRESH_TOKEN", ""), type="password")
            login_customer_id = st.text_input("Login customer ID", value=env_values.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""))
            customer_id = st.text_input("Customer ID", value=env_values.get("GOOGLE_ADS_CUSTOMER_ID", ""))
            save_google = st.form_submit_button("Salvar dados do Google Ads")
            if save_google:
                write_env_values(
                    {
                        "GOOGLE_ADS_DEVELOPER_TOKEN": developer_token.strip(),
                        "GOOGLE_ADS_CLIENT_ID": client_id.strip(),
                        "GOOGLE_ADS_CLIENT_SECRET": client_secret.strip(),
                        "GOOGLE_ADS_REFRESH_TOKEN": refresh_token.strip(),
                        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": login_customer_id.strip(),
                        "GOOGLE_ADS_CUSTOMER_ID": customer_id.strip(),
                    }
                )
                load_env_file()
                st.success("Dados do Google Ads salvos.")
                st.rerun()
    with right:
        st.markdown("### O que vem depois")
        render_step("1", "Validar token", "Conferir leitura real da conta e sinalizar erro de forma amigavel.")
        render_step("2", "Sincronizar dados", "Trazer snapshot dos ultimos 30 dias no mesmo padrao da Meta.")
        render_step("3", "Automatizar", "Deixar criacao e ajustes leves no mesmo fluxo guiado.")
        st.markdown(f"<p class='muted'>Docs oficiais: {connector.docs_url}</p>", unsafe_allow_html=True)


def render_connections() -> None:
    page_header(
        "Integracoes",
        "Conecte plataformas e acompanhe a qualidade de cada fonte sem expor detalhes tecnicos ao usuario final.",
        eyebrow="Configuracao | Integracoes",
    )
    env_values = read_env_values()
    meta_result = MetaAdsConnector().validate().to_dict()
    google_result = GoogleAdsConnector().validate().to_dict()
    ready = sum(1 for item in [meta_result, google_result] if item["ok"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Plataformas prontas", ready)
    c2.metric("Pendentes", 2 - ready)
    c3.metric("Arquivo .env", "OK" if ENV_PATH.exists() else "Criar")

    st.markdown(
        "<div class='soft-card'><strong>Direcao do sistema</strong><p class='muted'>Primeiro deixamos a Meta impecavel, com validacao real e sincronizacao. Depois repetimos o mesmo padrao visual e tecnico para Google Ads.</p></div>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Meta Ads e Instagram", "Google Ads"])
    with tabs[0]:
        render_meta_tab(env_values)
    with tabs[1]:
        render_google_tab(env_values)


page = render_sidebar()

if page == "overview":
    render_overview()
elif page == "help":
    render_help()
elif page == "clients":
    render_clients()
elif page == "imports":
    render_imports()
elif page == "routine":
    render_routine()
elif page == "campaigns":
    render_campaigns()
elif page == "reports":
    render_reports()
elif page == "connections":
    render_connections()
