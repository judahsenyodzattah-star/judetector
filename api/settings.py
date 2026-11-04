"""Environment-driven service settings.

Plain dataclass rather than pydantic-settings: the API has a handful of knobs and
no nested configuration, so one extra dependency would buy very little.

Every value can be supplied by the environment so the same image runs locally,
in CI and on Cloud Run without edits:

    JUDETECTOR_ENV             development | staging | production
    JUDETECTOR_REGISTRY        path to models.json
    JUDETECTOR_CORS_ORIGINS    comma-separated allowlist
    JUDETECTOR_MAX_UPLOAD_MB   upload cap in megabytes
    JUDETECTOR_MAX_PIXELS      decoded pixel budget per image
    JUDETECTOR_MAX_ANNOTATED_MB  cap for the inline annotated PNG
    JUDETECTOR_RATE_LIMIT_PER_MINUTE  per-instance requests per minute
    JUDETECTOR_RATE_LIMIT_BACKEND     memory (per instance) | none
    JUDETECTOR_TRUST_PROXY     honour the first X-Forwarded-For entry
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


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


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
    max_pixels: int = 40_000_000
    max_annotated_bytes: int = 6 * 1024 * 1024
    rate_limit_per_minute: int = 30
    rate_limit_backend: str = "memory"
    trust_proxy: bool = False

    #: Multipart overhead allowed on top of the file cap before the body guard
    #: rejects a request without reading it.
    multipart_overhead_bytes: int = 256 * 1024

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def max_request_bytes(self) -> int:
        return self.max_upload_bytes + self.multipart_overhead_bytes

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
            max_pixels=_int_env("JUDETECTOR_MAX_PIXELS", 40_000_000),
            max_annotated_bytes=_int_env(
                "JUDETECTOR_MAX_ANNOTATED_MB", 6
            )
            * 1024
            * 1024,
            rate_limit_per_minute=_int_env("JUDETECTOR_RATE_LIMIT_PER_MINUTE", 30),
            rate_limit_backend=(os.environ.get("JUDETECTOR_RATE_LIMIT_BACKEND", "memory").strip() or "memory"),
            trust_proxy=_bool_env("JUDETECTOR_TRUST_PROXY", False),
        )
