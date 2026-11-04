"""Presentation of a detection result.

The result panel is a small application surface, not a proof sheet: a summary line, the
annotated image, one row per detection, and the download — with the numbers and the raw
records in sibling tabs so the primary view stays legible.

Every value comes from the `DetectionResult` the detector produced, or from a timing
measured around the analyse call. Nothing is estimated or invented; a measurement that
is unavailable is omitted rather than filled with a placeholder.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from app.core.detector import DetectionResult
from app.core.image_io import to_png_bytes
from app.core.rendering import BOX_COLOURS
from app.ui.components import (
    bullets,
    detection_list,
    empty_state,
    fact_strip,
    meta,
    note,
)

__all__ = [
    "fact_fields",
    "format_ms",
    "readout_fields",
    "render_result_panel",
]

def format_ms(milliseconds: float) -> str:
    """A measured duration, honestly rounded.

    Sub-millisecond values are reported as "<1 ms" rather than "0 ms": the
    measurement exists, so it must not read as no time at all.
    """
    if milliseconds < 1:
        return "<1 ms"
    return f"{milliseconds:.0f} ms"


NOT_ANALYSED_TITLE = "Prediction results will appear here"
NOT_ANALYSED_BODY = (
    "Choose an image and select Analyse image. Results are shown only for an analysis "
    "you asked for."
)


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


def fact_fields(
    result: DetectionResult, total_ms: float | None
) -> list[tuple[str, str]]:
    """The compact fact strip: only measurements that actually exist."""
    rows: list[tuple[str, str]] = [("Detections", str(result.count))]
    if result.mean_confidence is not None:
        rows.append(("Mean confidence", f"{result.mean_confidence:.1%}"))
    if result.inference_ms and result.inference_ms > 0:
        rows.append(("Inference", format_ms(result.inference_ms)))
    if total_ms is not None and total_ms > 0:
        rows.append(("Total", format_ms(total_ms)))
    return rows


def summary_line(result: DetectionResult, total_ms: float | None) -> str:
    """`3 detections found · 412 ms total`, without the timing when unmeasured."""
    noun = "detection" if result.count == 1 else "detections"
    text = f"**{result.count} {noun} found**"
    if total_ms is not None and total_ms > 0:
        text += f" · {format_ms(total_ms)} total"
    return text


def render_result_panel(
    *,
    record: dict[str, Any] | None,
    filename: str,
    model_name: str,
) -> None:
    """Render Results / Details / JSON for the stored analysis, or its empty state."""
    results_tab, details_tab, raw_tab = st.tabs(["Results", "Details", "JSON"])

    outcome = record.get("outcome") if record else None
    processed = outcome.processed if outcome is not None and outcome.ok else None
    result: DetectionResult | None = outcome.result if outcome is not None and outcome.ok else None
    total_ms = record.get("total_ms") if record else None

    with results_tab:
        if outcome is None:
            empty_state(title=NOT_ANALYSED_TITLE, body=NOT_ANALYSED_BODY)
        elif not outcome.ok or result is None:
            note(
                "Image analysis is temporarily unavailable. Please try again in a moment.",
                tone="warn",
            )
            meta("Your image was not modified or stored.")
        else:
            st.markdown(summary_line(result, total_ms))
            if processed is not None:
                st.image(
                    processed,
                    width="stretch",
                    alt="The uploaded image with the model's detections marked",
                )
            _render_detection_rows(result)
            if result.count == 0:
                note(
                    "Nothing matched at this confidence level. A clearer photo, or a lower "
                    "confidence threshold under Params, may find more."
                )
            if processed is not None:
                render_download_button(processed, filename)

    with details_tab:
        if result is None:
            empty_state(
                title="No measurements yet",
                body="Details list the counts, confidences, timing and thresholds behind a result.",
            )
        else:
            fact_strip(fact_fields(result, total_ms))
            meta(
                f"Threshold {result.confidence_threshold:.2f} · overlap "
                f"{result.iou_threshold:.2f} · {model_name}",
            )
            if result.detections:
                _render_box_table(result)
                with st.expander("Source image", expanded=False):
                    st.image(
                        record["image"],
                        width="stretch",
                        alt="The image as uploaded, without annotations",
                    )
            else:
                meta("No boxes were produced for this image.")

    with raw_tab:
        if result is None:
            empty_state(
                title="No records yet",
                body="The JSON tab returns the detection records exactly as the model produced them.",
            )
        else:
            st.json(
                {
                    "file": filename,
                    "model": model_name,
                    "detections": result.records(),
                },
                expanded=True,
            )


def _render_detection_rows(result: DetectionResult) -> None:
    """One row per detection, in the same order as the overlay's colours."""
    if not result.detections:
        return
    detection_list(result.records(), BOX_COLOURS)


def _render_box_table(result: DetectionResult) -> None:
    columns = st.columns([1, 1])
    with columns[0]:
        meta("Boxes, in overlay order")
    with columns[1]:
        meta(f"{result.count} shown", mono=True)
    st.dataframe(
        pd.DataFrame(result.records()),
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


# `bullets` is re-exported for the Help page's use of this module's vocabulary.
_ = bullets
