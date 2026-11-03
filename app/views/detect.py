"""Detect page: image upload → detection → annotated image + counts + scores."""

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
    render_labels_line,
    render_model_caption,
    render_scope_warning,
    render_setup_help,
)
from app.core import config
from app.core.errors import InvalidImageError
from app.core.image_io import describe_image, downscale, load_image
from app.core.runtime import get_detector
from app.core.stats import DetectionRun, record_run_once

__all__ = ["render"]


def render() -> None:
    st.title("Detect")
    st.caption("Upload an image to run the active detector over it.")

    spec, model_error = select_model()
    confidence, iou = render_settings()

    if model_error:
        st.error(f"Model configuration problem: {model_error}")
        return
    if spec is None:
        return

    render_model_caption(spec)
    render_scope_warning(spec)

    uploaded = st.file_uploader(
        "Choose an image",
        type=list(config.SUPPORTED_IMAGE_TYPES),
        help=f"Max {config.MAX_UPLOAD_MB} MB. JPG, PNG, WEBP or BMP.",
    )

    if uploaded is None:
        st.info(
            "Upload an image to begin. No detection is run and no statistics are "
            "recorded until you do.",
            icon="ℹ️",
        )
        render_labels_line(spec.declared_labels, "declared")
        return

    try:
        image = load_image(uploaded.getvalue())
    except InvalidImageError as exc:
        st.error(f"Could not read that file — {exc}")
        return

    image, was_resized = downscale(image)
    if was_resized:
        st.info(
            f"Large image downscaled to {describe_image(image)} "
            f"(guard: {config.MAX_IMAGE_DIMENSION} px).",
            icon="ℹ️",
        )

    detector = get_detector(spec)
    outcome = analyse_image(image, spec, detector, confidence=confidence, iou=iou)

    original_column, processed_column = st.columns(2)
    with original_column:
        st.subheader("Original image")
        st.image(image, width="stretch")
        st.caption(f"`{uploaded.name}` · {describe_image(image)}")

    with processed_column:
        st.subheader("Processed image")
        if outcome.ok and outcome.processed is not None:
            st.image(outcome.processed, width="stretch")
            st.caption(
                f"{outcome.count} box(es) drawn · model `{spec.id}` · "
                f"confidence ≥ {confidence:.2f}"
            )
        else:
            st.info(
                "No processed image: detection could not run, so there is nothing "
                "to draw. See the message below.",
                icon="ℹ️",
            )

    if not outcome.ok:
        if outcome.unavailable:
            st.error(f"**{outcome.error_title}**\n\n{outcome.error_message}")
            render_setup_help(spec)
        else:
            st.error(f"**{outcome.error_title}**\n\n{outcome.error_message}")
        return

    result = outcome.result
    assert result is not None  # guaranteed by outcome.ok

    st.divider()
    render_summary_metrics(result, spec)
    render_no_detections_note(result)
    render_detection_table(result)

    if outcome.processed is not None:
        render_download_button(outcome.processed, uploaded.name)

    record_run_once(
        st.session_state,
        DetectionRun(
            source="upload",
            filename=uploaded.name,
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
            uploaded.name,
            len(uploaded.getvalue()),
            round(confidence, 2),
            round(iou, 2),
            result.count,
        ),
    )
    st.caption("This run has been added to the session statistics on the Dashboard.")
