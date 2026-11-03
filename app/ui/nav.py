"""Application navigation definition.

Pages are declared once, here, so `main.py` can hand them to `st.navigation` and
views can reference the same `Page` objects for in-app links without duplicating
route definitions.
"""

from __future__ import annotations

import streamlit as st

from app.views import about, camera, dashboard, detect, home

__all__ = ["PAGES", "PAGE", "PAGE_TITLES"]

PAGE: dict[str, st.Page] = {
    "overview": st.Page(
        home.render,
        title="Overview",
        icon=":material/space_dashboard:",
        url_path="overview",
        default=True,
    ),
    "detect": st.Page(
        detect.render,
        title="Detect",
        icon=":material/image_search:",
        url_path="detect",
    ),
    "camera": st.Page(
        camera.render,
        title="Camera",
        icon=":material/photo_camera:",
        url_path="camera",
    ),
    "analytics": st.Page(
        dashboard.render,
        title="Analytics",
        icon=":material/monitoring:",
        url_path="analytics",
    ),
    "about": st.Page(
        about.render,
        title="About",
        icon=":material/help:",
        url_path="about",
    ),
}

PAGES: list[st.Page] = list(PAGE.values())

PAGE_TITLES: dict[str, str] = {key: page.title for key, page in PAGE.items()}
