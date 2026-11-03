from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent.dashboard_router import router as agent_dashboard_router
from app.analysis.router import router as analysis_router
from app.auth.router import router as auth_router
from app.automation.router import router as automation_router
from app.campaigns.router import router as campaigns_router
from app.config import get_settings
from app.events.router import router as events_router
from app.shared.exceptions import AppError

settings = get_settings()

logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="Gestor Ads API",
    description="Backend unificado — Campaign Optimizer + Gestor de Tráfego",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "meta": exc.meta,
        },
    )


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Mount routers
app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(analysis_router)
app.include_router(automation_router)
app.include_router(events_router)
app.include_router(agent_dashboard_router)
