"""Analytics: recorded evaluation results and session activity.

Three kinds of number, kept visually and semantically separate:

1. **Evaluation metrics** — read verbatim from a recorded evaluation run. If no
   record exists, the section stays empty. Nothing is estimated.
2. **Session activity** — computed from detections actually run in this session.
3. **Model and dataset details** — declared configuration, tucked into an
   expander so developer-oriented detail stays out of the primary view.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.model_sidebar import current_model
from app.core import config
from app.core.errors import MetricsSchemaError
from app.core.metrics import METRIC_LABELS, load_metrics
from app.core.registry import ModelSpec
from app.core.runtime import get_detector
from app.core.stats import clear_runs, get_runs, runs_to_records, summarise
from app.ui.components import (
    bullets,
    empty_state,
    kv_row,
    meta,
    note,
    page_header,
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

    spec, model_error = current_model()
    connected = bool(spec is not None and spec.weights_present)

    page_header(
        "Analytics",
        "Recorded evaluation results for the connected model, and this session's "
        "detection activity.",
        eyebrow="Insights",
        status=("Model connected", "ok") if connected else ("Model not connected", "warn"),
    )

    if model_error:
        st.error(f"Model configuration problem: {model_error}")
        return
    if spec is None:
        empty_state(
            icon="cpu",
            title="No model configured",
            body="Register a detector in config/models.json to populate analytics.",
        )
        return

    _render_evaluation(spec)
    _render_session_activity()
    _render_technical_details(spec)


# --------------------------------------------------------------------------
# Evaluation results
# --------------------------------------------------------------------------
def _render_evaluation(spec: ModelSpec) -> None:
    section("Evaluation", "Measured performance of the connected model, as recorded.")

    metrics_path = spec.metrics_file
    try:
        report = load_metrics(metrics_path)
    except MetricsSchemaError as exc:
        st.error(f"**The stored metrics record is invalid.**\n\n{exc}")
        return

    if report is None:
        empty_state(
            icon="chart",
            title="No evaluation metrics recorded",
            body="This model has no recorded evaluation run yet, so no performance "
            "figures are shown.",
        )
        _render_metrics_help(metrics_path)
        return

    items = report.display_items()
    if items:
        columns = st.columns(len(items), gap="small")
        for column, (label, value) in zip(columns, items):
            column.metric(label, f"{value:.4f}")

    for label, value in report.extra_items():
        meta(f"{label}: {value:.4f}")
    if not items:
        meta("The record contains no recognised metric values.")

    meta(
        f"model {report.model_id} · split {report.split or 'not stated'} · "
        f"evaluated {report.evaluated_on or 'not stated'} · "
        f"source: {report.source or 'not stated'}"
    )

    if report.per_class:
        st.markdown("**Per class**")
        st.dataframe(
            [
                {"class": name, **{METRIC_LABELS.get(k, k): v for k, v in values.items()}}
                for name, values in report.per_class.items()
            ],
            hide_index=True,
            width="stretch",
        )

    if report.notes:
        meta(f"Notes: {report.notes}")

    if report.curves:
        base = metrics_path.parent if metrics_path else config.get_metrics_dir()
        shown = 0
        for relative in report.curves:
            candidate = (base / relative).resolve()
            if candidate.is_file():
                st.image(str(candidate), caption=relative, width="content")
                shown += 1
        if shown == 0:
            meta("Referenced plots were not found on disk.")


def _render_metrics_help(metrics_path) -> None:
    with st.expander("Developer notes", expanded=False):
        st.markdown(
            f"""
Metrics are read from `{metrics_path}` — copy values from your own evaluation
run, never estimate them:

```json
{_METRICS_SCHEMA_EXAMPLE}
```

`model_id` and `metrics` are required; every metric is a ratio in `[0, 1]`.
Missing metrics stay missing.
"""
        )


# --------------------------------------------------------------------------
# Session activity
# --------------------------------------------------------------------------
def _render_session_activity() -> None:
    section("Session activity", "Detections run in this browser session — usage, not model quality.")

    runs = get_runs(st.session_state)
    if not runs:
        empty_state(
            icon="activity",
            title="No detections yet in this session",
            body="Run an image through Detect or Camera to populate this section.",
        )
        return

    summary = summarise(runs)
    columns = st.columns(4, gap="small")
    columns[0].metric("Runs", summary.total_runs)
    columns[1].metric("Total detections", summary.total_faces)
    columns[2].metric("Mean per image", f"{summary.mean_faces_per_image:.2f}")
    columns[3].metric(
        "Mean confidence",
        f"{summary.mean_confidence:.1%}" if summary.mean_confidence is not None else "—",
    )

    records = runs_to_records(runs)
    st.dataframe(records, hide_index=True, width="stretch")

    chart_rows = [
        {"run": index + 1, "detections": record["detections"]}
        for index, record in enumerate(records)
    ]
    st.bar_chart(pd.DataFrame(chart_rows).set_index("run"), height=200)

    meta(
        f"Zero-detection runs: {summary.empty_runs} · by source: {summary.by_source} · "
        f"mean inference: "
        f"{f'{summary.mean_inference_ms:.0f} ms' if summary.mean_inference_ms else '—'}"
    )

    if st.button("Clear session activity", icon=":material/delete:"):
        clear_runs(st.session_state)
        st.rerun()


# --------------------------------------------------------------------------
# Technical detail (kept out of the primary view)
# --------------------------------------------------------------------------
def _render_technical_details(spec: ModelSpec) -> None:
    detector = get_detector(spec)
    info = detector.model_info()

    with st.expander("Model and dataset details", expanded=False):
        kv_row(
            [
                ("Model id", spec.id),
                ("Task", spec.task),
                ("Weights", "present" if info["weights_present"] else "missing"),
                ("Labels source", info["labels_source"]),
                ("General purpose", "yes" if spec.is_general_purpose else "no"),
            ]
        )
        meta(f"Weights path: {spec.weights_path}")
        meta(f"Class labels: {', '.join(info['labels']) if info['labels'] else 'unknown'}")

        dataset = spec.dataset
        if dataset:
            section("Dataset", "Declared composition of the training data.")
            split = dataset.get("split") or {}
            kv_row(
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
            _render_dataset_checks(dataset)
            labels = spec.provenance.get("dataset_name") if spec.provenance else None
            if labels:
                meta(f"Dataset: {labels}")
        else:
            meta("No dataset information is recorded for this model.")

        if spec.provenance:
            section("Provenance")
            bullets(
                [f"{key.replace('_', ' ')}: {value}" for key, value in spec.provenance.items()]
            )


def _render_dataset_checks(dataset: dict) -> None:
    """Surface declared-composition inconsistencies as quiet inline notes."""
    split = dataset.get("split") or {}
    total = dataset.get("total_images")
    parts = [split.get("train"), split.get("val"), split.get("test")]
    if not (total and all(isinstance(part, int) for part in parts)):
        return

    split_total = sum(parts)  # type: ignore[arg-type]
    annotated = dataset.get("annotated_images")
    if isinstance(annotated, int) and split_total > annotated:
        note(
            f"The declared split covers {split_total} images while {annotated} are "
            f"annotated, so up to {split_total - annotated} split images may have no "
            "label file. Verify before treating metrics as authoritative.",
            tone="warn",
            icon="alert-triangle",
        )
