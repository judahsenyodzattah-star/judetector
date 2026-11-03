"""Reusable interface primitives.

Every page composes these instead of hand-rolling markup, which is what keeps the
visual language consistent. Any dynamic value interpolated into HTML is escaped;
the only unescaped content is the trusted static icon markup from `app.ui.icons`.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from app.ui.icons import ICON_INLINE, ICON_UI, svg

__all__ = [
    "PILL_TONES",
    "bullets",
    "empty_state",
    "footer",
    "hero",
    "kv_row",
    "meta",
    "note",
    "page_header",
    "section",
    "status_pill",
    "steps",
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
    """Page title block: optional eyebrow, title, one-line subtitle."""
    pill = f"<div>{status_pill(*status)}</div>" if status else ""
    subtitle_html = f'<p class="jd-sub">{escape(subtitle)}</p>' if subtitle else ""
    eyebrow_html = (
        f'<div class="jd-eyebrow">{svg(eyebrow_icon, ICON_INLINE)}{escape(eyebrow)}</div>'
        if eyebrow
        else ""
    )
    _html(
        '<div class="jd-head">'
        '<div class="jd-head-row">'
        "<div>"
        f"{eyebrow_html}"
        f'<h1 class="jd-h1">{escape(title)}</h1>'
        f"{subtitle_html}"
        "</div>"
        f"{pill}"
        "</div>"
        "</div>"
    )


def hero(
    title: str,
    lede: str,
    *,
    eyebrow: str,
    eyebrow_icon: str = "scan",
) -> None:
    """Landing-page hero: small eyebrow, large headline, one supporting line."""
    _html(
        '<div class="jd-hero">'
        f'<div class="jd-hero__eyebrow">{svg(eyebrow_icon, ICON_INLINE)}{escape(eyebrow)}</div>'
        f'<h1 class="jd-hero__title">{escape(title)}</h1>'
        f'<p class="jd-hero__lede">{escape(lede)}</p>'
        "</div>"
    )


def section(title: str, subtitle: str | None = None) -> None:
    """Section divider with an optional short caption."""
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
    _html(
        f'<div class="jd-note {tone_css}">{svg(icon, ICON_INLINE)}<div>{escape(text)}</div></div>'
    )


def empty_state(*, icon: str, title: str, body: str) -> None:
    """Purposeful empty state: says what is missing and what to do next."""
    _html(
        '<div class="jd-empty">'
        f'<div class="jd-empty__icon">{svg(icon, ICON_UI)}</div>'
        f'<p class="jd-empty__title">{escape(title)}</p>'
        f'<p class="jd-empty__body">{escape(body)}</p>'
        "</div>"
    )


def steps(
    items: Sequence[tuple[str, str, str]],
    *,
    grid: bool = False,
) -> None:
    """Ordered ``(icon, title, body)`` steps.

    ``grid=True`` lays them out horizontally for the landing page; the default is a
    vertical list for reference-style pages.
    """
    rendered = "".join(
        '<div class="jd-step">'
        f'<div class="jd-step__num">{index}</div>'
        f'<div class="jd-step__body"><b>{escape(title)}</b>'
        f"<span>{escape(body)}</span></div>"
        f'<div class="jd-step__icon">{svg(icon_name, ICON_UI)}</div>'
        "</div>"
        for index, (icon_name, title, body) in enumerate(items, start=1)
    )
    layout = "jd-steps jd-steps--grid" if grid else "jd-steps"
    _html(f'<div class="{layout}">{rendered}</div>')


def bullets(items: Sequence[str]) -> None:
    """Tight bulleted list for limitations and privacy notes."""
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


# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
def footer(note: str, *, page, page_label: str = "Help") -> None:
    """Minimal branded footer: wordmark, one privacy line, one page link.

    The link is rendered with `st.page_link`, so it is a real anchor — keyboard
    accessible and routable — rather than raw HTML.
    """
    body = (
        '<div class="jd-footer">'
        f'<div class="jd-footer__brand"><span class="jd-footer__mark">{svg("scan", ICON_INLINE)}'
        "</span>JUDEtector</div>"
        f'<p class="jd-footer__note">{escape(note)}</p>'
        "</div>"
    )
    text_column, link_column = st.columns([5, 1], gap="small", vertical_alignment="center")
    with text_column:
        _html(body)
    with link_column:
        st.page_link(page, label=page_label, icon=None)
