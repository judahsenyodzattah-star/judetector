"""Response contracts for the inference API.

These pydantic models are the published contract: they generate the OpenAPI
document, they are what the Next.js and Expo clients are generated from, and
they are what the contract tests assert against. Additive changes only within
`/v1`.
"""

from __future__ import annotations

from api.schemas.detect import (
    AnnotatedImage,
    Box,
    DetectionOut,
    DetectResponse,
    ImageInfo,
    ModelRef,
    Thresholds,
    Timing,
)
from api.schemas.errors import Problem
from api.schemas.health import HealthResponse, ModelStatus
from api.schemas.model import ModelCard

__all__ = [
    "AnnotatedImage",
    "Box",
    "DetectResponse",
    "DetectionOut",
    "HealthResponse",
    "ImageInfo",
    "ModelCard",
    "ModelRef",
    "ModelStatus",
    "Problem",
    "Thresholds",
    "Timing",
]
