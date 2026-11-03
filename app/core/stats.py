"""Session detection statistics.

Pure functions over a plain mapping (Streamlit's `session_state` is dict-like),
so the arithmetic is unit-testable without a running Streamlit server.

These statistics describe *this session's actual inference runs* only. They are
never presented as model evaluation metrics.
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core import config

__all__ = [
    "DetectionRun",
    "RunSummary",
    "STATE_KEY",
    "record_run",
    "record_run_once",
    "get_runs",
    "clear_runs",
    "summarise",
    "runs_to_records",
]

STATE_KEY = "detection_runs"
_SIGNATURE_KEY = "detection_runs_last_signature"


@dataclass(frozen=True)
class DetectionRun:
    """One inference pass performed in this session."""

    source: str
    filename: str
    model_id: str
    face_count: int
    image_width: int
    image_height: int
    confidence_threshold: float
    iou_threshold: float
    mean_confidence: float | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None
    inference_ms: float | None = None
    labels: tuple[str, ...] = ()
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["labels"] = list(self.labels)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DetectionRun:
        known = {f for f in cls.__dataclass_fields__ if f != "labels"}
        data = {key: payload[key] for key in known if key in payload}
        data["labels"] = tuple(payload.get("labels") or ())
        data.setdefault("source", "unknown")
        data.setdefault("filename", "")
        data.setdefault("model_id", "")
        data.setdefault("face_count", 0)
        data.setdefault("image_width", 0)
        data.setdefault("image_height", 0)
        data.setdefault("confidence_threshold", 0.0)
        data.setdefault("iou_threshold", 0.0)
        return cls(**data)


@dataclass(frozen=True)
class RunSummary:
    total_runs: int = 0
    total_faces: int = 0
    mean_faces_per_image: float = 0.0
    mean_confidence: float | None = None
    max_faces_single_image: int = 0
    empty_runs: int = 0
    mean_inference_ms: float | None = None
    by_source: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _state_list(state: MutableMapping[str, Any]) -> list[dict[str, Any]]:
    runs = state.get(STATE_KEY)
    if not isinstance(runs, list):
        runs = []
        state[STATE_KEY] = runs
    return runs


def record_run(state: MutableMapping[str, Any], run: DetectionRun) -> None:
    """Append a run, trimming the oldest entries beyond the configured cap."""
    runs = _state_list(state)
    runs.append(run.to_dict())
    overflow = len(runs) - config.MAX_RECORDED_RUNS
    if overflow > 0:
        del runs[:overflow]


def record_run_once(
    state: MutableMapping[str, Any], run: DetectionRun, signature: tuple[Any, ...]
) -> bool:
    """Record a run only if `signature` differs from the last recorded one.

    Streamlit re-runs the whole script on every widget interaction; without this
    guard, nudging a slider would inflate the statistics with duplicates.
    Returns True when the run was recorded.
    """
    if state.get(_SIGNATURE_KEY) == signature:
        return False
    state[_SIGNATURE_KEY] = signature
    record_run(state, run)
    return True


def get_runs(state: MutableMapping[str, Any]) -> list[DetectionRun]:
    return [DetectionRun.from_dict(item) for item in _state_list(state)]


def clear_runs(state: MutableMapping[str, Any]) -> None:
    state[STATE_KEY] = []
    state.pop(_SIGNATURE_KEY, None)


def summarise(runs: Sequence[DetectionRun]) -> RunSummary:
    """Aggregate runs. Confidence means are averaged over *detections*, weighted
    by face count, so a 1-face and a 5-face image are not equally weighted."""
    if not runs:
        return RunSummary()

    total_faces = sum(max(0, run.face_count) for run in runs)
    confidence_weight = 0
    confidence_total = 0.0
    for run in runs:
        if run.mean_confidence is not None and run.face_count > 0:
            confidence_total += run.mean_confidence * run.face_count
            confidence_weight += run.face_count

    inference_values = [r.inference_ms for r in runs if r.inference_ms is not None]
    by_source: dict[str, int] = {}
    for run in runs:
        by_source[run.source] = by_source.get(run.source, 0) + 1

    return RunSummary(
        total_runs=len(runs),
        total_faces=total_faces,
        mean_faces_per_image=(total_faces / len(runs)) if runs else 0.0,
        mean_confidence=(confidence_total / confidence_weight) if confidence_weight else None,
        max_faces_single_image=max((run.face_count for run in runs), default=0),
        empty_runs=sum(1 for run in runs if run.face_count == 0),
        mean_inference_ms=(
            sum(inference_values) / len(inference_values) if inference_values else None
        ),
        by_source=by_source,
    )


def runs_to_records(runs: Sequence[DetectionRun]) -> list[dict[str, Any]]:
    """Display-ready rows, newest last, with a short timestamp."""
    records: list[dict[str, Any]] = []
    for run in runs:
        stamp = run.timestamp.replace("T", " ")
        records.append(
            {
                "time (UTC)": stamp[:19],
                "source": run.source,
                "file": run.filename,
                "model": run.model_id,
                "detections": run.face_count,
                "mean conf": (
                    round(run.mean_confidence, 3) if run.mean_confidence is not None else None
                ),
                "labels": ", ".join(run.labels) if run.labels else "",
                "conf ≥": round(run.confidence_threshold, 2),
                "ms": round(run.inference_ms, 1) if run.inference_ms is not None else None,
            }
        )
    return records
