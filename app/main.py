"""JUDEtector — application entry point.

Run locally with:

    streamlit run app/main.py

Navigation is declared in `app/ui/nav.py`; each page is a `render()` callable in
`app/views/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow `streamlit run app/main.py` without requiring an installed package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.model_sidebar import render_sidebar_status  # noqa: E402
from app.ui.nav import PAGES  # noqa: E402

__all__ = ["main"]


def main() -> None:
    st.set_page_config(
        page_title="JUDEtector",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Each page applies the shared stylesheet, so the theme travels with the page
    # rather than leaking from the entry point.

    # The navigation block renders at the top of the sidebar; the read-only model
    # status sits beneath it. Model *controls* deliberately live on the workspace
    # pages, not in the navigation rail.
    page = st.navigation(PAGES)
    render_sidebar_status()
    page.run()


main()
