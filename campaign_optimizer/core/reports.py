"""HTML report generation for client review."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from .database import ensure_client_folder
from .rules import summarize_kpis


def money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_html_report(client: dict, rows: list[dict], alerts: list[dict], analysis: str) -> Path:
    kpis = summarize_kpis(rows)
    folder = ensure_client_folder(client["name"]) / "relatorios"
    filename = f"{datetime.now().strftime('%Y-%m-%d-%H%M')}-relatorio-campanhas.html"
    path = folder / filename

    alert_rows = "".join(
        f"<tr><td>{escape(a.get('severity',''))}</td><td>{escape(a.get('platform',''))}</td>"
        f"<td>{escape(a.get('campaign',''))}</td><td>{escape(a.get('action',''))}</td>"
        f"<td>{escape(a.get('reason',''))}</td></tr>"
        for a in alerts
    ) or "<tr><td colspan='5'>Sem alertas nas regras atuais.</td></tr>"

    campaign_rows = "".join(
        f"<tr><td>{escape(r.get('platform',''))}</td><td>{escape(r.get('campaign',''))}</td>"
        f"<td>{money(float(r.get('spend') or 0))}</td><td>{int(r.get('leads') or 0)}</td>"
        f"<td>{money(float(r.get('cpl') or 0))}</td><td>{float(r.get('ctr') or 0):.2f}%</td></tr>"
        for r in rows[:200]
    ) or "<tr><td colspan='6'>Sem dados importados.</td></tr>"

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Relatorio de Campanhas - {escape(client['name'])}</title>
  <style>
    body {{ margin: 0; background: #050505; color: #f7f7f7; font-family: Arial, sans-serif; }}
    .wrap {{ max-width: 1120px; margin: 0 auto; padding: 32px; }}
    .brand {{ display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #222; padding-bottom:18px; }}
    h1 {{ margin: 0; font-size: 30px; }}
    .mark {{ height: 5px; width: 130px; background: linear-gradient(90deg,#FFD400,#FF7A00,#D00018); border-radius: 99px; }}
    .grid {{ display:grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 24px 0; }}
    .card {{ background:#111; border:1px solid #242424; border-radius:8px; padding:16px; }}
    .label {{ color:#aaa; font-size: 13px; }}
    .value {{ font-size: 26px; font-weight: 800; margin-top: 6px; }}
    pre {{ white-space: pre-wrap; background:#111; border:1px solid #242424; border-radius:8px; padding:16px; line-height:1.45; }}
    table {{ width:100%; border-collapse: collapse; margin-top: 12px; background:#0d0d0d; }}
    th, td {{ border-bottom:1px solid #242424; padding:10px; text-align:left; font-size:14px; }}
    th {{ color:#FFD400; }}
    .note {{ color:#bbb; font-size:13px; margin-top:24px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand"><div><h1>{escape(client['name'])}</h1><p>Relatorio de campanhas</p></div><div class="mark"></div></div>
    <div class="grid">
      <div class="card"><div class="label">Investimento</div><div class="value">{money(kpis['spend'])}</div></div>
      <div class="card"><div class="label">Leads</div><div class="value">{kpis['leads']}</div></div>
      <div class="card"><div class="label">CPL medio</div><div class="value">{money(kpis['cpl'])}</div></div>
      <div class="card"><div class="label">CTR medio</div><div class="value">{kpis['ctr']:.2f}%</div></div>
    </div>
    <h2>Analise executiva</h2>
    <pre>{escape(analysis)}</pre>
    <h2>Alertas e acoes</h2>
    <table><thead><tr><th>Risco</th><th>Canal</th><th>Campanha</th><th>Acao</th><th>Motivo</th></tr></thead><tbody>{alert_rows}</tbody></table>
    <h2>Campanhas</h2>
    <table><thead><tr><th>Canal</th><th>Campanha</th><th>Gasto</th><th>Leads</th><th>CPL</th><th>CTR</th></tr></thead><tbody>{campaign_rows}</tbody></table>
    <div class="note">Leitura baseada em leads de WhatsApp/formulario quando nao houver CRM integrado. Nao representa venda fechada.</div>
  </div>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")
    return path
