"""Health contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

__all__ = ["HealthResponse", "ModelStatus"]


class ModelStatus(BaseModel):
    """Whether the configured model can be used right now."""

    id: str = Field(description="Registered model id, safe for public display.")
    available: bool = Field(description="Weights exist on disk.")
    loaded: bool = Field(description="The model is loaded in this process and can predict.")


class HealthResponse(BaseModel):
    """Liveness plus honest model state.

    `status` is `ok` only when the service can actually analyse an image;
    `degraded` means the service is up but inference is unavailable, and the
    client must show its unavailable state instead of inventing results.
    """

    status: Literal["ok", "degraded"]
    service: str
    version: str
    uptime_s: float = Field(ge=0.0)
    model: ModelStatus | None = None
