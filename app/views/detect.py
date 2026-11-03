"""Detect: image upload workspace → detection → annotated result."""

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
from app.ui.components import empty_state, meta, note, page_header, section
from app.ui.theme import inject_theme

__all__ = ["render"]


def render() -> None:
    inject_theme()

    spec, confidence, iou, model_error = detection_settings()
    connected = bool(spec is not None and spec.weights_present)

    page_header(
        "Detect",
        "Upload an image and run the connected model over it. Results include boxes, "
        "per-detection confidence and a downloadable annotated file.",
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

    if not connected:
        note(
            "Detection is unavailable until model weights are connected. You can still "
            "preview an image.",
            icon="alert-circle",
            tone="warn",
        )

    uploaded = st.file_uploader(
        "Image file",
        type=list(config.SUPPORTED_IMAGE_TYPES),
        help=f"JPG, PNG, WEBP or BMP · max {config.MAX_UPLOAD_MB} MB. Processed in memory.",
    )

    if uploaded is None:
        empty_state(
            icon="image",
            title="No image selected",
            body="Drop an image above to run detection. Nothing is analysed or recorded "
            "until a file is provided.",
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
        note(
            f"Large image downscaled to {describe_image(image)} "
            f"(limit {config.MAX_IMAGE_DIMENSION} px).",
            icon="info",
        )

    detector = get_detector(spec)
    outcome = analyse_image(image, spec, detector, confidence=confidence, iou=iou)

    if not outcome.ok:
        st.error(f"**{outcome.error_title}**\n\n{outcome.error_message}")
        if outcome.unavailable:
            render_setup_help(spec)
        return

    result = outcome.result
    assert result is not None  # guaranteed by outcome.ok

    section("Results", f"{uploaded.name} · {describe_image(image)}")
    render_summary_metrics(result, spec)
    render_no_detections_note(result)

    original_column, processed_column = st.columns(2, gap="medium")
    with original_column:
        st.image(image, caption="Original", width="stretch")
    with processed_column:
        st.image(outcome.processed, caption="Annotated", width="stretch")

    if result.detections:
        section("Detections", "Sorted by confidence, with pixel coordinates.")
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
    meta("Added to this session's activity. Open Analytics for the aggregate view.")
