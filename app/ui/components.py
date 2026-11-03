"""Reusable interface primitives.

The vocabulary here is intentionally small: a page header, an editorial headline,
a section label, a note, an empty state, ordered steps, key/value rows and a
footer. No icon set, no cards, no pills. Hierarchy comes from type, alignment and
hairline rules, which is what keeps the pages feeling like one product.

Any dynamic value interpolated into HTML is escaped.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

__all__ = [
    "bullets",
    "display_headline",
    "empty_state",
    "footer",
    "kv_row",
    "meta",
    "note",
    "page_header",
    "section",
    "steps",
    "workflow_line",
]


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Headings
# --------------------------------------------------------------------------
def page_header(title: str, subtitle: str | None = None) -> None:
    """Page title plus one supporting line."""
    subtitle_html = f'<p class="jd-sub">{escape(subtitle)}</p>' if subtitle else ""
    _html(
        '<div class="jd-head">'
        f'<h1 class="jd-h1">{escape(title)}</h1>'
        f"{subtitle_html}"
        "</div>"
    )


def display_headline(title: str, intro: str) -> None:
    """Landing-page headline with a single supporting sentence."""
    _html(
        f'<h1 class="jd-display">{escape(title)}</h1>'
        f'<p class="jd-intro">{escape(intro)}</p>'
    )


def section(title: str, subtitle: str | None = None) -> None:
    """Section label: hairline rule and small caps. Replaces card headers."""
    sub = f'<p class="jd-section__sub">{escape(subtitle)}</p>' if subtitle else ""
    _html(
        f'<div class="jd-section"><p class="jd-section__title">{escape(title)}</p>{sub}</div>'
    )


# --------------------------------------------------------------------------
# Text pieces
# --------------------------------------------------------------------------
def note(text: str, *, tone: str = "info") -> None:
    """Quiet inline notice: a rule and a sentence, never a banner."""
    tone_css = {"warn": "jd-note--warn", "ok": "jd-note--ok"}.get(tone, "")
    _html(f'<div class="jd-note {tone_css}">{escape(text)}</div>')


def empty_state(*, title: str, body: str) -> None:
    """Left-aligned statement of what is missing and what to do next."""
    _html(
        '<div class="jd-empty">'
        f'<p class="jd-empty__title">{escape(title)}</p>'
        f'<p class="jd-empty__body">{escape(body)}</p>'
        "</div>"
    )


def steps(items: Sequence[tuple[str, str]]) -> None:
    """Ordered ``(title, body)`` steps as a numbered text list."""
    rendered = "".join(
        '<div class="jd-step">'
        f'<div class="jd-step__num">{index}</div>'
        f'<div class="jd-step__body"><b>{escape(title)}</b><span>{escape(body)}</span></div>'
        "</div>"
        for index, (title, body) in enumerate(items, start=1)
    )
    _html(f'<div class="jd-steps">{rendered}</div>')


def bullets(items: Sequence[str]) -> None:
    """Tight bulleted list for limits and privacy notes."""
    rendered = "".join(f"<li>{escape(item)}</li>" for item in items)
    _html(f'<ul class="jd-list">{rendered}</ul>')


def kv_row(items: Sequence[tuple[str, str]]) -> None:
    """Key/value strip (label above value) for technical readouts."""
    rendered = "".join(
        f'<div class="jd-kv__item">{escape(label)}<b>{escape(value)}</b></div>'
        for label, value in items
    )
    _html(f'<div class="jd-kv">{rendered}</div>')


def meta(text: str) -> None:
    """Dim single line of context under a component."""
    _html(f'<p class="jd-meta">{escape(text)}</p>')


def workflow_line(text: str) -> None:
    """One-line description of the flow, used under the landing fold."""
    _html(f'<p class="jd-workflow">{escape(text)}</p>')


# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
def footer(note: str, *, page, page_label: str = "Help") -> None:
    """Single-row footer: wordmark, one privacy line, one real page link.

    The link is rendered with `st.page_link`, so it is a genuine anchor rather than
    raw HTML.
    """
    text_column, link_column = st.columns([5, 1], gap="small", vertical_alignment="center")
    with text_column:
        _html(
            '<div class="jd-footer">'
            '<p class="jd-footer__brand">JUDEtector</p>'
            f'<p class="jd-footer__note">{escape(note)}</p>'
            "</div>"
        )
    with link_column:
        st.page_link(page, label=page_label, icon=None)
