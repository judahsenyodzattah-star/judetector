"""Dashboard: model information, recorded evaluation metrics and session statistics.

Three strictly separated kinds of number, each labelled at the point of display:

1. **Model / dataset facts** — declared by the project author (config registry).
2. **Evaluation metrics** — read verbatim from an evaluation record on disk.
   If no record exists, this page says so and shows nothing. It never estimates.
3. **Session statistics** — computed from this session's real inference runs.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.model_sidebar import select_model
from app.components.status import render_labels_line, render_scope_warning
from app.core import config
from app.core.errors import MetricsSchemaError
from app.core.metrics import METRIC_LABELS, load_metrics
from app.core.registry import ModelSpec
from app.core.runtime import get_detector
from app.core.stats import clear_runs, get_runs, runs_to_records, summarise

__all__ = ["render"]

_METRICS_SCHEMA_EXAMPLE = """{
  "model_id": "judah-face-v1",
  "model_name": "judah model v1",
  "split": "test",
  "evaluated_on": "2026-11-15",
  "source": "Ultralytics HUB evaluation on the held-out test split",
  "metrics": { "mAP50": 0.0, "mAP50_95": 0.0, "precision": 0.0, "recall": 0.0 },
  "notes": "Copy these values from your own evaluation run."
}"""


def render() -> None:
    st.title("Dashboard")

    spec, model_error = select_model()
    if model_error:
        st.error(f"Model configuration problem: {model_error}")
        return
    if spec is None:
        return

    detector = get_detector(spec)

    _render_model_section(spec, detector)
    st.divider()
    _render_dataset_section(spec)
    st.divider()
    _render_metrics_section(spec)
    st.divider()
    _render_session_statistics()


# --------------------------------------------------------------------------
def _render_model_section(spec: ModelSpec, detector) -> None:
    st.subheader("Model information")
    info = detector.model_info()

    columns = st.columns(4)
    columns[0].metric("Task", spec.task)
    columns[1].metric("Weights", "found" if info["weights_present"] else "missing")
    columns[2].metric("Loaded in memory", "yes" if info["loaded"] else "no")
    columns[3].metric("Class labels", len(info["labels"]) or "—")

    st.dataframe(
        [
            {"property": "model id", "value": spec.id},
            {"property": "display name", "value": spec.display_name},
            {"property": "kind", "value": spec.kind},
            {
                "property": "general-purpose face detector",
                "value": "yes" if spec.is_general_purpose else "no",
            },
            {"property": "weights path", "value": str(spec.weights_path)},
            {"property": "weights present", "value": str(info["weights_present"])},
            {"property": "labels source", "value": info["labels_source"]},
        ],
        hide_index=True,
        width="stretch",
    )
    render_labels_line(tuple(info["labels"]), info["labels_source"])
    render_scope_warning(spec)

    if spec.provenance:
        with st.expander("Provenance (declared by project author)"):
            st.dataframe(
                [{"property": key, "value": str(value)} for key, value in spec.provenance.items()],
                hide_index=True,
                width="stretch",
            )


def _render_dataset_section(spec: ModelSpec) -> None:
    st.subheader("Dataset information")
    st.caption(
        "Declared dataset composition from the project registry. These are descriptive "
        "facts about the data, not measured model performance."
    )
    dataset = spec.dataset
    if not dataset:
        st.info("No dataset information is recorded for this model.", icon="ℹ️")
        return

    columns = st.columns(4)
    columns[0].metric("Total images", dataset.get("total_images", "—"))
    columns[1].metric("Annotated", dataset.get("annotated_images", "—"))
    columns[2].metric("Reserved (unannotated)", dataset.get("unannotated_reserved", "—"))
    classes = dataset.get("classes") or []
    columns[3].metric("Classes", len(classes) or "—")

    dataset_name = (
        dataset.get("dataset_name")
        or (spec.provenance or {}).get("dataset_name")
        or "—"
    )
    rows: list[dict[str, object]] = [
        {"property": "dataset name", "value": str(dataset_name)},
        {"property": "classes", "value": ", ".join(classes) if classes else "—"},
    ]
    split = dataset.get("split") or {}
    for split_name in ("train", "val", "test"):
        if split_name in split:
            rows.append({"property": f"{split_name} images", "value": split[split_name]})
    if dataset.get("source"):
        rows.append({"property": "source", "value": str(dataset["source"])})
    st.dataframe(rows, hide_index=True, width="stretch")

    total = dataset.get("total_images")
    parts = [split.get("train"), split.get("val"), split.get("test")]
    if total and all(isinstance(part, int) for part in parts):
        split_total = sum(parts)  # type: ignore[arg-type]
        if split_total != total:
            st.warning(
                f"Split totals ({split_total}) do not equal the declared image count "
                f"({total}). Verify the split before treating it as authoritative.",
                icon="⚠️",
            )
        annotated = dataset.get("annotated_images")
        if isinstance(annotated, int) and split_total > annotated:
            st.warning(
                f"The declared split covers {split_total} images but only {annotated} are "
                f"annotated, so up to {split_total - annotated} split images may have no "
                "label file. Confirm this against the dataset before reporting metrics.",
                icon="⚠️",
            )


def _render_metrics_section(spec: ModelSpec) -> None:
    st.subheader("Evaluation metrics")
    st.caption(
        "Read directly from a recorded evaluation run. If nothing is recorded here, "
        "the app shows nothing — metrics are never estimated or invented."
    )

    metrics_path = spec.metrics_file
    try:
        report = load_metrics(metrics_path)
    except MetricsSchemaError as exc:
        st.error(f"**The stored metrics record is invalid.**\n\n{exc}")
        return

    if report is None:
        st.info(
            f"No evaluation metrics recorded yet for `{spec.id}`. "
            f"Expected file: `{metrics_path}`.",
            icon="ℹ️",
        )
        with st.expander("How to record real metrics", expanded=False):
            st.markdown(
                f"""
Create `{metrics_path}` containing values copied from **your own** evaluation run
(Ultralytics HUB → your model → evaluation, or a local `model.val(split='test')`):

```json
{_METRICS_SCHEMA_EXAMPLE}
```

Rules the loader enforces:

- `model_id` and `metrics` are required.
- Every metric must be a number in `[0, 1]` (ratios, not percentages).
- Missing metrics stay missing — the dashboard shows only what the file contains.
- A malformed file raises a visible error instead of being silently replaced.
"""
            )
        return

    items = report.display_items()
    if items:
        columns = st.columns(len(items))
        for column, (label, value) in zip(columns, items):
            column.metric(label, f"{value:.4f}")
    for label, value in report.extra_items():
        st.caption(f"Additional recorded metric — {label}: {value:.4f}")
    if not items:
        st.caption("The record contains no recognised metric values.")

    details = [
        {"property": "model id", "value": report.model_id},
        {"property": "split", "value": report.split or "not stated"},
        {"property": "evaluated on", "value": report.evaluated_on or "not stated"},
        {"property": "source", "value": report.source or "not stated"},
    ]
    st.dataframe(details, hide_index=True, width="stretch")

    if report.per_class:
        st.markdown("**Per-class metrics (as recorded)**")
        rows = [
            {"class": class_name, **{METRIC_LABELS.get(k, k): v for k, v in values.items()}}
            for class_name, values in report.per_class.items()
        ]
        st.dataframe(rows, hide_index=True, width="stretch")

    if report.notes:
        st.caption(f"Notes from the evaluation record: {report.notes}")

    if report.curves:
        st.markdown("**Recorded performance plots**")
        base = metrics_path.parent if metrics_path else config.get_metrics_dir()
        shown = 0
        for relative in report.curves:
            candidate = (base / relative).resolve()
            if candidate.is_file():
                st.image(str(candidate), caption=relative, width="content")
                shown += 1
        if shown == 0:
            st.caption("Curve files are referenced by the record but none were found on disk.")
    else:
        st.caption(
            "No performance plots are recorded. Save your Ultralytics result plots "
            "(results.png, PR curve, F1 curve) next to the metrics file and list them "
            "under a `curves` key to display them here."
        )


def _render_session_statistics() -> None:
    st.subheader("Detection statistics — this session")
    st.caption(
        "Computed from detections actually run in this browser session. These describe "
        "usage, not model quality, and reset with the session."
    )

    runs = get_runs(st.session_state)
    if not runs:
        st.info(
            "No detections yet in this session. Run an image through **Detect** or "
            "**Camera** and the statistics will appear here.",
            icon="ℹ️",
        )
        return

    summary = summarise(runs)
    columns = st.columns(4)
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
    st.bar_chart(pd.DataFrame(chart_rows).set_index("run"), height=220)
    st.caption(
        f"Runs with zero detections: {summary.empty_runs} · "
        f"by source: {summary.by_source} · "
        f"mean inference: "
        f"{f'{summary.mean_inference_ms:.0f} ms' if summary.mean_inference_ms else '—'}"
    )

    if st.button("Clear session statistics"):
        clear_runs(st.session_state)
        st.rerun()
