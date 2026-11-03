"""Presentation of a detection result: counts, confidence scores, table, export.

All values come from the `DetectionResult` produced by the detector; this module
only formats them.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.detector import DetectionResult
from app.core.image_io import to_png_bytes
from app.core.registry import ModelSpec
from app.ui.components import meta, note

__all__ = [
    "render_detection_table",
    "render_download_button",
    "render_no_detections_note",
    "render_summary_metrics",
]


def render_summary_metrics(result: DetectionResult, spec: ModelSpec) -> None:
    """Headline numbers, derived solely from the inference result."""
    mean_conf = result.mean_confidence
    columns = st.columns(4, gap="small")
    columns[0].metric("Detections", result.count)
    columns[1].metric(
        "Mean confidence", f"{mean_conf:.1%}" if mean_conf is not None else "—"
    )
    columns[2].metric(
        "Confidence range",
        (
            f"{result.min_confidence:.2f} – {result.max_confidence:.2f}"
            if result.min_confidence is not None and result.max_confidence is not None
            else "—"
        ),
    )
    columns[3].metric("Inference time", f"{result.inference_ms:.0f} ms")
    meta(
        f"{spec.display_name} · confidence ≥ {result.confidence_threshold:.2f} · "
        f"IoU {result.iou_threshold:.2f} · "
        f"labels: {', '.join(result.labels_present) if result.labels_present else 'none'}"
    )


def render_detection_table(result: DetectionResult) -> None:
    """Per-detection confidence scores, most confident first."""
    if not result.detections:
        return
    records = sorted(result.records(), key=lambda row: row["confidence"], reverse=True)
    st.dataframe(
        pd.DataFrame(records),
        hide_index=True,
        width="stretch",
        column_config={
            "label": "class",
            "confidence": st.column_config.NumberColumn("confidence", format="%.4f"),
            "x1": st.column_config.NumberColumn("x1 (px)", format="%.1f"),
            "y1": st.column_config.NumberColumn("y1 (px)", format="%.1f"),
            "width": st.column_config.NumberColumn("width (px)", format="%.1f"),
            "height": st.column_config.NumberColumn("height (px)", format="%.1f"),
        },
    )


def render_no_detections_note(result: DetectionResult) -> None:
    if result.count:
        return
    note(
        f"No detections above the confidence threshold ({result.confidence_threshold:.2f}). "
        "Lower the threshold to include weaker candidates. A single-class model returns "
        "nothing for images that do not contain its subject.",
        icon="info",
    )


def render_download_button(processed_image, filename: str) -> None:
    """Offer the annotated image as a PNG download."""
    if processed_image is None:
        return
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    st.download_button(
        "Download annotated image",
        data=to_png_bytes(processed_image),
        file_name=f"{stem}_judetector.png",
        mime="image/png",
        icon=":material/download:",
    )
