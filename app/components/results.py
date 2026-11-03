"""Presentation of a detection result.

The primary view is deliberately small: how many detections, how confident, the
images and the download. Coordinates, applied thresholds and timing are real
measurements but of little use to someone who just wants the annotated image, so
they live in one collapsed section.

All values come from the `DetectionResult` produced by the detector; this module
only formats them.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.detector import DetectionResult
from app.core.image_io import to_png_bytes
from app.ui.components import kv_row, meta, note, section

__all__ = [
    "render_detection_details",
    "render_download_button",
    "render_no_detections_note",
    "render_result_summary",
]


def render_result_summary(result: DetectionResult) -> None:
    """Two headline numbers, derived solely from the inference result."""
    mean_conf = result.mean_confidence
    columns = st.columns(2, gap="small")
    columns[0].metric("Detections", result.count)
    columns[1].metric(
        "Mean confidence", f"{mean_conf:.1%}" if mean_conf is not None else "—"
    )


def render_no_detections_note(result: DetectionResult) -> None:
    if result.count:
        return
    note(
        "Nothing matched at this confidence level. Lower the confidence threshold in "
        "Advanced settings to include weaker matches, or try a clearer photo.",
        icon="info",
    )


def render_detection_details(result: DetectionResult) -> None:
    """Collapsed technical detail: applied settings, timing and per-box rows."""
    with st.expander("Detection details", expanded=False):
        range_text = (
            f"{result.min_confidence:.2f} – {result.max_confidence:.2f}"
            if result.min_confidence is not None and result.max_confidence is not None
            else "—"
        )
        kv_row(
            [
                ("Confidence threshold", f"{result.confidence_threshold:.2f}"),
                ("Overlap (IoU)", f"{result.iou_threshold:.2f}"),
                ("Confidence range", range_text),
                ("Processing time", f"{result.inference_ms:.0f} ms"),
            ]
        )
        if not result.detections:
            meta("No boxes were produced for this image.")
            return

        section("Detected items")
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
