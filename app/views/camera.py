"""Camera — a browser snapshot analysed exactly like an upload.

Snapshot only. Continuous video would need a WebRTC component and reachable
STUN/TURN servers, so it is deliberately out of scope and never claimed.

The layout mirrors Detect: capture on the left, result on the right, one explicit
*Analyse snapshot* action.
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
    decode_image,
    image_facts,
)
from app.ui.components import card, meta, note, page_header
from app.ui.theme import inject_theme

__all__ = ["render"]

NAMESPACE = "camera_analysis"


def _summary(record: dict[str, Any] | None) -> str:
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
        page_header("Camera", "Take a snapshot and analyse it the same way as an upload.")
    with controls:
        confidence, iou = parameters()

    image_column, result_column = st.columns([1.18, 1], gap="medium", wrap=True)

    filename = "camera_snapshot.png"
    model_name = spec.display_name if spec is not None else "model unavailable"
    record: dict[str, Any] | None = None

    with image_column:
        with card(title="Snapshot", note="One still frame"):
            snapshot = st.camera_input(
                "Take a snapshot",
                help="Your browser will ask for camera access.",
                label_visibility="collapsed",
            )
            meta("One still frame per capture. Live video is not analysed.")

            if snapshot is not None:
                data = snapshot.getvalue()
                image = decode_image(data)
                if image is None:
                    note(UNREADABLE_MESSAGE, tone="warn")
                else:
                    st.image(image, width="stretch", alt="The snapshot you just took")
                    meta(f"{image_facts(image, filename)}", mono=True)
                    if spec is None or model_error:
                        note(UNAVAILABLE_MESSAGE, tone="warn")
                    else:
                        record = analyse_controls(
                            namespace=NAMESPACE,
                            source="camera",
                            image=image,
                            filename=filename,
                            data_length=len(data),
                            spec=spec,
                            confidence=confidence,
                            iou=iou,
                            button_label="Analyse snapshot",
                        )

    with result_column:
        with card(title="Results", note=_summary(record)):
            render_result_panel(record=record, filename=filename, model_name=model_name)
