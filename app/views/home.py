"""Home — the application entry point and default route.

The page has one purpose: start an analysis. The native uploader is the dominant
surface; choosing a file stages it and opens Detect, where the explicit *Analyse image*
action lives. Nothing is inferred here.

Beside it sits this session's real information — a compact summary and, once an analysis
has actually run, the annotated output it produced, which reopens that exact result on
Detect. A new session shows a sentence, not a fabricated preview. Beneath both, the
workflow is one understated line rather than three competing columns.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.components.results import format_ms
from app.components.workflow import latest_result, remember_pending, stage_existing_result
from app.core import config
from app.core.stats import get_runs, summarise
from app.ui.components import card, flow_line, meta, page_header, panel, readout
from app.ui.theme import inject_theme

__all__ = ["render", "specimen_svg"]

HOME_UPLOAD_KEY = "home_upload"

#: Namespace Detect stores its analysis under; Home only ever reads it.
DETECT_NAMESPACE = "detect_analysis"

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


def _open_last_result() -> None:
    """Callback: reopen the stored analysis on Detect, unchanged."""
    if stage_existing_result(DETECT_NAMESPACE):
        st.switch_page(_page("detect"))


def render() -> None:
    inject_theme()

    page_header(
        "Analyse an image",
        "Upload a photo or take a snapshot. Analysis starts only when you choose "
        "Analyse image.",
    )

    workspace, session = st.columns([7, 3], gap="large", wrap=True)

    with workspace:
        with card():
            st.file_uploader(
                "Image file",
                type=list(config.SUPPORTED_IMAGE_TYPES),
                key=HOME_UPLOAD_KEY,
                on_change=_handoff,
                label_visibility="collapsed",
            )
        st.page_link(
            _page("camera"),
            label="Take a snapshot with the camera",
            icon=":material/photo_camera:",
        )
        meta("Images are analysed in memory and never stored.")

    with session:
        _session_panel()

    flow_line(["Choose an image", "Analyse", "Review and download"])


def _session_panel() -> None:
    """Session figures and the latest real result, or a meaningful empty state."""
    runs = get_runs(st.session_state)
    record = latest_result(DETECT_NAMESPACE)

    with panel("This session"):
        if not runs:
            meta(
                "No analyses yet. Counts and confidences appear here after your first "
                "analysis."
            )
            return

        summary = summarise(runs)
        rows = [
            ("Analyses", str(summary.total_runs)),
            ("Detections", str(summary.total_faces)),
        ]
        if summary.mean_confidence is not None:
            rows.append(("Mean confidence", f"{summary.mean_confidence:.1%}"))
        readout(rows)

        if record is not None:
            _last_result(record)


def _last_result(record: dict[str, Any]) -> None:
    """The annotated output of the latest analysis: a real measurement, not a preview."""
    outcome = record.get("outcome")
    if outcome is None or not outcome.ok or outcome.result is None:
        return
    result = outcome.result
    processed = outcome.processed
    filename = str(record.get("filename", "image"))
    total = record.get("total_ms")

    facts = [filename, f"{result.count} detection" + ("" if result.count == 1 else "s")]
    if isinstance(total, (int, float)) and total > 0:
        facts.append(format_ms(total))

    if processed is not None:
        st.image(
            processed,
            width="stretch",
            alt=(
                f"The annotated result for {filename}: "
                f"{result.count} detection" + ("" if result.count == 1 else "s")
            ),
        )
    meta(" · ".join(facts), mono=True)
    st.button(
        "Open this result",
        icon=":material/open_in_new:",
        on_click=_open_last_result,
        help="Reopen this analysis on Detect",
    )


def specimen_svg(*, annotated: bool) -> str:
    """The abstract specimen, drawn from palette tokens.

    No longer used on Home — a drawn abstraction read as a placeholder in review. It is
    kept because the palette-derived artwork is still asserted by the style suite, and
    would be the honest basis for any future illustration.
    """
    from app.ui.theme import PALETTE

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
