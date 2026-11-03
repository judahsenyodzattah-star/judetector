"""Overview: the product landing workspace."""

from __future__ import annotations

import streamlit as st

from app.components.model_sidebar import current_model
from app.components.status import render_scope_warning, render_setup_help
from app.core.stats import get_runs, runs_to_records, summarise
from app.ui.components import (
    empty_state,
    note,
    page_header,
    panel,
    section,
    tiles,
)
from app.ui.theme import inject_theme

__all__ = ["render"]

_CAPABILITIES = [
    (
        "image",
        "Image detection",
        "Upload a still image and get bounding boxes, a detection count and a confidence score for each result.",
    ),
    (
        "camera",
        "Camera capture",
        "Take a browser snapshot and run the same pipeline. Single frames per capture, not live video.",
    ),
    (
        "sliders",
        "Threshold control",
        "Adjust confidence and IoU per analysis. Lowering the threshold surfaces weaker candidates.",
    ),
    (
        "download",
        "Annotated export",
        "Download the processed image as a PNG, with boxes and labels already drawn.",
    ),
    (
        "chart",
        "Session analytics",
        "Review recorded evaluation results and this session's detection activity in one place.",
    ),
    (
        "shirt-shield",
        "In-memory processing",
        "Images are processed for the request only. Nothing is written to disk or retained.",
    ),
]


def _kv_markup(items: list[tuple[str, str]]) -> str:
    """Key/value strip markup for use inside a panel."""
    from html import escape

    return '<div class="jd-kv">' + "".join(
        f'<div class="jd-kv__item">{escape(label)}<b>{escape(value)}</b></div>'
        for label, value in items
    ) + "</div>"


def _navigate(page_key: str) -> None:
    # Imported lazily: `app.ui.nav` imports the views, so a module-level import here
    # would be circular.
    from app.ui.nav import PAGE

    st.switch_page(PAGE[page_key])


def render() -> None:
    inject_theme()

    spec, model_error = current_model()
    runs = get_runs(st.session_state)
    summary = summarise(runs)
    connected = bool(spec is not None and spec.weights_present)

    page_header(
        "Overview",
        "Run the connected detection model over images and camera snapshots, then "
        "review confidence scores and session activity.",
        eyebrow="Workspace",
        status=("Model connected", "ok") if connected else ("Model not connected", "warn"),
    )

    primary, secondary, _ = st.columns([1.05, 1, 1.7], gap="small")
    with primary:
        if st.button(
            "Upload an image",
            type="primary",
            width="stretch",
            icon=":material/upload:",
        ):
            _navigate("detect")
    with secondary:
        if st.button("Open camera", width="stretch", icon=":material/photo_camera:"):
            _navigate("camera")

    section("Model status", "The detector currently wired into the workspace.")
    if model_error:
        note(model_error, tone="warn", icon="alert-circle")
    elif spec is not None:
        panel(
            _kv_markup(
                [
                    ("Model", spec.display_name),
                    ("Classes", ", ".join(spec.declared_labels) or "—"),
                    ("Weights", "Connected" if spec.weights_present else "Not connected"),
                    ("Runs this session", str(summary.total_runs)),
                ]
            )
        )
        if not connected:
            note(
                "Detection is unavailable until weights are connected. Navigation and "
                "image upload remain active.",
                icon="info",
            )
            render_setup_help(spec)
        render_scope_warning(spec)
    else:
        empty_state(
            icon="cpu",
            title="No model configured",
            body="Register a detector in config/models.json to enable detection.",
        )

    section("Capabilities", "What the workspace does today.")
    tiles(_CAPABILITIES)

    section("Recent activity", "Detections run in this browser session.")
    if not runs:
        empty_state(
            icon="activity",
            title="No detections yet",
            body="Analysed images will be listed here and summarised in Analytics.",
        )
    else:
        st.dataframe(
            runs_to_records(runs[-6:]),
            hide_index=True,
            width="stretch",
        )
