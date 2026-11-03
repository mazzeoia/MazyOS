"""Standardized naming convention for Meta Ads entities.

Pattern: [MARCA] | objetivo | publico | AAAAMMDD-HHMM
"""

from __future__ import annotations

from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def campaign_name(marca: str, objetivo: str, publico: str) -> str:
    """[MARCA] | objetivo | publico | AAAAMMDD-HHMM"""
    return f"[{marca}] | {objetivo} | {publico} | {_timestamp()}"


def adset_name(marca: str, segmento: str) -> str:
    """[MARCA] | segmento | AAAAMMDD-HHMM"""
    return f"[{marca}] | {segmento} | {_timestamp()}"


def ad_name(marca: str, criativo: str) -> str:
    """[MARCA] | criativo | AAAAMMDD-HHMM"""
    return f"[{marca}] | {criativo} | {_timestamp()}"
