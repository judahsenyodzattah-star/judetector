"""HTTP routes, mounted under `/v1`."""

from __future__ import annotations

from api.routes import health, model

__all__ = ["health", "model"]
