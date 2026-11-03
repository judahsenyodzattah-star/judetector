"""The shared analyse-image workflow used by Detect and Camera.

One place owns the sequence *preview → analyse → results*, so both entry points
behave identically and neither can drift from the detection pipeline.

User-facing failures are deliberately plain: no paths, no dependency names, no
registry vocabulary. The underlying error is kept in `session_state` under
`last_analysis_error` for the developer page, which is where diagnostics belong.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st
from PIL import Image

from app.components.pipeline import AnalysisOutcome, analyse_image
from app.components.results import (
    render_detection_details,
    render_download_button,
    render_no_detections_note,
    render_result_summary,
)
from app.core.errors import InvalidImageError
from app.core.image_io import downscale, load_image
from app.core.registry import ModelSpec
from app.core.runtime import get_detector
from app.core.stats import DetectionRun, record_run_once
from app.ui.components import meta, note, section

__all__ = [
    "ERROR_STATE_KEY",
    "UNAVAILABLE_MESSAGE",
    "UNREADABLE_MESSAGE",
    "analysis_workspace",
    "decode_image",
    "render_outcome",
]

ERROR_STATE_KEY = "last_analysis_error"

UNAVAILABLE_MESSAGE = "Image analysis is temporarily unavailable. Please try again in a moment."
UNREADABLE_MESSAGE = "That file could not be read as an image. Try a JPG, PNG, WEBP or BMP file."


def decode_image(data: bytes) -> Image.Image | None:
    """Decode uploaded bytes, or return ``None`` when the file is not an image."""
    try:
        image = load_image(data)
    except InvalidImageError:
        return None
    image, _ = downscale(image)
    return image


def analysis_workspace(
    *,
    namespace: str,
    source: str,
    data: bytes,
    filename: str,
    spec: ModelSpec,
    confidence: float,
    iou: float,
    button_label: str = "Analyse image",
    image: Image.Image | None = None,
) -> None:
    """Render the Analyse action and, once pressed, the results.

    Results are cached per (file, size, thresholds) so interacting with the rest of
    the page never silently re-runs inference or double-counts session activity.
    """
    if image is None:
        image = decode_image(data)
    if image is None:
        note(UNREADABLE_MESSAGE, tone="warn", icon="alert-circle")
        return

    signature = (filename, len(data), round(confidence, 2), round(iou, 2))
    pressed = st.button(button_label, type="primary", icon=":material/bolt:")

    if pressed:
        with st.spinner("Analysing image…"):
            outcome = analyse_image(
                image, spec, get_detector(spec), confidence=confidence, iou=iou
            )
        if outcome.ok:
            _record_run(outcome, image, spec, source, filename)
        else:
            _remember_error(outcome, source)
        st.session_state[namespace] = {
            "signature": signature,
            "outcome": outcome,
            "image": image,
        }

    stored = st.session_state.get(namespace)
    if stored and stored.get("signature") == signature:
        render_outcome(stored["outcome"], stored["image"], filename)


def render_outcome(outcome: AnalysisOutcome, image: Image.Image, filename: str) -> None:
    """Show either the plain unavailable message or the real result."""
    if not outcome.ok:
        note(UNAVAILABLE_MESSAGE, tone="warn", icon="alert-circle")
        meta("Your image was not modified or stored.")
        return

    result = outcome.result
    assert result is not None  # guaranteed by outcome.ok

    section("Result")
    render_result_summary(result)
    render_no_detections_note(result)

    original_column, detected_column = st.columns(2, gap="medium")
    with original_column:
        st.image(image, caption="Original", width="stretch")
    with detected_column:
        st.image(outcome.processed, caption="Detected", width="stretch")

    if outcome.processed is not None:
        render_download_button(outcome.processed, filename)

    render_detection_details(result)


def _record_run(
    outcome: AnalysisOutcome,
    image: Image.Image,
    spec: ModelSpec,
    source: str,
    filename: str,
) -> None:
    """Add this inference pass to session statistics (unchanged semantics)."""
    result = outcome.result
    if result is None:
        return
    record_run_once(
        st.session_state,
        DetectionRun(
            source=source,
            filename=filename,
            model_id=spec.id,
            face_count=result.count,
            image_width=image.width,
            image_height=image.height,
            confidence_threshold=result.confidence_threshold,
            iou_threshold=result.iou_threshold,
            mean_confidence=result.mean_confidence,
            min_confidence=result.min_confidence,
            max_confidence=result.max_confidence,
            inference_ms=result.inference_ms,
            labels=result.labels_present,
        ),
        signature=(
            source,
            filename,
            image.width,
            image.height,
            round(result.confidence_threshold, 2),
            round(result.iou_threshold, 2),
            result.count,
        ),
    )


def _remember_error(outcome: AnalysisOutcome, source: str) -> None:
    """Keep the technical cause for the developer page only."""
    st.session_state[ERROR_STATE_KEY] = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "title": outcome.error_title or "Analysis failed",
        "message": outcome.error_message or "",
        "unavailable": bool(outcome.unavailable),
    }
