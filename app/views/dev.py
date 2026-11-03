"""Developer page — diagnostics, technical controls and recorded evaluation data.

Everything an administrator or developer needs that an end user does not: model
resolution, weights paths, runtime availability, setup instructions, dataset
composition, evaluation records and session statistics.

This route is hidden from navigation (`visibility="hidden"`), which hides a link —
it does **not** authorise anything. The page says so itself, and nothing in the
interface claims access control.
"""

from __future__ import annotations

import importlib.util
import platform

import pandas as pd
import streamlit as st

from app.components.settings import (
    reload_model_button,
    select_model,
)
from app.components.workflow import ERROR_STATE_KEY
from app.core import config
from app.core.errors import MetricsSchemaError
from app.core.metrics import METRIC_LABELS, load_metrics
from app.core.registry import ModelSpec
from app.core.runtime import get_detector
from app.core.stats import clear_runs, get_runs, runs_to_records, summarise
from app.ui.components import (
    bullets,
    empty_state,
    meta,
    note,
    page_header,
    readout,
    section,
)
from app.ui.theme import inject_theme

__all__ = ["render"]

_METRICS_SCHEMA_EXAMPLE = """{
  "model_id": "judah-face-v1",
  "model_name": "judah model v1",
  "split": "test",
  "evaluated_on": "2026-11-15",
  "source": "Evaluation on the held-out test split",
  "metrics": { "mAP50": 0.0, "mAP50_95": 0.0, "precision": 0.0, "recall": 0.0 }
}"""


def render() -> None:
    inject_theme()

    page_header(
        "Developer",
        "Diagnostics, model controls and recorded evaluation data. Not shown to end users.",
    )

    note(
        "This page is hidden from the navigation, not protected by it. Anyone with the "
        "URL can open it, so keep it off public deployments or restrict it at the hosting "
        "layer.",
        tone="warn",
    )

    spec, error = select_model()
    if error:
        st.error(f"**Model configuration problem**\n\n{error}")
        _render_setup_instructions(None)
        return
    if spec is None:
        empty_state(
            title="No model registered",
            body="Add an entry to config/models.json to enable detection.",
        )
        _render_setup_instructions(None)
        return

    _render_model(spec)
    _render_last_error()
    _render_runtime()
    _render_evaluation(spec)
    _render_dataset(spec)
    _render_session_activity()
    _render_setup_instructions(spec)


# --------------------------------------------------------------------------
# Model + runtime
# --------------------------------------------------------------------------
def _render_model(spec: ModelSpec) -> None:
    detector = get_detector(spec)
    info = detector.model_info()

    section("Model", "What the application resolved for this session.")
    readout(
        [
            ("Model id", spec.id),
            ("Task", spec.task),
            ("Kind", spec.kind.replace("_", " ")),
            ("General purpose", "yes" if spec.is_general_purpose else "no"),
            ("Weights", "present" if info["weights_present"] else "missing"),
        ]
    )
    meta(f"Weights path: {spec.weights_path}")
    meta(f"Labels source: {info['labels_source']}")
    meta(f"Class labels: {', '.join(info['labels']) if info['labels'] else 'unknown'}")

    meta(
        "Detector ready."
        if info["weights_present"]
        else "Detector unavailable. End users see the temporary-unavailable message."
    )

    reload_model_button()


def _render_runtime() -> None:
    section("Runtime", "Optional packages are only needed for inference.")
    rows = [("Python", platform.python_version())]
    for module in ("torch", "ultralytics"):
        if importlib.util.find_spec(module) is None:
            rows.append((module, "not installed"))
            continue
        try:
            loaded = importlib.import_module(module)
            rows.append((module, str(getattr(loaded, "__version__", "installed"))))
        except Exception as exc:  # noqa: BLE001 - diagnostics only
            rows.append((module, f"import failed: {type(exc).__name__}"))
    readout(rows)


def _render_last_error() -> None:
    section("Last analysis error", "Kept for diagnostics; end users never see this text.")
    record = st.session_state.get(ERROR_STATE_KEY)
    if not record:
        meta("No failed analysis in this session.")
        return
    readout(
        [
            ("When", record.get("at", "—")),
            ("Source", record.get("source", "—")),
            ("Type", "unavailable" if record.get("unavailable") else "failure"),
        ]
    )
    st.code(f"{record.get('title', '')}\n{record.get('message', '')}".strip(), language="text")


# --------------------------------------------------------------------------
# Recorded evaluation data (never estimated)
# --------------------------------------------------------------------------
def _render_evaluation(spec: ModelSpec) -> None:
    section("Evaluation", "Read verbatim from the recorded metrics file.")
    metrics_path = spec.metrics_file

    try:
        report = load_metrics(metrics_path)
    except MetricsSchemaError as exc:
        st.error(f"**The stored metrics record is invalid.**\n\n{exc}")
        _render_metrics_help(metrics_path)
        return

    if report is None:
        empty_state(
            title="No evaluation metrics recorded",
            body="Nothing is displayed rather than estimating performance.",
        )
        _render_metrics_help(metrics_path)
        return

    items = report.display_items()
    if items:
        for column, (label, value) in zip(st.columns(len(items), gap="small"), items):
            column.metric(label, f"{value:.4f}")
    for label, value in report.extra_items():
        meta(f"{label}: {value:.4f}")

    meta(
        f"model {report.model_id} · split {report.split or 'not stated'} · "
        f"evaluated {report.evaluated_on or 'not stated'} · "
        f"source: {report.source or 'not stated'}"
    )
    if report.per_class:
        st.dataframe(
            pd.DataFrame(
                [
                    {"class": name, **{METRIC_LABELS.get(k, k): v for k, v in values.items()}}
                    for name, values in report.per_class.items()
                ]
            ),
            hide_index=True,
            width="stretch",
        )
    if report.notes:
        meta(f"Notes: {report.notes}")

    for relative in report.curves or ():
        base = metrics_path.parent if metrics_path else config.get_metrics_dir()
        candidate = (base / relative).resolve()
        if candidate.is_file():
            st.image(str(candidate), caption=relative, width="content")


def _render_metrics_help(metrics_path) -> None:
    with st.expander("Metrics file format", expanded=False):
        st.markdown(
            f"""
Metrics are read from `{metrics_path}`. Copy values from a real evaluation run;
never estimate them.

```json
{_METRICS_SCHEMA_EXAMPLE}
```

`model_id` and `metrics` are required; every metric is a ratio in `[0, 1]`. Missing
metrics stay missing.
"""
        )


# --------------------------------------------------------------------------
# Dataset
# --------------------------------------------------------------------------
def _render_dataset(spec: ModelSpec) -> None:
    dataset = spec.dataset
    if not dataset:
        return

    section("Dataset", "Declared composition of the training data.")
    split = dataset.get("split") or {}
    readout(
        [
            ("Images", str(dataset.get("total_images", "—"))),
            ("Annotated", str(dataset.get("annotated_images", "—"))),
            ("Reserved", str(dataset.get("unannotated_reserved", "—"))),
            (
                "Train / Val / Test",
                f"{split.get('train', '—')} / {split.get('val', '—')} / {split.get('test', '—')}",
            ),
        ]
    )

    total, parts = dataset.get("total_images"), [
        split.get("train"),
        split.get("val"),
        split.get("test"),
    ]
    annotated = dataset.get("annotated_images")
    if total and all(isinstance(part, int) for part in parts):
        split_total = sum(parts)  # type: ignore[arg-type]
        if isinstance(annotated, int) and split_total > annotated:
            note(
                f"The declared split covers {split_total} images while {annotated} are "
                f"annotated, so up to {split_total - annotated} split images may have no "
                "label file. Verify before treating metrics as authoritative.",
                tone="warn",
            )

    if spec.provenance:
        section("Provenance")
        bullets([f"{key.replace('_', ' ')}: {value}" for key, value in spec.provenance.items()])


# --------------------------------------------------------------------------
# Session activity
# --------------------------------------------------------------------------
def _render_session_activity() -> None:
    section("Session activity", "Inference actually run in this browser session.")

    runs = get_runs(st.session_state)
    if not runs:
        empty_state(
            title="No runs in this session",
            body="Run an analysis on Detect or Camera to populate this table.",
        )
        return

    summary = summarise(runs)
    for column, (label, value) in zip(
        st.columns(4, gap="small"),
        [
            ("Runs", str(summary.total_runs)),
            ("Total detections", str(summary.total_faces)),
            ("Mean per image", f"{summary.mean_faces_per_image:.2f}"),
            (
                "Mean confidence",
                f"{summary.mean_confidence:.1%}" if summary.mean_confidence is not None else "—",
            ),
        ],
    ):
        column.metric(label, value)

    st.dataframe(runs_to_records(runs), hide_index=True, width="stretch")
    meta(
        f"Zero-detection runs: {summary.empty_runs} · by source: {summary.by_source} · "
        f"mean inference: "
        f"{f'{summary.mean_inference_ms:.0f} ms' if summary.mean_inference_ms else '—'}"
    )

    if st.button("Clear session activity"):
        clear_runs(st.session_state)
        st.rerun()


# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------
def _render_setup_instructions(spec: ModelSpec | None) -> None:
    with st.expander("Connect weights", expanded=False):
        weights_path = spec.weights_path if spec else config.DEFAULT_MODELS_DIR / "judah-face-v1/best.pt"
        st.markdown(
            f"""
Place trained Ultralytics weights at `{weights_path}`, or point the app at an
existing file:

```bash
export JUDETECTOR_MODEL_PATH=/absolute/path/to/best.pt
```

Then install the optional runtime and reload:

```bash
pip install -r requirements-model.txt
```

Weights are git-ignored and never shipped with the application. Full details are in
`docs/MODEL_INTEGRATION.md`.
"""
        )
