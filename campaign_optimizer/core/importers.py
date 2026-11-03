"""CSV import and normalization for Google Ads and Meta Ads exports."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import unicodedata

import pandas as pd

COLUMN_ALIASES = {
    "date": [
        "date",
        "dia",
        "data",
        "day",
        "inicio dos relatorios",
        "encerramento dos relatorios",
        "reporting starts",
        "reporting ends",
    ],
    "campaign": ["campaign", "campanha", "campaign name", "nome da campanha"],
    "ad_group": [
        "ad group",
        "grupo de anuncios",
        "grupo de anuncio",
        "conjunto",
        "ad set",
        "adset",
        "grupo",
        "nome do conjunto de anuncios",
    ],
    "ad_name": ["ad", "ad name", "anuncio", "nome do anuncio", "creative", "criativo"],
    "impressions": ["impressions", "impressoes", "impr.", "impressoes"],
    "reach": ["reach", "alcance"],
    "clicks": ["clicks", "cliques", "cliques no link", "link clicks", "interactions"],
    "ctr": ["ctr", "ctr (link click-through rate)", "taxa de cliques", "ctr medio"],
    "cpc": ["cpc", "avg. cpc", "cpc medio", "custo por clique"],
    "cpm": ["cpm", "custo por 1.000 impressoes", "custo por mil"],
    "frequency": ["frequency", "frequencia"],
    "spend": ["spend", "cost", "custo", "valor usado", "amount spent", "valor gasto"],
    "leads": ["results", "resultados", "conversions", "conversoes", "leads", "conv.", "resultados (iniciais)"],
    "cpl": ["cost per result", "custo por resultado", "cpa", "cost / conv.", "custo por lead"],
    "balance": ["saldo", "balance", "remaining budget", "orcamento restante"],
}


def normalize_header(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def detect_mapping(columns: list[str]) -> dict[str, str]:
    normalized = {normalize_header(col): col for col in columns}
    mapping: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            alias_normalized = normalize_header(alias)
            if alias_normalized in normalized:
                mapping[target] = normalized[alias_normalized]
                break
            if len(alias_normalized.split()) < 2:
                continue
            partial_match = next(
                (
                    original
                    for key, original in normalized.items()
                    if key.startswith(alias_normalized) or alias_normalized in key
                ),
                None,
            )
            if partial_match:
                mapping[target] = partial_match
                break
    return mapping


def parse_number(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "-"}:
        return 0.0
    text = text.replace("R$", "").replace("%", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    text = re.sub(r"[^0-9.\-]", "", text)
    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_platform(platform: str) -> str:
    value = normalize_header(platform)
    if "google" in value:
        return "google_ads"
    if "instagram" in value:
        return "meta_ads"
    if "meta" in value or "facebook" in value:
        return "meta_ads"
    return value or "unknown"


def read_csv(path_or_buffer, platform: str, source_file: str | None = None) -> list[dict]:
    df = pd.read_csv(path_or_buffer)
    mapping = detect_mapping(list(df.columns))
    today = date.today().isoformat()
    rows: list[dict] = []
    for _, raw in df.iterrows():
        get = lambda key, default="": raw.get(mapping[key], default) if key in mapping else default
        impressions = int(parse_number(get("impressions")))
        reach = int(parse_number(get("reach")))
        clicks = int(parse_number(get("clicks")))
        spend = parse_number(get("spend"))
        leads = int(parse_number(get("leads")))
        ctr = parse_number(get("ctr"))
        if ctr == 0 and impressions:
            ctr = (clicks / impressions) * 100
        cpc = parse_number(get("cpc"))
        if cpc == 0 and clicks:
            cpc = spend / clicks
        cpm = parse_number(get("cpm"))
        if cpm == 0 and impressions:
            cpm = spend / impressions * 1000
        cpl = parse_number(get("cpl"))
        if cpl == 0 and leads:
            cpl = spend / leads
        rows.append(
            {
                "platform": normalize_platform(platform),
                "source_file": source_file or str(getattr(path_or_buffer, "name", "upload.csv")),
                "date": str(get("date", today))[:10] or today,
                "campaign": str(get("campaign", "Campanha sem nome")).strip() or "Campanha sem nome",
                "ad_group": str(get("ad_group", "")).strip(),
                "ad_name": str(get("ad_name", "")).strip(),
                "impressions": impressions,
                "reach": reach,
                "clicks": clicks,
                "ctr": round(ctr, 4),
                "cpc": round(cpc, 4),
                "cpm": round(cpm, 4),
                "frequency": round(parse_number(get("frequency")), 4),
                "spend": round(spend, 2),
                "leads": leads,
                "cpl": round(cpl, 2),
                "balance": parse_number(get("balance")) if "balance" in mapping else None,
                "raw_json": json.dumps(raw.to_dict(), ensure_ascii=False, default=str),
            }
        )
    return rows


def read_csv_file(path: str | Path, platform: str) -> list[dict]:
    path = Path(path)
    return read_csv(path, platform=platform, source_file=path.name)
