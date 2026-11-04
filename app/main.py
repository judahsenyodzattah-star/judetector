"""JUDEtector — application entry point.

Run locally with:

    streamlit run app/main.py

The frame is a dark navigation rail around a light analysis canvas. Navigation is
declared in `app/ui/nav.py`; each page is a `render()` callable in `app/views/`. End
users see Home, Detect, Camera and Help. The developer page is hidden from the
navigation and reachable only at `/developer`.

The rail carries the wordmark, grouped destinations, genuine model state and one
privacy line — nothing else. There is no account, avatar or workspace switcher,
because the application has no such concepts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow `streamlit run app/main.py` without requiring an installed package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.components import rail_status  # noqa: E402
from app.ui.nav import build_pages  # noqa: E402

__all__ = ["main"]

LOGO_PATH = PROJECT_ROOT / "assets" / "logo.svg"
MARK_PATH = PROJECT_ROOT / "assets" / "mark.svg"


def _model_state() -> tuple[str, str, str]:
    """(state, label, detail) for the rail footer.

    Reads the registry only: it never loads weights or runs inference, so the footer
    can never imply a capability the application does not have.
    """
    from app.components.settings import current_model

    spec, error = current_model()
    if error or spec is None:
        return "unavailable", "No model configured", "analysis off"
    detail = "ready" if spec.weights_present else "unavailable"
    return ("ready" if spec.weights_present else "unavailable"), spec.display_name, detail


def main() -> None:
    st.set_page_config(
        page_title="JUDEtector",
        page_icon=str(MARK_PATH) if MARK_PATH.is_file() else None,
        layout="wide",
        initial_sidebar_state="auto",
    )

    if LOGO_PATH.is_file():
        st.logo(str(LOGO_PATH), size="large", icon_image=str(MARK_PATH))

    page = st.navigation(build_pages())

    with st.sidebar:
        state, label, detail = _model_state()
        rail_status(label, state=state, detail=detail)
        st.caption("Images are analysed in memory and never stored.")

    page.run()


main()
