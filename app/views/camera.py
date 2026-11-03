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
from app.ui.components import empty_state, meta, note, page_header
from app.ui.theme import inject_theme

__all__ = ["render"]


def render() -> None:
    inject_theme()

    page_header(
        "Camera",
        "Take a snapshot with your camera and analyse it the same way as an upload.",
        eyebrow="",
    )

    spec, model_error = current_model()
    confidence, iou = advanced_settings()

    snapshot = st.camera_input("Take a snapshot", help="Your browser will ask for camera access.")

    if snapshot is None:
        empty_state(
            icon="camera",
            title="No snapshot yet",
            body="Allow camera access and take a photo. One still frame is captured "
            "each time — live video is not analysed.",
        )
        return

    data = snapshot.getvalue()
    image = decode_image(data)
    if image is None:
        note(UNREADABLE_MESSAGE, tone="warn", icon="alert-circle")
        return

    if spec is None or model_error:
        note(UNAVAILABLE_MESSAGE, tone="warn", icon="alert-circle")
        return

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
    meta("Single-frame capture. Continuous live detection is not supported.")
