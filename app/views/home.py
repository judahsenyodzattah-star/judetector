"""Home — the application entry point and default route.

The page answers one question — *how do I analyse an image?* — with a real control, not
a link disguised as marketing: choosing a file stages it and opens Detect, where the
explicit *Analyse image* action lives. Nothing is inferred here.

Around that: this session's real numbers (only once they exist), a compact account of
the three steps, and one small specimen plate that shows what a detection looks like.
The plate is secondary by design and captioned as an illustration.
"""

from __future__ import annotations

import streamlit as st

from app.components.workflow import remember_pending
from app.core import config
from app.core.stats import get_runs, summarise
from app.ui.components import card, empty_state, fact_strip, meta, page_header, specimen, steps
from app.ui.theme import PALETTE, inject_theme

__all__ = ["render", "specimen_svg"]

HOME_UPLOAD_KEY = "home_upload"

_PLATE_WIDTH = 320
_PLATE_HEIGHT = 200


def _page(key: str):
    """Resolve a navigation page lazily (nav imports this module)."""
    from app.ui.nav import page_for

    return page_for(key)


def _handoff() -> None:
    """Callback: stage the chosen file for Detect and open it.

    Runs before the page renders, so Detect receives the image already in place. It
    stores bytes only — it never runs the model.
    """
    uploaded = st.session_state.get(HOME_UPLOAD_KEY)
    if uploaded is None:
        return
    remember_pending(uploaded.getvalue(), uploaded.name)
    st.switch_page(_page("detect"))


def render() -> None:
    inject_theme()

    page_header(
        "Analyse an image",
        "Upload a photo or take a snapshot. JUDEtector marks what the model finds and "
        "reports the confidence for each detection.",
    )

    main_column, side_column = st.columns([1.55, 1], gap="medium", wrap=True)

    with main_column:
        with card(title="Start an analysis"):
            st.file_uploader(
                "Image file",
                type=list(config.SUPPORTED_IMAGE_TYPES),
                key=HOME_UPLOAD_KEY,
                on_change=_handoff,
                label_visibility="collapsed",
            )
            meta(
                f"JPG, PNG, WEBP or BMP · up to {config.MAX_UPLOAD_MB} MB. Choosing a file "
                "opens Detect with the image ready; analysis starts when you ask for it."
            )
            st.page_link(
                _page("camera"),
                label="Or take a snapshot with the camera",
                icon=":material/photo_camera:",
            )

        with card(title="How it works"):
            steps(
                [
                    ("Choose an image", "Upload a file here, or capture a frame on Camera."),
                    ("Analyse", "Review the thresholds, then select Analyse image."),
                    (
                        "Review and download",
                        "Check the marked image and each confidence, then download the PNG.",
                    ),
                ]
            )

    with side_column:
        _session_card()
        specimen(
            annotated=True,
            label="Illustration. Each outline marks one detection; the model reports "
            "its own count and confidences.",
        )


def _session_card() -> None:
    """Session figures, shown only for analyses that actually ran."""
    runs = get_runs(st.session_state)
    with card(title="This session"):
        if not runs:
            empty_state(
                title="No analyses yet",
                body="Counts and confidences from the analyses you run will be summarised here.",
            )
            return

        summary = summarise(runs)
        items = [
            ("Analyses", str(summary.total_runs)),
            ("Detections", str(summary.total_faces)),
        ]
        if summary.mean_confidence is not None:
            items.append(("Mean confidence", f"{summary.mean_confidence:.1%}"))
        fact_strip(items)
        meta("Recorded in this browser session only.")


def specimen_svg(*, annotated: bool) -> str:
    """The abstract specimen, drawn from palette tokens.

    `annotated=True` adds one marking rectangle in the marking colour and changes
    nothing else. No score, count or timing appears on the artwork, so it cannot be
    mistaken for a measurement.
    """
    marking = (
        f'<rect x="126" y="40" width="68" height="76" fill="none" '
        f'stroke="{PALETTE["mark"]}" stroke-width="3"/>'
        if annotated
        else ""
    )
    return (
        f'<svg viewBox="0 0 {_PLATE_WIDTH} {_PLATE_HEIGHT}" aria-hidden="true" '
        f'focusable="false">'
        f'<rect width="{_PLATE_WIDTH}" height="{_PLATE_HEIGHT}" '
        f'fill="{PALETTE["art_canvas"]}"/>'
        f'<circle cx="160" cy="76" r="28" fill="{PALETTE["art_shape"]}"/>'
        f'<path d="M118 200c0-24 19-44 42-44s42 20 42 44Z" '
        f'fill="{PALETTE["art_shape"]}"/>'
        f"{marking}"
        "</svg>"
    )
