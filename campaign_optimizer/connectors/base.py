"""Prepared connector contract. Real API writes stay behind dry-run validation."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import os


@dataclass
class ConnectorResult:
    ok: bool
    platform: str
    mode: str
    message: str
    payload: dict

    def to_dict(self) -> dict:
        return asdict(self)


class BaseAdsConnector:
    platform = "base"
    required_env: tuple[str, ...] = ()
    docs_url = ""
    setup_items: tuple[str, ...] = ()

    def validate(self) -> ConnectorResult:
        missing = [key for key in self.required_env if not os.getenv(key)]
        if missing:
            return ConnectorResult(
                False,
                self.platform,
                "setup",
                "Credenciais ausentes.",
                {
                    "missing_env": missing,
                    "docs_url": self.docs_url,
                    "setup_items": list(self.setup_items),
                },
            )
        return ConnectorResult(True, self.platform, "ready", "Credenciais encontradas.", {"docs_url": self.docs_url})

    def pause_entity(self, entity_id: str, entity_level: str, reason: str, dry_run: bool = True) -> ConnectorResult:
        payload = {"entity_id": entity_id, "entity_level": entity_level, "reason": reason}
        if dry_run:
            return ConnectorResult(True, self.platform, "dry-run", "Acao simulada. Nada foi alterado na conta.", payload)
        return ConnectorResult(False, self.platform, "blocked", "Pausa real ainda exige validacao final da API nesta V1.", payload)
