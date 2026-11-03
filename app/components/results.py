"""Presentation of a detection result.

The primary view is a fixed-column readout of the numbers the detector actually
produced — count, mean confidence, confidence range, applied thresholds — then the
two prints (original and annotated) and the download. Per-box coordinates and
timing are real measurements but of little use to someone who wants the annotated
image, so they live in one collapsed section.

All values come from the `DetectionResult` produced by the detector; this module
only formats them. Nothing is estimated, rounded from a guess, or invented.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.detector import DetectionResult
from app.core.image_io import to_png_bytes
from app.ui.components import meta, note, readout, section

__all__ = [
    "readout_fields",
    "render_detection_details",
    "render_download_button",
    "render_no_detections_note",
    "render_result_readout",
]


def readout_fields(result: DetectionResult) -> list[tuple[str, str]]:
    """The result as label/value pairs, every one of them measured.

    Confidence rows appear only when the result carries them, so an empty result
    never shows a placeholder that could be read as a score.
    """
    rows: list[tuple[str, str]] = [("Detections", str(result.count))]
    if result.mean_confidence is not None:
        rows.append(("Mean confidence", f"{result.mean_confidence:.1%}"))
    if result.min_confidence is not None and result.max_confidence is not None:
        rows.append(
            (
                "Confidence range",
                f"{result.min_confidence:.1%} – {result.max_confidence:.1%}",
            )
        )
    rows.append(("Threshold", f"{result.confidence_threshold:.2f}"))
    rows.append(("Overlap", f"{result.iou_threshold:.2f}"))
    return rows


def render_result_readout(result: DetectionResult) -> None:
    """Render the readout block. Labels left, mono values right, aligned."""
    readout(readout_fields(result))


def render_no_detections_note(result: DetectionResult) -> None:
    if result.count:
        return
    note(
        "Nothing matched at this confidence level. Lower the confidence threshold in "
        "Advanced settings to include weaker matches, or try a clearer photo."
    )


def render_detection_details(result: DetectionResult) -> None:
    """Collapsed technical detail: applied settings, timing and per-box rows."""
    with st.expander("Detection details", expanded=False):
        readout([("Processing time", f"{result.inference_ms:.0f} ms")])
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
    )
