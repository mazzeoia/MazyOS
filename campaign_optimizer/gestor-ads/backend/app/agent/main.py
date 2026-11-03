# app/agent/main.py
from __future__ import annotations

import logging

from fastapi import FastAPI

from app.agent.router import router as agent_router
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="Gestor Ads — Agente Conversacional", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(agent_router)
