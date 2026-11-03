from __future__ import annotations

from dataclasses import dataclass

import httpx
from fastapi import Header, HTTPException, status

from .config import get_settings


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None = None


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login obrigatorio.")

    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise HTTPException(status_code=500, detail="Supabase nao configurado.")

    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={
                "apikey": settings.supabase_publishable_key,
                "Authorization": f"Bearer {token}",
            },
        )

    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessao invalida.")

    data = response.json()
    user_id = data.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessao invalida.")

    return CurrentUser(id=user_id, email=data.get("email"))
