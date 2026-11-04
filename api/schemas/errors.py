"""The single error contract (RFC 9457 problem details)."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["Problem", "PROBLEM_MEDIA_TYPE"]

PROBLEM_MEDIA_TYPE = "application/problem+json"


class Problem(BaseModel):
    """A problem document. Never contains paths, internals or stack traces."""

    type: str = Field(description='Stable, machine-readable code, e.g. "invalid_image".')
    title: str
    status: int
    detail: str
    request_id: str
