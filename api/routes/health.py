"""Liveness and model state."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

from api.schemas import HealthResponse
from api.services import resolve_model, status_for
from api.settings import Settings

__all__ = ["router"]

router = APIRouter(prefix="/v1", tags=["service"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service liveness and model state",
    responses={
        200: {
            "description": (
                "The service is running. `status` is `degraded` when inference is "
                "unavailable, and `model` is null when no model is configured."
            )
        }
    },
)
def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    started_at: float = request.app.state.started_at
    resolved = resolve_model(settings)
    uptime = max(0.0, time.monotonic() - started_at)

    if resolved.spec is None:
        return HealthResponse(
            status="degraded",
            service=settings.service_name,
            version=settings.version,
            uptime_s=round(uptime, 3),
            model=None,
        )

    model_status = status_for(resolved.spec)
    return HealthResponse(
        status="ok" if model_status.available else "degraded",
        service=settings.service_name,
        version=settings.version,
        uptime_s=round(uptime, 3),
        model=model_status,
    )
