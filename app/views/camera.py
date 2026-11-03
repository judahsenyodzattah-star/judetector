"""Camera page: browser snapshot → detection (continuous video is out of scope)."""

from __future__ import annotations

import streamlit as st

from app.components.model_sidebar import render_settings, select_model
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

__all__ = ["render"]


def render() -> None:
    st.title("Camera")
    st.caption("Capture a browser camera snapshot and analyse it with the active model.")

    spec, model_error = select_model()
    confidence, iou = render_settings()

    if model_error:
        st.error(f"Model configuration problem: {model_error}")
        return
    if spec is None:
        return

    render_model_caption(spec)
    render_scope_warning(spec)

    st.info(
        "**Snapshot mode.** The browser captures a single still frame, which is then "
        "analysed exactly like an uploaded image. Continuous live video is not part "
        "of this milestone — see the note below.",
        icon="📷",
    )

    snapshot = st.camera_input(
        "Take a snapshot",
        help="Requires browser camera permission. Works over HTTPS or on localhost.",
    )

    if snapshot is None:
        st.caption(
            "If no camera appears: grant camera permission in the browser, ensure the "
            "page is served over HTTPS (or on localhost), and check that no other "
            "application is holding the camera. A laptop without a webcam will show "
            "no capture control — use the **Detect** page instead."
        )
        return

    try:
        image = load_image(snapshot.getvalue())
    except InvalidImageError as exc:
        st.error(f"Could not read the camera capture — {exc}")
        return

    image, _ = downscale(image)
    detector = get_detector(spec)
    outcome = analyse_image(image, spec, detector, confidence=confidence, iou=iou)

    original_column, processed_column = st.columns(2)
    with original_column:
        st.subheader("Snapshot")
        st.image(image, width="stretch")
        st.caption(describe_image(image))
    with processed_column:
        st.subheader("Processed")
        if outcome.ok and outcome.processed is not None:
            st.image(outcome.processed, width="stretch")
            st.caption(f"{outcome.count} box(es) drawn · confidence ≥ {confidence:.2f}")
        else:
            st.info("No processed image: detection could not run.", icon="ℹ️")

    if not outcome.ok:
        if outcome.unavailable:
            st.error(f"**{outcome.error_title}**\n\n{outcome.error_message}")
            render_setup_help(spec)
        else:
            st.error(f"**{outcome.error_title}**\n\n{outcome.error_message}")
        return

    result = outcome.result
    assert result is not None

    st.divider()
    render_summary_metrics(result, spec)
    render_no_detections_note(result)
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

    with st.expander("Why snapshot instead of live video?"):
        st.markdown(
            """
Continuous live video in Streamlit requires a WebRTC component plus reachable
STUN/TURN servers, and is unreliable on free hosting tiers. Snapshot capture uses
the browser's native camera API, works wherever the app is served over HTTPS, and
reuses the same detection pipeline — so the feature is genuinely available rather
than nominally available. Live streaming can be added later as a separate page
without changing `DetectorService`.
"""
        )
