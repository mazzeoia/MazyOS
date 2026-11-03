from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes import actions, clients, google, health, meta, optimize, overview, whatsapp


settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(overview.router)
app.include_router(clients.router)
app.include_router(meta.router)
app.include_router(google.router)
app.include_router(whatsapp.router)
app.include_router(optimize.router)
app.include_router(actions.router)
