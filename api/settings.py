"""Environment-driven service settings.

Plain dataclass rather than pydantic-settings: the API has a handful of knobs and
no nested configuration, so one extra dependency would buy very little.

Every value can be supplied by the environment so the same image runs locally,
in CI and on Cloud Run without edits:

    JUDETECTOR_ENV             development | staging | production
    JUDETECTOR_REGISTRY        path to models.json
    JUDETECTOR_CORS_ORIGINS    comma-separated allowlist
    JUDETECTOR_MAX_UPLOAD_MB   upload cap in megabytes
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.core import config

__all__ = ["Settings"]


def _csv(name: str) -> tuple[str, ...]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class Settings:
    """Immutable service configuration."""

    service_name: str = "judetector-api"
    version: str = "0.1.0"
    environment: str = "development"
    registry_path: Path | None = None
    docs_enabled: bool = True
    allowed_origins: tuple[str, ...] = ()
    max_upload_mb: int = config.MAX_UPLOAD_MB
    max_image_dimension: int = config.MAX_IMAGE_DIMENSION

    def __post_init__(self) -> None:
        # Interactive docs are a development affordance. Production never gets
        # them, however the settings object was constructed.
        if self.environment == "production" and self.docs_enabled:
            object.__setattr__(self, "docs_enabled", False)

    @classmethod
    def from_env(cls) -> Settings:
        environment = os.environ.get("JUDETECTOR_ENV", "development").strip().lower() or "development"
        registry = os.environ.get("JUDETECTOR_REGISTRY", "").strip()
        return cls(
            environment=environment,
            registry_path=Path(registry) if registry else None,
            docs_enabled=environment != "production",
            allowed_origins=_csv("JUDETECTOR_CORS_ORIGINS"),
            max_upload_mb=_int_env("JUDETECTOR_MAX_UPLOAD_MB", config.MAX_UPLOAD_MB),
            max_image_dimension=_int_env(
                "JUDETECTOR_MAX_IMAGE_DIMENSION", config.MAX_IMAGE_DIMENSION
            ),
        )
