"""SMTP email sender for automation notifications.

Best-effort only: if credentials aren't configured, or sending fails,
this logs and returns without raising — a notification failure must never
break the automation run that triggered it.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from app.config import Settings

logger = logging.getLogger(__name__)


def send_email(settings: Settings, to: str, subject: str, body: str) -> bool:
    """Send a plaintext email. Returns True on success, False otherwise."""
    if not settings.smtp_user or not settings.smtp_password:
        logger.info("SMTP not configured (SMTP_USER/SMTP_PASSWORD blank) — skipping email to %s", to)
        return False

    if not to:
        logger.warning("send_email called without a recipient — skipping")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"] = to

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, [to], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc, exc_info=True)
        return False
