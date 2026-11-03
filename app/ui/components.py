"""Reusable interface primitives.

Every page composes these instead of hand-rolling markup, which is what keeps the
visual language consistent. Any dynamic value interpolated into HTML is escaped;
the only unescaped content is the trusted static icon markup from `app.ui.icons`.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from app.ui.icons import svg

__all__ = [
    "PILL_TONES",
    "bullets",
    "panel",
    "empty_state",
    "kv_row",
    "meta",
    "note",
    "page_header",
    "section",
    "spacer",
    "status_pill",
    "tiles",
]

PILL_TONES = {"ok": "jd-pill--ok", "warn": "jd-pill--warn", "muted": "jd-pill--muted"}


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
def page_header(
    title: str,
    subtitle: str | None = None,
    *,
    eyebrow: str = "JUDEtector",
    eyebrow_icon: str = "scan",
    status: tuple[str, str] | None = None,
) -> None:
    """Page title block: eyebrow, title, one-line subtitle, optional status pill."""
    pill = f"<div>{status_pill(*status)}</div>" if status else ""
    subtitle_html = f'<p class="jd-sub">{escape(subtitle)}</p>' if subtitle else ""
    _html(
        '<div class="jd-head">'
        '<div class="jd-head-row">'
        "<div>"
        f'<div class="jd-eyebrow">{svg(eyebrow_icon, 13)}{escape(eyebrow)}</div>'
        f'<h1 class="jd-h1">{escape(title)}</h1>'
        f"{subtitle_html}"
        "</div>"
        f"{pill}"
        "</div>"
        "</div>"
    )


def section(title: str, subtitle: str | None = None) -> None:
    """Section divider with a short caption."""
    sub = f'<p class="jd-section__sub">{escape(subtitle)}</p>' if subtitle else ""
    _html(
        f'<div class="jd-section"><p class="jd-section__title">{escape(title)}</p>{sub}</div>'
    )


# --------------------------------------------------------------------------
# Small pieces
# --------------------------------------------------------------------------
def status_pill(label: str, tone: str = "muted") -> str:
    """Return the HTML for a status pill (`ok`, `warn`, `muted`)."""
    css = PILL_TONES.get(tone, PILL_TONES["muted"])
    return (
        f'<span class="jd-pill {css}"><span class="jd-pill__dot"></span>{escape(label)}</span>'
    )


def note(text: str, *, tone: str = "info", icon: str = "info") -> None:
    """Compact inline notice. Used instead of full-width alert banners."""
    tone_css = {"warn": "jd-note--warn", "ok": "jd-note--ok"}.get(tone, "")
    _html(f'<div class="jd-note {tone_css}">{svg(icon, 15)}<div>{escape(text)}</div></div>')


def empty_state(*, icon: str, title: str, body: str) -> None:
    """Purposeful empty state: says what is missing and why it is empty."""
    _html(
        '<div class="jd-empty">'
        f'<div class="jd-empty__icon">{svg(icon, 17)}</div>'
        f'<p class="jd-empty__title">{escape(title)}</p>'
        f'<p class="jd-empty__body">{escape(body)}</p>'
        "</div>"
    )


def tiles(items: Sequence[tuple[str, str, str]]) -> None:
    """Responsive grid of (icon, title, body) capability tiles."""
    cards = "".join(
        '<div class="jd-tile">'
        f'<div class="jd-tile__icon">{svg(icon_name, 17)}</div>'
        f'<p class="jd-tile__title">{escape(title)}</p>'
        f'<p class="jd-tile__body">{escape(body)}</p>'
        "</div>"
        for icon_name, title, body in items
    )
    _html(f'<div class="jd-grid">{cards}</div>')


def bullets(items: Sequence[str]) -> None:
    """Tight bulleted list for limitations and capability summaries."""
    rendered = "".join(f"<li>{escape(item)}</li>" for item in items)
    _html(f'<ul class="jd-list">{rendered}</ul>')


def kv_row(items: Sequence[tuple[str, str]]) -> None:
    """Horizontal key/value strip (label above value)."""
    rendered = "".join(
        f'<div class="jd-kv__item">{escape(label)}<b>{escape(value)}</b></div>'
        for label, value in items
    )
    _html(f'<div class="jd-kv">{rendered}</div>')


def meta(text: str) -> None:
    """Dim single line of context under a component."""
    _html(f'<p class="jd-meta">{escape(text)}</p>')


def spacer(rem: float = 0.6) -> None:
    _html(f'<div style="height:{float(rem):.2f}rem"></div>')


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------
def panel(*parts: str) -> None:
    """Render pre-built markup inside a bordered panel.

    A plain HTML wrapper is used rather than `st.container(border=True)` because
    bordered-container internals differ between Streamlit releases; this keeps the
    card appearance stable.
    """
    _html(f'<div class="jd-panel">{"".join(parts)}</div>')
