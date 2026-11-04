"""The shared analyse-image workflow used by Detect and Camera.

One place owns the sequence *choose image → analyse → inspect result*, so both entry
points behave identically and neither can drift from the detection pipeline.

Two rules the interface depends on:

* **Analysis is explicit.** Nothing here runs inference until the *Analyse image*
  button reports a press. Changing the image or the parameters only invalidates the
  stored result; it never re-runs the model.
* **Timing is measured, never assumed.** Inference time comes from the detector;
  total time is measured around the whole analyse call and stored next to the result.
  When a measurement is missing the interface omits it rather than showing a guess.

User-facing failures stay plain: no paths, no dependency names, no registry
vocabulary. The underlying error is kept in `session_state` under
`last_analysis_error` for the developer page, which is where diagnostics belong.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import streamlit as st
from PIL import Image

from app.components.pipeline import AnalysisOutcome, analyse_image
from app.core.errors import InvalidImageError
from app.core.image_io import downscale, load_image
from app.core.registry import ModelSpec
from app.core.runtime import get_detector
from app.core.stats import DetectionRun, record_run_once
from app.ui.components import meta, note

__all__ = [
    "ERROR_STATE_KEY",
    "UNAVAILABLE_MESSAGE",
    "UNREADABLE_MESSAGE",
    "analyse_controls",
    "analyse_now",
    "clear_pending",
    "decode_image",
    "image_facts",
    "pending_image",
    "remember_pending",
    "stored_analysis",
]

ERROR_STATE_KEY = "last_analysis_error"

UNAVAILABLE_MESSAGE = "Image analysis is temporarily unavailable. Please try again in a moment."
UNREADABLE_MESSAGE = "That file could not be read as an image. Try a JPG, PNG, WEBP or BMP file."

#: A file chosen on Home and handed to Detect. Holds bytes only; nothing is analysed.
PENDING_KEY = "pending_image"


def decode_image(data: bytes) -> Image.Image | None:
    """Decode uploaded bytes, or return ``None`` when the file is not an image."""
    try:
        image = load_image(data)
    except InvalidImageError:
        return None
    image, _ = downscale(image)
    return image


# --------------------------------------------------------------------------
# Handoff from Home to Detect
# --------------------------------------------------------------------------
def remember_pending(data: bytes, filename: str) -> None:
    """Stage an image for Detect. Deliberately does not analyse it."""
    st.session_state[PENDING_KEY] = {"data": data, "filename": filename}


def pending_image() -> tuple[bytes, str] | None:
    """The staged image, if any."""
    staged = st.session_state.get(PENDING_KEY)
    if not isinstance(staged, dict):
        return None
    data, filename = staged.get("data"), staged.get("filename")
    if not isinstance(data, bytes) or not isinstance(filename, str):
        return None
    return data, filename


def clear_pending() -> None:
    st.session_state.pop(PENDING_KEY, None)


def image_facts(image: Image.Image, filename: str) -> str:
    """One honest line of real image facts: name, pixel size, megapixels."""
    megapixels = image.width * image.height / 1_000_000
    return f"{filename} · {image.width} × {image.height} px · {megapixels:.1f} MP"


def signature_for(
    filename: str, data_length: int, confidence: float, iou: float
) -> tuple[Any, ...]:
    """Identity of one analysis configuration.

    The stored result only renders while this matches, so a changed image or changed
    thresholds never leaves stale numbers on screen next to controls that no longer
    produced them.
    """
    return (filename, data_length, round(confidence, 2), round(iou, 2))


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------
def analyse_now(
    *,
    namespace: str,
    source: str,
    image: Image.Image,
    filename: str,
    data_length: int,
    spec: ModelSpec,
    confidence: float,
    iou: float,
) -> dict[str, Any]:
    """Run one inference pass and store it under `namespace`.

    Only called from a pressed button. Returns the stored record so the caller can
    render it without a second lookup.
    """
    started = time.perf_counter()
    with st.spinner("Analysing image…"):
        outcome = analyse_image(image, spec, get_detector(spec), confidence=confidence, iou=iou)
    total_ms = (time.perf_counter() - started) * 1000.0

    if outcome.ok:
        _record_run(outcome, image, spec, source, filename)
    else:
        _remember_error(outcome, source)

    record = {
        "signature": signature_for(filename, data_length, confidence, iou),
        "outcome": outcome,
        "image": image,
        "filename": filename,
        "total_ms": total_ms,
    }
    st.session_state[namespace] = record
    return record


def analyse_controls(
    *,
    namespace: str,
    source: str,
    image: Image.Image,
    filename: str,
    data_length: int,
    spec: ModelSpec,
    confidence: float,
    iou: float,
    button_label: str = "Analyse image",
) -> dict[str, Any] | None:
    """The single explicit Analyse action, plus whatever is already stored for it.

    Returns the stored record for exactly this configuration, or ``None``. When a
    record exists for the same image but different thresholds, the interface says so
    instead of showing numbers the current controls did not produce.
    """
    signature = signature_for(filename, data_length, confidence, iou)
    if st.button(button_label, type="primary", icon=":material/play_arrow:", width="stretch"):
        return analyse_now(
            namespace=namespace,
            source=source,
            image=image,
            filename=filename,
            data_length=data_length,
            spec=spec,
            confidence=confidence,
            iou=iou,
        )

    stored = stored_analysis(namespace, signature)
    if stored is None:
        previous = st.session_state.get(namespace)
        if isinstance(previous, dict) and previous.get("filename") == filename:
            meta("Thresholds changed — analyse again to apply them.")
    return stored


def stored_analysis(namespace: str, signature: tuple[Any, ...]) -> dict[str, Any] | None:
    """The stored result for exactly this configuration, if one exists."""
    stored = st.session_state.get(namespace)
    if isinstance(stored, dict) and stored.get("signature") == signature:
        return stored
    return None


def render_failure(outcome: AnalysisOutcome) -> None:
    """The plain unavailable message, with the guarantee that matters."""
    note(UNAVAILABLE_MESSAGE, tone="warn")


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
