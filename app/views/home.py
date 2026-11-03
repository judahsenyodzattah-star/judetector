"""Home — the proof sheet, and the default route.

Composition rather than effects: a headline, one supporting sentence, one primary
action, then the same specimen mounted twice — once as captured, once with the
marking the model would draw. The pair is the product's subject, so it is the
primary visual element of the page.

Both plates are drawn from the same markup; the annotated plate differs only by the
single marking rectangle. Nothing on this page is a measurement, and the caption
says so.
"""

from __future__ import annotations

import streamlit as st

from app.ui.components import display_headline, flow_line, footer, plate
from app.ui.theme import PALETTE, inject_theme

__all__ = ["render", "specimen_svg"]

HEADLINE = "See exactly what the model sees."
INTRO = (
    "Upload an image or take a snapshot, and the annotated copy comes back with the "
    "detection count and a confidence score for each match."
)
FLOW = ("Upload or capture", "Analyse", "Review", "Download")
ILLUSTRATION_NOTE = "Illustration, not an actual detection result."

_PLATE_WIDTH = 320
_PLATE_HEIGHT = 200


def _page(key: str):
    """Resolve a navigation page lazily (nav imports this module)."""
    from app.ui.nav import page_for

    return page_for(key)


def render() -> None:
    inject_theme()

    display_headline(HEADLINE, INTRO)

    action_column, link_column, _ = st.columns([1, 1, 1.4], vertical_alignment="center")
    with action_column:
        if st.button("Analyse an image", type="primary"):
            st.switch_page(_page("detect"))
    with link_column:
        st.page_link(_page("camera"), label="Use the camera instead", icon=None)

    original_column, annotated_column = st.columns(2, gap="medium")
    with original_column:
        plate(specimen_svg(annotated=False), label="Original")
    with annotated_column:
        plate(specimen_svg(annotated=True), label="Annotated")

    st.caption(ILLUSTRATION_NOTE)

    flow_line(FLOW)

    footer(
        "Images are processed in memory and never stored. Detection is not recognition.",
        page=_page("help"),
        page_label="Help",
    )


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
