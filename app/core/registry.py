"""Model registry: the configurable list of available detectors.

Adding a new model is a configuration edit (`config/models.json`), not a code
change. That is what lets a subject-specific `judah` model be replaced later by
a genuine general-purpose face detector.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from app.core import config
from app.core.detector import Detector, UltralyticsDetector
from app.core.errors import RegistryError

__all__ = ["ModelSpec", "ModelRegistry", "load_registry"]


@dataclass(frozen=True)
class ModelSpec:
    """Declarative description of one registerable model."""

    id: str
    display_name: str
    weights_path: Path
    kind: str = "unknown"
    is_general_purpose: bool = False
    enabled: bool = True
    task: str = "detect"
    declared_labels: tuple[str, ...] = ()
    description: str = ""
    metrics_file: Path | None = None
    dataset: dict[str, Any] | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    # -- derived facts -----------------------------------------------------
    @property
    def weights_present(self) -> bool:
        return self.weights_path.is_file()

    @property
    def is_subject_specific(self) -> bool:
        return self.kind == "subject_specific" or not self.is_general_purpose

    def weight_status_label(self) -> str:
        return "weights found" if self.weights_present else "weights missing"

    # -- construction ------------------------------------------------------
    @classmethod
    def from_dict(
        cls, payload: dict[str, Any], *, project_root: Path | None = None
    ) -> ModelSpec:
        if not isinstance(payload, dict):
            raise RegistryError("Each model entry must be a JSON object.")
        model_id = str(payload.get("id", "")).strip()
        if not model_id:
            raise RegistryError("Every model entry requires a non-empty 'id'.")
        weights = payload.get("weights")
        if not weights:
            raise RegistryError(f"Model '{model_id}' is missing 'weights'.")

        metrics_file = payload.get("metrics_file")
        labels = payload.get("declared_labels") or []
        if not isinstance(labels, (list, tuple)):
            raise RegistryError(f"Model '{model_id}': 'declared_labels' must be a list.")

        return cls(
            id=model_id,
            display_name=str(payload.get("display_name") or model_id),
            weights_path=config.resolve_path(weights, base=project_root),
            kind=str(payload.get("kind", "unknown")),
            is_general_purpose=bool(payload.get("is_general_purpose", False)),
            enabled=bool(payload.get("enabled", True)),
            task=str(payload.get("task", "detect")),
            declared_labels=tuple(str(label) for label in labels),
            description=str(payload.get("description", "")),
            metrics_file=(
                config.resolve_path(metrics_file, base=project_root)
                if metrics_file
                else None
            ),
            dataset=payload.get("dataset"),
            provenance=payload.get("provenance") or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "weights": str(self.weights_path),
            "kind": self.kind,
            "is_general_purpose": self.is_general_purpose,
            "enabled": self.enabled,
            "task": self.task,
            "declared_labels": list(self.declared_labels),
            "description": self.description,
            "metrics_file": str(self.metrics_file) if self.metrics_file else None,
            "dataset": self.dataset,
            "provenance": self.provenance,
        }


@dataclass
class ModelRegistry:
    """Container of `ModelSpec` objects, loadable from JSON."""

    specs: tuple[ModelSpec, ...]
    default_model_id: str

    # -- lookup ------------------------------------------------------------
    def enabled(self) -> tuple[ModelSpec, ...]:
        return tuple(spec for spec in self.specs if spec.enabled)

    def get(self, model_id: str) -> ModelSpec:
        for spec in self.specs:
            if spec.id == model_id:
                return spec
        raise RegistryError(f"Unknown model id '{model_id}'.")

    def default(self) -> ModelSpec:
        try:
            return self.get(self.default_model_id)
        except RegistryError:
            enabled = self.enabled()
            if not enabled:
                raise RegistryError(
                    "No enabled models are registered. Check config/models.json."
                ) from None
            return enabled[0]

    # -- construction ------------------------------------------------------
    @classmethod
    def from_dict(
        cls, payload: dict[str, Any], *, project_root: Path | None = None
    ) -> ModelRegistry:
        if not isinstance(payload, dict):
            raise RegistryError("Model registry must be a JSON object.")
        raw_models = payload.get("models")
        if not isinstance(raw_models, list) or not raw_models:
            raise RegistryError("Registry must contain a non-empty 'models' list.")

        specs: list[ModelSpec] = []
        seen: set[str] = set()
        for entry in raw_models:
            spec = ModelSpec.from_dict(entry, project_root=project_root)
            if spec.id in seen:
                raise RegistryError(f"Duplicate model id '{spec.id}' in registry.")
            seen.add(spec.id)
            specs.append(spec)

        default_id = str(payload.get("default_model_id") or specs[0].id)
        return cls(specs=tuple(specs), default_model_id=default_id)

    @classmethod
    def load(
        cls, path: str | Path | None = None, *, project_root: Path | None = None
    ) -> ModelRegistry:
        registry_path = Path(path) if path else config.get_registry_path()
        if not registry_path.is_file():
            raise RegistryError(
                f"Model registry not found at '{registry_path}'. "
                "Restore config/models.json or set JUDETECTOR_REGISTRY."
            )
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RegistryError(f"Invalid JSON in registry '{registry_path}': {exc}") from exc

        registry = cls.from_dict(payload, project_root=project_root)
        return _apply_weights_override(registry)


def _apply_weights_override(registry: ModelRegistry) -> ModelRegistry:
    """Honour JUDETECTOR_MODEL_PATH for the default model, if set."""
    override = config.get_model_path_override()
    if override is None:
        return registry
    default_id = registry.default().id
    patched = tuple(
        replace(spec, weights_path=override) if spec.id == default_id else spec
        for spec in registry.specs
    )
    return ModelRegistry(specs=patched, default_model_id=registry.default_model_id)


def load_registry(path: str | Path | None = None) -> ModelRegistry:
    """Convenience wrapper used by the application."""
    return ModelRegistry.load(path)


def build_detector(spec: ModelSpec, *, model_loader: Any | None = None) -> Detector:
    """Create the appropriate `Detector` for a spec.

    Kept as a factory so additional backends (ONNX Runtime, RT-DETR, a hosted
    API) can be added here later without touching the views.
    """
    return UltralyticsDetector(
        model_id=spec.id,
        weights_path=spec.weights_path,
        display_name=spec.display_name,
        declared_labels=spec.declared_labels,
        is_general_purpose=spec.is_general_purpose,
        model_loader=model_loader,
    )


def iter_specs(registry: ModelRegistry, *, include_disabled: bool = False) -> Iterable[ModelSpec]:
    return registry.specs if include_disabled else registry.enabled()
