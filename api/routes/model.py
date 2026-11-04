"""The public model card."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.errors import ProblemError
from api.schemas import ModelCard, Problem
from api.services import card_for, resolve_model
from api.settings import Settings

__all__ = ["router"]

router = APIRouter(prefix="/v1", tags=["service"])


@router.get(
    "/model",
    response_model=ModelCard,
    summary="Describe the active model",
    responses={
        503: {
            "model": Problem,
            "description": "No usable model is configured for this service.",
            "content": {"application/problem+json": {}},
        }
    },
)
def model(request: Request) -> ModelCard:
    settings: Settings = request.app.state.settings
    resolved = resolve_model(settings)
    if resolved.spec is None:
        raise ProblemError(
            status=503,
            type_="model_unavailable",
            title="No model is available",
            detail="This service has no usable model configured. Try again later.",
        )
    return card_for(resolved.spec)
