"""Camera: browser snapshot capture → detection.

Snapshot only. Continuous video would need a WebRTC component and reachable
STUN/TURN servers, so it is deliberately out of scope and never claimed.
"""

from __future__ import annotations

import streamlit as st

from app.components.model_sidebar import detection_settings
from app.components.pipeline import analyse_image
from app.components.results import (
    render_detection_table,
    render_download_button,
    render_no_detections_note,
    render_summary_metrics,
)
from app.components.status import (
    render_model_caption,
    render_scope_warning,
    render_setup_help,
)
from app.core.errors import InvalidImageError
from app.core.image_io import describe_image, downscale, load_image
from app.core.runtime import get_detector
from app.core.stats import DetectionRun, record_run_once
from app.ui.components import empty_state, meta, note, page_header, section
from app.ui.theme import inject_theme

__all__ = ["render"]


def render() -> None:
    inject_theme()

    spec, confidence, iou, model_error = detection_settings()
    connected = bool(spec is not None and spec.weights_present)

    page_header(
        "Camera",
        "Capture a single frame from the browser camera and analyse it with the "
        "connected model.",
        eyebrow="Workspace",
        status=("Model connected", "ok") if connected else ("Model not connected", "warn"),
    )

    if model_error:
        st.error(f"Model configuration problem: {model_error}")
        return
    if spec is None:
        return

    render_model_caption(spec)
    render_scope_warning(spec)

    note(
        "Snapshot capture: one still frame per shot, analysed exactly like an upload. "
        "Live video detection is not supported.",
        icon="camera",
    )

    if not connected:
        note(
            "Detection is unavailable until model weights are connected. Capture still "
            "works for previewing framing.",
            icon="alert-circle",
            tone="warn",
        )

    capture_column, preview_column = st.columns([1, 1], gap="medium")

    with capture_column:
        st.markdown("**Camera**")
        snapshot = st.camera_input(
            "Take a snapshot",
            help="Requires camera permission. Works over HTTPS or on localhost.",
        )
        if snapshot is None:
            meta(
                "No camera? Grant permission in the browser, serve the app over HTTPS or "
                "localhost, then try again — or use Detect to upload an image."
            )

    with preview_column:
        st.markdown("**Result**")
        if snapshot is None:
            empty_state(
                icon="camera",
                title="Awaiting capture",
                body="Take a snapshot to see detections, confidence scores and the "
                "annotated frame here.",
            )

    if snapshot is None:
        return

    try:
        image = load_image(snapshot.getvalue())
    except InvalidImageError as exc:
        st.error(f"Could not read the camera capture — {exc}")
        return

    image, _ = downscale(image)
    detector = get_detector(spec)
    outcome = analyse_image(image, spec, detector, confidence=confidence, iou=iou)

    if not outcome.ok:
        st.error(f"**{outcome.error_title}**\n\n{outcome.error_message}")
        if outcome.unavailable:
            render_setup_help(spec)
        return

    result = outcome.result
    assert result is not None

    section("Results", f"Snapshot · {describe_image(image)}")
    render_summary_metrics(result, spec)
    render_no_detections_note(result)

    annotated_column, original_column = st.columns(2, gap="medium")
    with annotated_column:
        st.image(outcome.processed, caption="Annotated", width="stretch")
    with original_column:
        st.image(image, caption="Snapshot", width="stretch")

    if result.detections:
        section("Detections", "Sorted by confidence, with pixel coordinates.")
        render_detection_table(result)

    if outcome.processed is not None:
        render_download_button(outcome.processed, "camera_snapshot.png")

    record_run_once(
        st.session_state,
        DetectionRun(
            source="camera",
            filename="camera_snapshot.png",
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
            "camera",
            image.width,
            image.height,
            round(confidence, 2),
            round(iou, 2),
            result.count,
        ),
    )
    meta("Added to this session's activity.")
