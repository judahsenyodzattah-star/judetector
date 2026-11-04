"""Application navigation definition.

Consumer destinations only — Home, Detect, Camera, Help. Technical controls and
diagnostics live on a separate developer page that is *hidden* from the navigation
(`visibility="hidden"`) and reachable only by its URL, `/developer`.

That page is deliberately not described as secured: Streamlit's visibility flag
hides a route, it does not authorise one. Real access control would have to be
implemented at the hosting layer, and nothing here should imply otherwise.

**Why Material icons in the navigation?** `st.Page(icon=...)` accepts only an
emoji, ``:material/name:`` or ``"spinner"`` — arbitrary inline SVG is not
supported. The four destinations are the only place an icon is genuinely needed
(they stand in for the wordmark on the mobile drawer), so the navigation uses one
coherent Material Symbols Rounded glyph per destination and nothing inside the
pages uses icons at all. Replacing the native navigation with hand-written links
would cost URL routing, keyboard support and the mobile drawer.

Destinations are declared as plain data (:class:`NavEntry`) and turned into
`st.Page` objects per script run, so tests can assert the information architecture
without instantiating Streamlit objects.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from app.views import camera, detect, dev, home
from app.views import help as help_view

__all__ = [
    "DEVELOPER",
    "ENTRIES",
    "PAGE_TITLES",
    "SECTIONS",
    "NavEntry",
    "build_pages",
    "page_for",
]


@dataclass(frozen=True)
class NavEntry:
    """One navigable destination."""

    key: str
    title: str
    icon: str
    url_path: str
    render: Callable[[], None]
    default: bool = False
    hidden: bool = False
    section: str | None = None


ENTRIES: tuple[NavEntry, ...] = (
    NavEntry("home", "Home", ":material/home:", "home", home.render, default=True),
    NavEntry(
        "detect", "Detect", ":material/crop_free:", "detect", detect.render, section="Workspace"
    ),
    NavEntry(
        "camera", "Camera", ":material/photo_camera:", "camera", camera.render, section="Workspace"
    ),
    NavEntry("help", "Help", ":material/help:", "help", help_view.render, section="Guidance"),
)

#: Rail grouping. Home sits above the group titles as the product's front door; the
#: working destinations are grouped, and the guide is kept apart from the tools.
SECTIONS: tuple[tuple[str | None, tuple[str, ...]], ...] = (
    (None, ("home",)),
    ("Workspace", ("detect", "camera")),
    ("Guidance", ("help",)),
)

DEVELOPER: NavEntry = NavEntry(
    "developer",
    "Developer",
    ":material/terminal:",
    "developer",
    dev.render,
    hidden=True,
)


def _page(entry: NavEntry) -> st.Page:
    return st.Page(
        entry.render,
        title=entry.title,
        icon=entry.icon,
        url_path=entry.url_path,
        default=entry.default,
        visibility="hidden" if entry.hidden else "visible",
    )


PAGE_TITLES: dict[str, str] = {entry.key: entry.title for entry in ENTRIES}


def build_pages() -> dict[str, list[st.Page]]:
    """Build the navigation for the current script run.

    Returns an ordered mapping so Streamlit prints its own section headings in the
    rail. Built per run rather than at import time: `st.Page` binds to the running
    script context, so a module-level list would be stale in a reused process
    (tests, hot reload).
    """
    pages: dict[str, list[st.Page]] = {}
    by_key = {entry.key: entry for entry in ENTRIES}
    for title, keys in SECTIONS:
        pages[title or ""] = [_page(by_key[key]) for key in keys]
    # The developer page shares the last section: it is `visibility="hidden"`, so it
    # never appears in the rail and must not introduce a stray group heading.
    pages[next(reversed(pages))].append(_page(DEVELOPER))
    return pages


def page_for(key: str) -> st.Page:
    """Navigation entry by key, for in-app links and CTA buttons."""
    for entry in (*ENTRIES, DEVELOPER):
        if entry.key == key:
            return _page(entry)
    raise KeyError(key)
