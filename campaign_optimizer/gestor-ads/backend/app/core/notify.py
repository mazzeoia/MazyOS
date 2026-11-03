"""Notification dispatch — in-app always, email/WhatsApp per account settings.

WhatsApp is architecturally wired in (the toggle and column exist) but not
functional yet: sending real WhatsApp messages needs a verified WhatsApp
Business Account + approved message templates, which this project doesn't
have configured. Until then, a WhatsApp request just logs and no-ops.
"""

from __future__ import annotations

import logging

from supabase import Client

from app.config import Settings
from app.shared.email import send_email

logger = logging.getLogger(__name__)


async def notify(
    supabase: Client,
    settings: Settings,
    owner_id: str,
    ad_account_id: str,
    title: str,
    body: str,
    severity: str = "info",
    notify_email: bool = False,
    notify_whatsapp: bool = False,
    owner_email: str = "",
) -> None:
    """Record an in-app notification and fan out to other enabled channels.

    Best-effort throughout: a delivery failure on one channel never blocks
    the others, and never raises into the caller (automation runs must
    finish and log even if notifying fails).
    """
    try:
        supabase.table("notifications").insert(
            {
                "owner_id": owner_id,
                "ad_account_id": ad_account_id,
                "title": title,
                "body": body,
                "severity": severity,
            }
        ).execute()
    except Exception as exc:
        logger.error("Failed to write in-app notification: %s", exc, exc_info=True)

    if notify_email:
        send_email(settings, owner_email, title, body)

    if notify_whatsapp:
        logger.info(
            "WhatsApp notification requested for owner %s but the channel isn't configured yet — skipping",
            owner_id,
        )
