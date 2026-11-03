"""Evaluation-metrics loading.

Hard rule: this module never computes, estimates, infers or fills in a metric.
It either returns exactly what an evaluation record says, or `None` when no
record exists, or raises when the record is malformed. The Dashboard therefore
cannot display a number that did not come from a real evaluation run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.errors import MetricsSchemaError

__all__ = [
    "MetricsReport",
    "load_metrics",
    "validate_payload",
    "METRIC_LABELS",
    "CANONICAL_METRIC_KEYS",
]

# Canonical metric keys, with accepted aliases (Ultralytics exports use both
# underscore and dash spellings, often suffixed with "(B)" for box metrics).
_ALIASES: dict[str, str] = {
    "map50": "mAP50",
    "mAP50": "mAP50",
    "mAP50(B)": "mAP50",
    "map50-95": "mAP50_95",
    "map50_95": "mAP50_95",
    "mAP50-95": "mAP50_95",
    "mAP50_95": "mAP50_95",
    "mAP50-95(B)": "mAP50_95",
    "precision": "precision",
    "precision(B)": "precision",
    "recall": "recall",
    "recall(B)": "recall",
    "f1": "f1",
    "f1_score": "f1",
}

CANONICAL_METRIC_KEYS: tuple[str, ...] = ("mAP50", "mAP50_95", "precision", "recall", "f1")

METRIC_LABELS: dict[str, str] = {
    "mAP50": "mAP@0.5",
    "mAP50_95": "mAP@0.5:0.95",
    "precision": "Precision",
    "recall": "Recall",
    "f1": "F1-score",
}

REQUIRED_TOP_LEVEL: tuple[str, ...] = ("model_id", "metrics")


@dataclass(frozen=True)
class MetricsReport:
    """A validated evaluation record."""

    model_id: str
    metrics: dict[str, float]
    model_name: str | None = None
    split: str | None = None
    evaluated_on: str | None = None
    source: str | None = None
    per_class: dict[str, dict[str, float]] | None = None
    dataset: dict[str, Any] | None = None
    notes: str | None = None
    curves: tuple[str, ...] = ()
    raw: dict[str, Any] | None = None

    def get(self, key: str) -> float | None:
        """Value for a canonical metric key, or None if it was not recorded."""
        return self.metrics.get(key)

    def display_items(self) -> list[tuple[str, float]]:
        """Only metrics that actually exist, in canonical order."""
        return [
            (METRIC_LABELS.get(key, key), self.metrics[key])
            for key in CANONICAL_METRIC_KEYS
            if key in self.metrics
        ]

    def extra_items(self) -> list[tuple[str, float]]:
        """Recorded metrics outside the canonical set (shown, never hidden)."""
        return [
            (key, value)
            for key, value in self.metrics.items()
            if key not in CANONICAL_METRIC_KEYS
        ]


def _canonical_metrics(payload: dict[str, Any]) -> dict[str, float]:
    """Map accepted metric keys to canonical names, converting values strictly."""
    canonical: dict[str, float] = {}
    for key, value in payload.items():
        target = _ALIASES.get(key) or _ALIASES.get(str(key).strip()) or _ALIASES.get(
            str(key).replace("metrics/", "")
        )
        if target is None:
            # Unrecognised but numeric metrics are preserved under their own name
            # rather than silently dropped or coerced.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            if value != value:  # NaN
                raise MetricsSchemaError(f"Metric '{key}' is NaN.")
            canonical[str(key)] = float(value)
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MetricsSchemaError(
                f"Metric '{key}' must be a number, got {type(value).__name__}."
            )
        numeric = float(value)
        if numeric != numeric:  # NaN guard
            raise MetricsSchemaError(f"Metric '{key}' is NaN.")
        if not 0.0 <= numeric <= 1.0:
            raise MetricsSchemaError(
                f"Metric '{key}' = {numeric} is outside the expected [0, 1] range. "
                "Record ratios (0-1), not percentages -- or fix the export."
            )
        canonical[target] = numeric
    return canonical


def validate_payload(payload: Any) -> list[str]:
    """Return a list of human-readable problems (empty list == valid)."""
    if not isinstance(payload, dict):
        return ["Metrics record must be a JSON object."]
    problems: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in payload:
            problems.append(f"Missing required key '{key}'.")
    if "model_id" in payload and not str(payload.get("model_id", "")).strip():
        problems.append("'model_id' must be a non-empty string.")
    metrics = payload.get("metrics")
    if "metrics" in payload:
        if not isinstance(metrics, dict):
            problems.append("'metrics' must be an object of metric name -> number.")
        elif not metrics:
            problems.append("'metrics' is empty; nothing to report.")
        else:
            try:
                _canonical_metrics(metrics)
            except MetricsSchemaError as exc:
                problems.append(str(exc))
    curves = payload.get("curves")
    if curves is not None and not isinstance(curves, list):
        problems.append("'curves' must be a list of file paths when provided.")
    return problems


def load_metrics(path: str | Path | None) -> MetricsReport | None:
    """Load and validate an evaluation record.

    Returns ``None`` when no record exists. Raises :class:`MetricsSchemaError`
    when a record exists but is unusable -- a broken record is surfaced, never
    silently replaced with placeholder numbers.
    """
    if path is None:
        return None
    metrics_path = Path(path)
    if not metrics_path.is_file():
        return None

    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MetricsSchemaError(f"Invalid JSON in '{metrics_path}': {exc}") from exc

    problems = validate_payload(payload)
    if problems:
        raise MetricsSchemaError(
            f"Metrics record '{metrics_path}' is invalid: " + " ".join(problems)
        )

    per_class_raw = payload.get("per_class") or None
    per_class: dict[str, dict[str, float]] | None = None
    if isinstance(per_class_raw, dict):
        per_class = {}
        for class_name, values in per_class_raw.items():
            if isinstance(values, dict):
                per_class[str(class_name)] = _canonical_metrics(values)

    curves_raw = payload.get("curves") or []
    curves = tuple(str(item) for item in curves_raw) if isinstance(curves_raw, list) else ()

    return MetricsReport(
        model_id=str(payload["model_id"]),
        metrics=_canonical_metrics(payload["metrics"]),
        model_name=payload.get("model_name"),
        split=payload.get("split"),
        evaluated_on=payload.get("evaluated_on"),
        source=payload.get("source"),
        per_class=per_class,
        dataset=payload.get("dataset"),
        notes=payload.get("notes"),
        curves=curves,
        raw=payload,
    )
