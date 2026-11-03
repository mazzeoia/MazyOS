"""Date-preset helpers shared across sync and analysis endpoints.

Meta's Marketing API resolves a `date_preset` (e.g. "last_7d") into an
absolute date range on its side when fetching insights. Locally we only
store the resulting rows tagged with `metric_date`, so filtering
already-synced data by period means re-deriving that same start date here.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

PRESET_LABELS = {
    "today": "Hoje",
    "yesterday": "Ontem",
    "last_7d": "Últimos 7 dias",
    "last_14d": "Últimos 14 dias",
    "last_30d": "Últimos 30 dias",
    "this_month": "Este mês",
}


def date_preset_to_start_date(preset: str, today: date | None = None) -> str:
    """Translate a Meta-style date_preset into an ISO start date (inclusive).

    Unknown presets fall back to the last_7d window, matching the schema
    defaults on EvaluateRequest/SummaryRequest/SyncRequest.
    """
    today = today or datetime.now(timezone.utc).date()

    if preset == "today":
        start = today
    elif preset == "yesterday":
        start = today - timedelta(days=1)
    elif preset == "last_14d":
        start = today - timedelta(days=14)
    elif preset == "last_30d":
        start = today - timedelta(days=30)
    elif preset == "this_month":
        start = today.replace(day=1)
    else:  # "last_7d" and any unrecognized value
        start = today - timedelta(days=7)

    return start.isoformat()
