"""Application navigation definition.

Only end-user destinations are listed. Technical controls and diagnostics live on
a separate developer page that is *hidden* from the navigation
(`visibility="hidden"`) and reachable only by its URL, `/developer`.

That page is deliberately not described as secured: Streamlit's visibility flag
hides a route, it does not authorise one. Real access control would have to be
implemented at the hosting layer, and nothing here should imply otherwise.

Destinations are declared as plain data (:class:`NavEntry`) and turned into
`st.Page` objects once, so tests can assert the information architecture without
instantiating Streamlit objects.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from app.views import camera, detect, dev
from app.views import help as help_view

__all__ = [
    "DEVELOPER",
    "ENTRIES",
    "PAGE_TITLES",
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


ENTRIES: tuple[NavEntry, ...] = (
    NavEntry("detect", "Detect", ":material/image_search:", "detect", detect.render, default=True),
    NavEntry("camera", "Camera", ":material/photo_camera:", "camera", camera.render),
    NavEntry("help", "Help", ":material/help:", "help", help_view.render),
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


def build_pages() -> list[st.Page]:
    """Build the navigation for the current script run.

    Built per run rather than at import time: `st.Page` binds to the running
    script context, so a module-level list would be stale in a reused process
    (tests, hot reload).
    """
    return [_page(entry) for entry in (*ENTRIES, DEVELOPER)]


def page_for(key: str) -> st.Page:
    """Navigation entry by key, for in-app links."""
    for entry in (*ENTRIES, DEVELOPER):
        if entry.key == key:
            return _page(entry)
    raise KeyError(key)
