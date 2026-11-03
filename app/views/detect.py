"""Detect — the primary workflow: upload, analyse, review, download.

The image is the largest object on the page. It is mounted like a print, captioned
with real facts about the file (name, frame, size), and the controls sit beside it
rather than above it. Nothing technical appears here; if analysis cannot run, the
page says so in one plain sentence and the cause goes to the developer page.
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
from app.ui.components import caption_strip, meta, note, page_header
from app.ui.theme import inject_theme

__all__ = ["render"]


def _kilobytes(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, round(size / 1024))} KB"


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

    plate_column, controls_column = st.columns([7, 5], gap="large")

    with plate_column:
        st.image(image, width="stretch", alt=f"The uploaded image, {uploaded.name}")

    with controls_column:
        caption_strip(
            [
                ("File", uploaded.name),
                ("Frame", f"{image.width} × {image.height}"),
                ("Size", _kilobytes(len(data))),
            ]
        )
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
