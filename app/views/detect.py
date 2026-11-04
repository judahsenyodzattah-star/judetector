"""Detect — the primary workspace: choose → analyse → review → download.

Two panels are always present. The image and its controls sit on the left; the result
sits on the right, so the outcome appears beside the thing that produced it instead of
below a long scroll. Analysis is explicit: only *Analyse image* runs the model.

Nothing technical appears here. If analysis cannot run, the page says so in one plain
sentence and the cause goes to the developer page.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.components.results import format_ms, render_result_panel
from app.components.settings import current_model, parameters
from app.components.workflow import (
    UNAVAILABLE_MESSAGE,
    UNREADABLE_MESSAGE,
    analyse_controls,
    clear_pending,
    decode_image,
    image_facts,
    pending_image,
)
from app.core import config
from app.ui.components import card, meta, note, page_header
from app.ui.theme import inject_theme

__all__ = ["render"]

NAMESPACE = "detect_analysis"
UPLOAD_KEY = "detect_upload"


def _page(key: str):
    """Resolve a navigation page lazily (nav imports this module)."""
    from app.ui.nav import page_for

    return page_for(key)


def _clear_source() -> None:
    """Callback: drop both the staged handoff and the uploader's own file."""
    clear_pending()
    st.session_state.pop(UPLOAD_KEY, None)


def _kilobytes(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, round(size / 1024))} KB"


def _summary(record: dict[str, Any] | None) -> str:
    """The one-line state of the result panel: analysis state, never a placeholder."""
    if record is None:
        return "Not analysed yet"
    outcome = record.get("outcome")
    if outcome is None or not outcome.ok or outcome.result is None:
        return "Unavailable"
    result = outcome.result
    noun = "detection" if result.count == 1 else "detections"
    total = record.get("total_ms")
    summary = f"{result.count} {noun}"
    if isinstance(total, (int, float)) and total > 0:
        summary += f" · {format_ms(total)}"
    return summary


def render() -> None:
    inject_theme()

    spec, model_error = current_model()

    heading, controls = st.columns([5, 1], gap="small", vertical_alignment="center")
    with heading:
        page_header(
            "Detect",
            "Choose an image, check the thresholds if you need to, then analyse it.",
        )
    with controls:
        confidence, iou = parameters()

    image_column, result_column = st.columns([1.18, 1], gap="medium", wrap=True)

    filename = "image"
    model_name = spec.display_name if spec is not None else "model unavailable"
    record: dict[str, Any] | None = None
    staged_image = pending_image()

    with image_column:
        with card(title="Image", note="One image per analysis"):
            uploaded = st.file_uploader(
                "Image file",
                type=list(config.SUPPORTED_IMAGE_TYPES),
                key=UPLOAD_KEY,
                label_visibility="collapsed",
            )

            source: tuple[bytes, str] | None = None
            if uploaded is not None:
                source = (uploaded.getvalue(), uploaded.name)
            elif staged_image is not None:
                source = staged_image

            if source is None:
                # The uploader states the accepted formats and size limit natively;
                # repeating them here would be a second instruction line.
                st.page_link(
                    _page("camera"),
                    label="Use the camera instead",
                    icon=":material/photo_camera:",
                )
            else:
                data, filename = source
                image = decode_image(data)
                if image is None:
                    note(UNREADABLE_MESSAGE, tone="warn")
                else:
                    st.image(image, width="stretch", alt=f"The image to analyse, {filename}")
                    meta(
                        f"{image_facts(image, filename)} · {_kilobytes(len(data))}",
                        mono=True,
                    )
                    if spec is None or model_error:
                        # A registry/config problem is a developer concern: the user
                        # gets one line, and no button that cannot work.
                        note(UNAVAILABLE_MESSAGE, tone="warn")
                    else:
                        record = analyse_controls(
                            namespace=NAMESPACE,
                            source="upload",
                            image=image,
                            filename=filename,
                            data=data,
                            spec=spec,
                            confidence=confidence,
                            iou=iou,
                        )
                    if uploaded is None and staged_image is not None:
                        st.button(
                            "Clear image",
                            type="tertiary",
                            on_click=_clear_source,
                            help="Remove the image staged on Home",
                        )

    with result_column:
        with card(title="Results", note=_summary(record)):
            render_result_panel(record=record, filename=filename, model_name=model_name)
