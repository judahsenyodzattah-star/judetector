"""Camera — a browser snapshot analysed exactly like an upload.

Snapshot only. Continuous video would need a WebRTC component and reachable
STUN/TURN servers, so it is deliberately out of scope and never claimed.
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
from app.ui.components import caption_strip, meta, note, page_header
from app.ui.theme import inject_theme

__all__ = ["render"]


def render() -> None:
    inject_theme()

    page_header("Camera", "Take a snapshot and analyse it the same way as an upload.")

    spec, model_error = current_model()

    snapshot = st.camera_input(
        "Take a snapshot", help="Your browser will ask for camera access."
    )
    meta("One still frame per capture. Live video is not analysed.")

    if snapshot is None:
        return

    data = snapshot.getvalue()
    image = decode_image(data)
    if image is None:
        note(UNREADABLE_MESSAGE, tone="warn")
        return

    plate_column, controls_column = st.columns([7, 5], gap="large")
    with plate_column:
        st.image(image, width="stretch", alt="The snapshot you just took")

    with controls_column:
        caption_strip(
            [
                ("Source", "Camera"),
                ("Frame", f"{image.width} × {image.height}"),
            ]
        )
        if spec is None or model_error:
            note(UNAVAILABLE_MESSAGE, tone="warn")
            return
        confidence, iou = advanced_settings()

    analysis_workspace(
        namespace="camera_analysis",
        source="camera",
        data=data,
        filename="camera_snapshot.png",
        image=image,
        spec=spec,
        confidence=confidence,
        iou=iou,
        button_label="Analyse snapshot",
    )
