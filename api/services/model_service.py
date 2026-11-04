"""Model resolution and public presentation.

The API never guesses: it asks the registry which model is active, asks the
engine whether that model's weights exist, and reports exactly that. Failure
reasons are logged for operators and never returned to clients — a problem
document says "no model is available", not where a file should have been.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from api.runtime import get_detector, get_registry
from api.schemas import ModelCard, ModelStatus
from api.settings import Settings
from app.core.detector import Detector
from app.core.errors import MetricsSchemaError, RegistryError
from app.core.metrics import load_metrics
from app.core.registry import ModelSpec

__all__ = [
    "ResolvedModel",
    "card_for",
    "detector_for",
    "limitations_for",
    "metrics_for",
    "resolve_model",
    "status_for",
]

logger = logging.getLogger("judetector.api")


@dataclass(frozen=True)
class ResolvedModel:
    """The active spec, or None with an internal-only reason."""

    spec: ModelSpec | None
    reason: str | None = None


def resolve_model(settings: Settings) -> ResolvedModel:
    """Resolve the registry default without loading any weights."""
    path = str(settings.registry_path) if settings.registry_path else None
    try:
        return ResolvedModel(get_registry(path).default())
    except RegistryError as exc:
        logger.warning("Model registry unavailable: %s", exc)
        return ResolvedModel(None, "registry_unavailable")
    except Exception:  # noqa: BLE001 - a broken registry must not take the service down
        logger.exception("Unexpected failure while resolving the model registry")
        return ResolvedModel(None, "registry_error")


def detector_for(spec: ModelSpec) -> Detector:
    return get_detector(spec)


def status_for(spec: ModelSpec) -> ModelStatus:
    detector = detector_for(spec)
    return ModelStatus(
        id=spec.id,
        available=detector.is_available(),
        loaded=detector.is_ready(),
    )


def limitations_for(spec: ModelSpec) -> str:
    """A plain statement of what this model is not, derived from the registry."""
    if spec.is_subject_specific:
        return (
            "Single-subject detector trained on one person. It is not a validated "
            "general-purpose face detector and cannot identify anyone. Do not use it "
            "for surveillance or access decisions. Detection is not recognition."
        )
    return (
        "General-purpose detector. Accuracy depends on the training data and conditions. "
        "It does not identify individuals and must not be used for surveillance or access "
        "decisions. Detection is not recognition."
    )


def metrics_for(spec: ModelSpec) -> dict[str, Any] | None:
    """The recorded evaluation record, verbatim, or None. Never an estimate."""
    try:
        report = load_metrics(spec.metrics_file)
    except MetricsSchemaError as exc:
        logger.warning("Recorded metrics are invalid and were withheld: %s", exc)
        return None
    if report is None:
        return None
    return {
        "model_id": report.model_id,
        "model_name": report.model_name,
        "split": report.split,
        "evaluated_on": report.evaluated_on,
        "source": report.source,
        "metrics": dict(report.metrics),
        "per_class": report.per_class,
        "notes": report.notes,
    }


def card_for(spec: ModelSpec) -> ModelCard:
    detector = detector_for(spec)
    return ModelCard(
        id=spec.id,
        display_name=spec.display_name,
        kind=spec.kind,
        task=spec.task,
        labels=list(detector.labels),
        labels_source=detector.labels_source,
        available=detector.is_available(),
        limitations=limitations_for(spec),
        metrics=metrics_for(spec),
    )
