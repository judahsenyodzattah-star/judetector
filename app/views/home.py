"""Home — the landing page and default route.

Deliberately short: hero, two calls to action, one illustrative preview of the
original/annotated relationship, three steps, and a privacy footer. No feature
grids, no documentation, and nothing that looks like measured model output.

The preview is a drawn diagram, labelled as such — it is not a captured result and
carries no confidence score, count or timing.
"""

from __future__ import annotations

import streamlit as st

from app.ui.components import footer, hero, section, steps
from app.ui.icons import ICON_UI, svg
from app.ui.theme import PALETTE, inject_theme

__all__ = ["render"]

EYEBROW = "IMAGE ANALYSIS, SIMPLIFIED"
HEADLINE = "A clearer way to explore your images."
LEDE = (
    "Upload a photo, analyse it with the configured detection model, and see the "
    "results in a simple visual workspace."
)

HOW_IT_WORKS = (
    (
        "upload",
        "Upload or capture an image",
        "Choose a file from your device, or take a snapshot with your camera.",
    ),
    (
        "scan",
        "Analyse the image",
        "Press Analyse image and the connected model marks what it finds.",
    ),
    (
        "download",
        "Review and download",
        "Compare the annotated and original images, then download if you need to.",
    ),
)

# Illustration geometry: a subject drawn as a head and shoulders on a warm field,
# with the same subject framed by a detection box in the second panel.
_ART_WIDTH = 256
_ART_HEIGHT = 160


def _page(key: str):
    """Resolve a navigation page lazily (nav imports this module)."""
    from app.ui.nav import page_for

    return page_for(key)


def render() -> None:
    inject_theme()

    hero(HEADLINE, LEDE, eyebrow=EYEBROW, eyebrow_icon="scan")
    _cta_row()
    _preview()

    section("How it works")
    steps(HOW_IT_WORKS, grid=True)

    footer(
        "Images are processed in memory and never stored. Detection is not recognition.",
        page=_page("help"),
        page_label="Help",
    )


def _cta_row() -> None:
    """Primary and secondary calls to action, side by side then stacked on mobile."""
    primary_column, secondary_column, _ = st.columns([1, 1, 2], gap="small")
    if primary_column.button("Start detecting", type="primary", width="stretch"):
        st.switch_page(_page("detect"))
    if secondary_column.button("Try camera", width="stretch"):
        st.switch_page(_page("camera"))


def _preview() -> None:
    """Illustrative original → annotated composition, drawn rather than captured."""
    st.markdown(
        '<div class="jd-preview" role="group" aria-label="Illustrative preview of an original and analysed image">'
        '<div class="jd-preview__stage">'
        '<div class="jd-preview__panel">'
        f'<div class="jd-preview__art">{_artwork(boxed=False)}</div>'
        '<span class="jd-preview__label">Original</span>'
        "</div>"
        f'<div class="jd-preview__arrow">{svg("arrow-right", ICON_UI)}</div>'
        '<div class="jd-preview__panel">'
        f'<div class="jd-preview__art">{_artwork(boxed=True)}</div>'
        '<span class="jd-preview__label">Analysed</span>'
        "</div>"
        "</div>"
        '<p class="jd-preview__note">Illustrative preview — not model output.</p>'
        "</div>",
        unsafe_allow_html=True,
    )


def _artwork(*, boxed: bool) -> str:
    """Return the illustration; `boxed` adds the detection outline.

    Decorative: the surrounding panel labels carry the meaning, so the SVG is
    hidden from assistive technology rather than described twice.
    """
    box = (
        '<rect x="98" y="32" width="60" height="58" rx="10" fill="none" '
        f'stroke="{PALETTE["accent"]}" stroke-width="2.5"/>'
        if boxed
        else ""
    )
    return (
        f'<svg viewBox="0 0 {_ART_WIDTH} {_ART_HEIGHT}" aria-hidden="true" focusable="false">'
        f'<rect width="{_ART_WIDTH}" height="{_ART_HEIGHT}" fill="{PALETTE["art_canvas"]}"/>'
        f'<circle cx="128" cy="62" r="24" fill="{PALETTE["art_shape"]}"/>'
        f'<path d="M92 160c0-20 16-36 36-36s36 16 36 36Z" fill="{PALETTE["art_shape"]}"/>'
        f"{box}"
        "</svg>"
    )
