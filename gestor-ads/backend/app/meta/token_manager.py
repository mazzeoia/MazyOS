from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from app.shared.crypto import decrypt_token, encrypt_token
from app.shared.exceptions import MetaAPIError


@dataclass
class TokenPair:
    access_token: str
    expires_at: datetime


class TokenManager:
    """Manages Meta OAuth tokens — encrypt, decrypt, exchange, extend, refresh, revoke."""

    GRAPH_URL = "https://graph.facebook.com/v23.0"

    def __init__(self, fernet_key: str, meta_app_id: str, meta_app_secret: str):
        self._fernet_key = fernet_key
        self._app_id = meta_app_id
        self._app_secret = meta_app_secret

    def encrypt(self, token: str) -> str:
        return encrypt_token(token, self._fernet_key)

    def decrypt(self, encrypted: str) -> str:
        return decrypt_token(encrypted, self._fernet_key)

    async def exchange_code(self, code: str) -> TokenPair:
        """Exchange authorization code for a long-lived token.

        Flow: code -> short-lived token -> long-lived token (60 days).
        """
        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: code -> short-lived
            resp = await client.get(
                f"{self.GRAPH_URL}/oauth/access_token",
                params={
                    "client_id": self._app_id,
                    "client_secret": self._app_secret,
                    "code": code,
                },
            )
            data = resp.json()
            if resp.status_code != 200 or "error" in data:
                msg = data.get("error", {}).get("message", "Erro ao trocar código OAuth")
                raise MetaAPIError(msg)

            short_lived = data["access_token"]

            # Step 2: short-lived -> long-lived
            return await self.extend_token(short_lived, client)

    async def extend_token(self, short_lived: str, client: httpx.AsyncClient | None = None) -> TokenPair:
        """Exchange a short-lived token for a long-lived one (60 days)."""
        should_close = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=30)

        try:
            resp = await client.get(
                f"{self.GRAPH_URL}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self._app_id,
                    "client_secret": self._app_secret,
                    "fb_exchange_token": short_lived,
                },
            )
            data = resp.json()
            if resp.status_code != 200 or "error" in data:
                msg = data.get("error", {}).get("message", "Erro ao estender token")
                raise MetaAPIError(msg)

            expires_in = int(data.get("expires_in", 5184000))
            return TokenPair(
                access_token=data["access_token"],
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            )
        finally:
            if should_close:
                await client.aclose()

    async def refresh_if_needed(self, connection_id: str, supabase) -> str:
        """If token expires within 7 days, extend it. Returns decrypted token.

        If refresh fails, marks connection as is_valid=False.
        """
        row = (
            supabase.table("meta_connections")
            .select("access_token_encrypted, token_expires_at")
            .eq("id", connection_id)
            .single()
            .execute()
            .data
        )

        token = self.decrypt(row["access_token_encrypted"])
        expires_at = datetime.fromisoformat(row["token_expires_at"])

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        days_left = (expires_at - datetime.now(timezone.utc)).days

        if days_left > 7:
            return token

        try:
            pair = await self.extend_token(token)
            encrypted = self.encrypt(pair.access_token)
            supabase.table("meta_connections").update(
                {
                    "access_token_encrypted": encrypted,
                    "token_expires_at": pair.expires_at.isoformat(),
                    "atualizado_em": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", connection_id).execute()
            return pair.access_token
        except MetaAPIError:
            supabase.table("meta_connections").update({"is_valid": False}).eq("id", connection_id).execute()
            raise

    async def revoke(self, connection_id: str, supabase) -> None:
        """Revoke token on Meta and delete the connection."""
        row = (
            supabase.table("meta_connections")
            .select("access_token_encrypted")
            .eq("id", connection_id)
            .single()
            .execute()
            .data
        )
        token = self.decrypt(row["access_token_encrypted"])

        async with httpx.AsyncClient(timeout=30) as client:
            await client.delete(
                f"{self.GRAPH_URL}/me/permissions",
                params={"access_token": token},
            )

        supabase.table("meta_connections").delete().eq("id", connection_id).execute()
