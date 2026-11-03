"""JUDEtector — Streamlit entry point.

Run locally with:

    streamlit run app/main.py

Navigation is declared here; each page is a `render()` callable in `app/views/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow `streamlit run app/main.py` without requiring an installed package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.model_sidebar import render_sidebar_footer  # noqa: E402
from app.views import about, camera, dashboard, detect, home  # noqa: E402

__all__ = ["main"]


def main() -> None:
    st.set_page_config(
        page_title="JUDEtector — AI Object Detection",
        page_icon="🔎",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    pages = [
        st.Page(home.render, title="Home", icon="🏠", url_path="home", default=True),
        st.Page(detect.render, title="Detect", icon="🖼️", url_path="detect"),
        st.Page(camera.render, title="Camera", icon="📷", url_path="camera"),
        st.Page(dashboard.render, title="Dashboard", icon="📊", url_path="dashboard"),
        st.Page(about.render, title="About", icon="ℹ️", url_path="about"),
    ]

    st.navigation(pages).run()
    render_sidebar_footer()


main()
