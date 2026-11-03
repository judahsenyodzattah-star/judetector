"""Detect — the primary end-user workflow: upload, analyse, review, download.

Nothing technical appears here. If analysis cannot run, the page says so in one
plain sentence; the technical cause goes to the developer page instead.
"""

from __future__ import annotations

import streamlit as st

from app.components.settings import advanced_settings, current_model
from app.components.workflow import (
    UNAVAILABLE_MESSAGE,
    UNREADABLE_MESSAGE,
    analysis_workspace,
    decode_image,
)
from app.core import config
from app.core.image_io import describe_image
from app.ui.components import meta, note, page_header
from app.ui.theme import inject_theme

__all__ = ["render"]


def render() -> None:
    inject_theme()

    page_header("Detect", "Upload an image to analyse it.")

    spec, model_error = current_model()

    uploaded = st.file_uploader(
        "Image file",
        type=list(config.SUPPORTED_IMAGE_TYPES),
        help=None,
    )

    if uploaded is None:
        meta(f"JPG, PNG, WEBP or BMP · up to {config.MAX_UPLOAD_MB} MB")
        return

    data = uploaded.getvalue()
    image = decode_image(data)
    if image is None:
        note(UNREADABLE_MESSAGE, tone="warn")
        return

    st.image(image, width=380)
    meta(f"{uploaded.name} · {describe_image(image)}")

    if spec is None or model_error:
        # A registry/config problem is a developer concern: the user gets one line.
        note(UNAVAILABLE_MESSAGE, tone="warn")
        return

    confidence, iou = advanced_settings()
    analysis_workspace(
        namespace="detect_analysis",
        source="upload",
        data=data,
        filename=uploaded.name,
        image=image,
        spec=spec,
        confidence=confidence,
        iou=iou,
        button_label="Analyse image",
    )
