"""HTTP routes, mounted under `/v1`."""

from __future__ import annotations

from api.routes import detect, health, model

__all__ = ["detect", "health", "model"]
