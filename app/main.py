"""JUDEtector — application entry point.

Run locally with:

    streamlit run app/main.py

Navigation is declared in `app/ui/nav.py`; each page is a `render()` callable in
`app/views/`. End users see Detect, Camera and Help. The developer page is hidden
from the navigation and reachable only at `/developer`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow `streamlit run app/main.py` without requiring an installed package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.nav import build_pages  # noqa: E402

__all__ = ["main"]

LOGO_PATH = PROJECT_ROOT / "assets" / "logo.svg"
MARK_PATH = PROJECT_ROOT / "assets" / "mark.svg"


def main() -> None:
    st.set_page_config(
        page_title="JUDEtector",
        page_icon=str(MARK_PATH) if MARK_PATH.is_file() else None,
        layout="wide",
        initial_sidebar_state="auto",
    )

    # The wordmark sits above the navigation; the sidebar itself carries nothing
    # but navigation and one privacy line, so the product stays task-focused.
    if LOGO_PATH.is_file():
        st.logo(str(LOGO_PATH), size="large", icon_image=str(MARK_PATH))

    page = st.navigation(build_pages())

    with st.sidebar:
        st.caption("Images are analysed in memory and never stored.")

    page.run()


main()
