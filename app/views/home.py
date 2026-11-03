"""Home — landing page and default route.

Editorial rather than promotional: one headline, one sentence, one primary action,
a small honest illustration, a single line about the flow and a footer. No badges,
no feature grid, no invented results.
"""

from __future__ import annotations

import streamlit as st

from app.ui.components import display_headline, footer, workflow_line
from app.ui.theme import PALETTE, inject_theme

__all__ = ["render"]

HEADLINE = "See exactly what the model sees."
INTRO = (
    "Upload a photo or take a snapshot and JUDEtector returns an annotated copy, the "
    "number of detections and a confidence score for each one."
)
WORKFLOW = "Upload or capture, analyse, then download the annotated image."

_ART_WIDTH = 256
_ART_HEIGHT = 160


def _page(key: str):
    """Resolve a navigation page lazily (nav imports this module)."""
    from app.ui.nav import page_for

    return page_for(key)


def render() -> None:
    inject_theme()

    copy_column, specimen_column = st.columns([1.2, 1], gap="large")

    with copy_column:
        display_headline(HEADLINE, INTRO)
        if st.button("Analyse an image", type="primary"):
            st.switch_page(_page("detect"))
        st.page_link(_page("camera"), label="Use the camera instead", icon=None)

    with specimen_column:
        _specimen()

    workflow_line(WORKFLOW)

    footer(
        "Images are processed in memory and never stored. Detection is not recognition.",
        page=_page("help"),
        page_label="Help",
    )


def _specimen() -> None:
    """A drawn panel showing what an annotation overlay looks like.

    Illustrative only: the caption says so, and the drawing carries no score,
    count or timing.
    """
    st.markdown(
        '<div class="jd-specimen">'
        f'<div class="jd-specimen__art">{_artwork()}</div>'
        '<p class="jd-specimen__note">Illustration, not a detection result.</p>'
        "</div>",
        unsafe_allow_html=True,
    )


def _artwork() -> str:
    """Head-and-shoulders figure with a detection outline, drawn from tokens."""
    return (
        f'<svg viewBox="0 0 {_ART_WIDTH} {_ART_HEIGHT}" aria-hidden="true" focusable="false">'
        f'<rect width="{_ART_WIDTH}" height="{_ART_HEIGHT}" fill="{PALETTE["art_canvas"]}"/>'
        f'<circle cx="128" cy="62" r="24" fill="{PALETTE["art_shape"]}"/>'
        f'<path d="M92 160c0-20 16-36 36-36s36 16 36 36Z" fill="{PALETTE["art_shape"]}"/>'
        f'<rect x="98" y="32" width="60" height="58" rx="10" fill="none" '
        f'stroke="{PALETTE["accent"]}" stroke-width="2.5"/>'
        "</svg>"
    )
