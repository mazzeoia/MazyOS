from __future__ import annotations

import json
import os
from typing import Any

import requests

from .base import BaseAdsConnector, ConnectorResult


class MetaAdsConnector(BaseAdsConnector):
    platform = "meta_ads"
    docs_url = "https://developers.facebook.com/docs/marketing-api/"
    api_version = "v23.0"
    required_env = (
        "META_ACCESS_TOKEN",
        "META_AD_ACCOUNT_ID",
    )
    setup_items = (
        "Criar app no Meta for Developers",
        "Liberar permissao ads_read para leitura",
        "Liberar permissao ads_management para alteracoes",
        "Gerar access token com a conta certa",
        "Informar o ad account ID no formato act_123456789",
    )

    def validate(self) -> ConnectorResult:
        base = super().validate()
        if not base.ok:
            return base

        try:
            response = requests.get(
                f"https://graph.facebook.com/{self.api_version}/{os.getenv('META_AD_ACCOUNT_ID')}",
                params={
                    "fields": "id,name,account_status,currency,timezone_name",
                    "access_token": os.getenv("META_ACCESS_TOKEN"),
                },
                timeout=20,
            )
            data = response.json()
        except requests.RequestException as exc:
            return ConnectorResult(
                False,
                self.platform,
                "network_error",
                "Nao consegui falar com a API da Meta.",
                {"error": str(exc), "docs_url": self.docs_url, "setup_items": list(self.setup_items)},
            )

        if not response.ok or "error" in data:
            error = data.get("error", {})
            return ConnectorResult(
                False,
                self.platform,
                "api_error",
                error.get("message", "A Meta recusou a conexao."),
                {
                    "error_code": error.get("code"),
                    "error_subcode": error.get("error_subcode"),
                    "docs_url": self.docs_url,
                    "setup_items": list(self.setup_items),
                },
            )

        return ConnectorResult(
            True,
            self.platform,
            "ready",
            "Conta Meta conectada.",
            {
                "docs_url": self.docs_url,
                "account": {
                    "id": data.get("id", ""),
                    "name": data.get("name", ""),
                    "account_status": data.get("account_status", ""),
                    "currency": data.get("currency", ""),
                    "timezone_name": data.get("timezone_name", ""),
                },
            },
        )

    @staticmethod
    def _extract_metric(items: list[dict[str, Any]] | None, match_terms: tuple[str, ...]) -> float:
        if not items:
            return 0.0
        total = 0.0
        for item in items:
            action_type = str(item.get("action_type", "")).lower()
            if any(term in action_type for term in match_terms):
                try:
                    total += float(item.get("value", 0) or 0)
                except (TypeError, ValueError):
                    continue
        return total

    def fetch_campaign_snapshot(self, date_preset: str = "last_30d", level: str = "adset") -> ConnectorResult:
        validation = self.validate()
        if not validation.ok:
            return validation

        rows: list[dict[str, Any]] = []
        url = f"https://graph.facebook.com/{self.api_version}/{os.getenv('META_AD_ACCOUNT_ID')}/insights"
        params = {
            "access_token": os.getenv("META_ACCESS_TOKEN"),
            "date_preset": date_preset,
            "level": level,
            "limit": 200,
            "fields": ",".join(
                [
                    "campaign_name",
                    "adset_name",
                    "ad_name",
                    "reach",
                    "impressions",
                    "clicks",
                    "ctr",
                    "cpc",
                    "cpm",
                    "spend",
                    "frequency",
                    "actions",
                    "cost_per_action_type",
                    "date_start",
                    "date_stop",
                ]
            ),
        }

        try:
            next_url: str | None = url
            next_params: dict[str, Any] | None = params
            page_count = 0
            while next_url and page_count < 10:
                response = requests.get(next_url, params=next_params, timeout=30)
                data = response.json()
                if not response.ok or "error" in data:
                    error = data.get("error", {})
                    return ConnectorResult(
                        False,
                        self.platform,
                        "api_error",
                        error.get("message", "Nao consegui puxar dados da Meta."),
                        {"docs_url": self.docs_url},
                    )

                for item in data.get("data", []):
                    leads = int(
                        self._extract_metric(
                            item.get("actions"),
                            ("messaging_conversation_started", "lead", "contact", "omni_lead"),
                        )
                    )
                    cpl = self._extract_metric(
                        item.get("cost_per_action_type"),
                        ("messaging_conversation_started", "lead", "contact", "omni_lead"),
                    )
                    spend = float(item.get("spend", 0) or 0)
                    rows.append(
                        {
                            "platform": self.platform,
                            "source_file": f"meta_api_{date_preset}",
                            "date": item.get("date_start", ""),
                            "campaign": item.get("campaign_name", "Campanha sem nome"),
                            "ad_group": item.get("adset_name", ""),
                            "ad_name": item.get("ad_name", ""),
                            "impressions": int(float(item.get("impressions", 0) or 0)),
                            "reach": int(float(item.get("reach", 0) or 0)),
                            "clicks": int(float(item.get("clicks", 0) or 0)),
                            "ctr": round(float(item.get("ctr", 0) or 0), 4),
                            "cpc": round(float(item.get("cpc", 0) or 0), 4),
                            "cpm": round(float(item.get("cpm", 0) or 0), 4),
                            "frequency": round(float(item.get("frequency", 0) or 0), 4),
                            "spend": round(spend, 2),
                            "leads": leads,
                            "cpl": round(cpl or (spend / leads if leads else 0), 2),
                            "balance": None,
                            "raw_json": json.dumps(item, ensure_ascii=False, default=str),
                        }
                    )

                paging = data.get("paging", {})
                next_url = paging.get("next")
                next_params = None
                page_count += 1
        except requests.RequestException as exc:
            return ConnectorResult(
                False,
                self.platform,
                "network_error",
                "Falha de rede ao puxar dados da Meta.",
                {"error": str(exc), "docs_url": self.docs_url},
            )

        return ConnectorResult(
            True,
            self.platform,
            "ready",
            f"Snapshot Meta carregado com {len(rows)} linha(s).",
            {"rows": rows, "docs_url": self.docs_url},
        )
