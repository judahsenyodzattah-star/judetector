"""Reusable interface primitives.

The vocabulary is deliberately small and readable: a page header, a card, a card
header, a fact strip, a detection list, an empty state, a note, steps, bullets and a
small specimen plate. Cards are Streamlit's own bordered containers, so they inherit
the theme's border, radius and background instead of being imitated with CSS.

Rules: no invented values (every number in a fact strip or detection row comes from a
measurement), monospace only for data, and any dynamic value interpolated into HTML is
escaped.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from html import escape
from typing import Any

import streamlit as st

__all__ = [
    "bullets",
    "card",
    "card_head",
    "detection_list",
    "empty_state",
    "fact_strip",
    "meta",
    "note",
    "page_header",
    "rail_status",
    "readout",
    "section",
    "specimen",
    "steps",
]


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Frame pieces
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


@contextmanager
def card(*, title: str | None = None, note: str | None = None) -> Iterator[None]:
    """A bordered card, optionally with a header line inside it.

    The border, radius and background come from `.streamlit/config.toml`, so the card
    looks the same as every native container in the app.
    """
    with st.container(border=True):
        if title or note:
            card_head(title or "", note=note)
        yield


def card_head(title: str, note: str | None = None) -> None:
    """Card title with an optional quiet note on the right."""
    note_html = f'<p class="jd-card__note">{escape(note)}</p>' if note else ""
    if not title:
        _html(f'<div class="jd-card__head">{note_html}</div>')
        return
    _html(
        '<div class="jd-card__head">'
        f'<p class="jd-card__title">{escape(title)}</p>'
        f"{note_html}"
        "</div>"
    )


def rail_status(label: str, *, state: str = "ready", detail: str | None = None) -> None:
    """Model state at the foot of the rail. Only ever reflects real resolution."""
    modifier = "jd-rail-status--ready" if state == "ready" else "jd-rail-status--unavailable"
    detail_html = f" · {escape(detail)}" if detail else ""
    _html(
        f'<div class="jd-rail-status {modifier}">'
        '<span class="jd-rail-status__dot"></span>'
        f"<span><b>{escape(label)}</b>{detail_html}</span>"
        "</div>"
    )


# --------------------------------------------------------------------------
# Data pieces
# --------------------------------------------------------------------------
def section(title: str, note_text: str | None = None) -> None:
    """Section heading with an optional quiet line. Used on the developer page."""
    note_html = f'<p class="jd-section__note">{escape(note_text)}</p>' if note_text else ""
    _html(
        f'<h2 class="jd-section">{escape(title)}</h2>'
        f"{note_html}"
    )


def readout(items: Sequence[tuple[str, str]]) -> None:
    """Aligned label/value list for diagnostics: labels left, mono values right."""
    rows = "".join(
        f'<div class="jd-readout__row"><span>{escape(label)}</span>'
        f'<b>{escape(value)}</b></div>'
        for label, value in items
    )
    _html(f'<div class="jd-readout">{rows}</div>')


def fact_strip(items: Sequence[tuple[str, str]]) -> None:
    """Compact strip of measured facts. One metric per entry, no filler tiles."""
    if not items:
        return
    columns = st.columns(len(items), gap="small", wrap=True)
    for column, (label, value) in zip(columns, items):
        with column:
            st.metric(label, value, border=False)


def detection_list(records: Sequence[Any], colours: Sequence[str]) -> None:
    """One row per detection: class colour, label, confidence bar, value.

    The colour is the same colour `app/core/rendering.py` used for that box, because
    both are assigned by detection index. Records are read-only; nothing is invented.
    """
    if not records:
        return
    rows = []
    for index, record in enumerate(records):
        label = escape(str(record.get("label", "")))
        confidence = float(record.get("confidence", 0.0))
        percent = max(0.0, min(1.0, confidence)) * 100
        colour = colours[index % len(colours)]
        rows.append(
            '<div class="jd-det">'
            f'<span class="jd-det__dot" style="background:{escape(colour)}"></span>'
            f'<span class="jd-det__label">{label}</span>'
            '<span class="jd-det__bar" aria-hidden="true">'
            f'<span style="width:{percent:.1f}%;background:{escape(colour)}"></span></span>'
            f'<span class="jd-det__value">{percent:.1f}%</span>'
            "</div>"
        )
    _html(f'<div class="jd-dets">{"".join(rows)}</div>')


# --------------------------------------------------------------------------
# Text pieces
# --------------------------------------------------------------------------
def empty_state(*, title: str, body: str) -> None:
    """Empty state that names the next action instead of apologising."""
    _html(
        '<div class="jd-empty">'
        f'<p class="jd-empty__title">{escape(title)}</p>'
        f'<p class="jd-empty__body">{escape(body)}</p>'
        "</div>"
    )


def note(text: str, *, tone: str = "info") -> None:
    """Quiet inline notice: a rule and a sentence, never a banner."""
    tone_css = "jd-note--warn" if tone == "warn" else ""
    _html(f'<div class="jd-note {tone_css}">{escape(text)}</div>')


def meta(text: str, *, mono: bool = False) -> None:
    """One line of real context: formats, limits, file facts."""
    modifier = " jd-meta--mono" if mono else ""
    _html(f'<p class="jd-meta{modifier}">{escape(text)}</p>')


def steps(items: Sequence[tuple[str, str]]) -> None:
    """Three short stages, numbered because the workflow really is ordered."""
    rendered = "".join(
        '<div class="jd-step">'
        f'<div class="jd-step__num">{index:02d}</div>'
        f'<div class="jd-step__body"><b>{escape(title)}</b><span>{escape(body)}</span></div>'
        "</div>"
        for index, (title, body) in enumerate(items, start=1)
    )
    _html(f'<div class="jd-steps">{rendered}</div>')


def bullets(items: Sequence[str]) -> None:
    """Tight bulleted list for limits and privacy notes."""
    rendered = "".join(f"<li>{escape(item)}</li>" for item in items)
    _html(f'<ul class="jd-list">{rendered}</ul>')


def specimen(*, annotated: bool = True, label: str = "Illustration, not a detection result.") -> None:
    """The small reference plate used once on Home. Never presented as output."""
    from app.views.home import specimen_svg

    _html(
        '<figure class="jd-specimen">'
        f'<div class="jd-specimen__art">{specimen_svg(annotated=annotated)}</div>'
        f'<figcaption class="jd-specimen__note">{escape(label)}</figcaption>'
        "</figure>"
    )
