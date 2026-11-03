"""Design system for the JUDEtector interface.

A single source of truth for visual language: colour tokens, typography, spacing
and component styling. Pages import from here instead of styling themselves, so
the interface stays consistent and restyling is a one-file change.
"""

from __future__ import annotations

import streamlit as st

__all__ = ["PALETTE", "inject_theme"]


# Tokens mirror the values in `.streamlit/config.toml`, which styles Streamlit's
# own widgets (sliders, focus rings, links). Keeping both in sync means the brand
# colour applies to native controls without fragile CSS overrides.
PALETTE: dict[str, str] = {
    "bg": "#FAFAF8",
    "surface": "#FFFFFF",
    "surface_muted": "#FCFCFB",
    "border": "#E6E4DF",
    "border_strong": "#D9D5CD",
    "text": "#16191C",
    "text_secondary": "#5B6470",
    "text_muted": "#8A929C",
    "accent": "#0F766E",
    "accent_strong": "#115E59",
    "accent_tint": "#EAF6F3",
    "accent_line": "#CBE9E3",
    "warn": "#B45309",
    "warn_tint": "#FEF8EE",
    "warn_line": "#F0E1C6",
    "danger": "#B42318",
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --jd-bg: #FAFAF8;
  --jd-surface: #FFFFFF;
  --jd-surface-muted: #FCFCFB;
  --jd-border: #E6E4DF;
  --jd-border-strong: #D9D5CD;
  --jd-text: #16191C;
  --jd-text-2: #5B6470;
  --jd-text-3: #8A929C;
  --jd-accent: #0F766E;
  --jd-accent-strong: #115E59;
  --jd-accent-tint: #EAF6F3;
  --jd-accent-line: #CBE9E3;
  --jd-warn: #B45309;
  --jd-warn-tint: #FEF8EE;
  --jd-warn-line: #F0E1C6;
  --jd-radius: 14px;
  --jd-radius-sm: 10px;
  --jd-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.05);
}

/* ---------- canvas ---------- */
.stApp, [data-testid="stAppViewContainer"] { background: var(--jd-bg); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp select, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}
.stApp { color: var(--jd-text); }

#MainMenu, footer, [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; }

.block-container {
  padding: 1.6rem 2.4rem 4.5rem;
  max-width: 1160px;
}
@media (max-width: 900px) {
  .block-container { padding: 0.9rem 1rem 3rem; }
}

/* ---------- typography ---------- */
.stApp h1 {
  font-size: 1.85rem !important;
  font-weight: 600;
  letter-spacing: -0.024em;
  color: var(--jd-text);
  padding: 0;
}
.stApp h2 { font-size: 1.1rem !important; font-weight: 600; letter-spacing: -0.012em; }
.stApp h3 { font-size: 0.98rem !important; font-weight: 600; }
.stApp p, .stApp li { font-size: 0.9rem; line-height: 1.6; color: var(--jd-text-2); }
.stApp strong { color: var(--jd-text); font-weight: 600; }
[data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
  font-size: 0.78rem !important;
  color: var(--jd-text-3) !important;
  line-height: 1.5;
}
.stApp code {
  background: #F1F3F2;
  color: #2A3038;
  border-radius: 5px;
  padding: 0.08em 0.35em;
  font-size: 0.82em;
}
[data-testid="stMarkdownContainer"] a { color: var(--jd-accent-strong); text-decoration: none; }
[data-testid="stMarkdownContainer"] a:hover { text-decoration: underline; }
hr { border-color: var(--jd-border); margin: 1.4rem 0; }

/* ---------- sidebar + navigation ---------- */
[data-testid="stSidebar"] {
  background: var(--jd-surface);
  border-right: 1px solid var(--jd-border);
  min-width: 232px;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 0.35rem; }
[data-testid="stSidebarNav"] { padding: 0.15rem 0.55rem 0.4rem; }
[data-testid="stSidebarNavItems"] { gap: 1px; }
[data-testid="stSidebarNavLink"] {
  border-radius: var(--jd-radius-sm);
  padding: 0.4rem 0.55rem !important;
  margin: 0;
  transition: background 0.15s ease, color 0.15s ease;
}
[data-testid="stSidebarNavLink"]:hover { background: #F4F6F5; }
[data-testid="stSidebarNavLink"][aria-current="page"] { background: var(--jd-accent-tint); }
[data-testid="stSidebarNavLink"] span {
  font-size: 0.875rem !important;
  font-weight: 500;
  color: var(--jd-text-2);
}
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {
  color: var(--jd-text-3);
  font-size: 18px;
}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {
  color: var(--jd-accent-strong) !important;
  font-weight: 600;
}
[data-testid="stSidebarNavSeparator"] { border-color: var(--jd-border); }

/* ---------- buttons ---------- */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton"],
button[kind="secondary"],
button[kind="tertiary"] {
  border-radius: var(--jd-radius-sm);
  font-size: 0.845rem;
  font-weight: 550;
  padding: 0.46rem 0.9rem;
  border: 1px solid var(--jd-border-strong);
  background: var(--jd-surface);
  color: var(--jd-text);
  box-shadow: 0 1px 1px rgba(16, 24, 40, 0.03);
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
button[kind="secondary"]:hover,
button[kind="tertiary"]:hover {
  background: #FBFBFA;
  border-color: #C7C2B8;
  color: var(--jd-text);
}
button[kind="primary"] {
  background: var(--jd-accent) !important;
  border-color: var(--jd-accent) !important;
  color: #FFFFFF !important;
}
button[kind="primary"]:hover {
  background: var(--jd-accent-strong) !important;
  border-color: var(--jd-accent-strong) !important;
  color: #FFFFFF !important;
}
.stApp button:disabled, .stApp button[disabled] { opacity: 0.5; cursor: not-allowed; }
.stApp :focus-visible { outline: 2px solid var(--jd-accent); outline-offset: 2px; }

/* ---------- metrics ---------- */
[data-testid="stMetric"] {
  background: var(--jd-surface);
  border: 1px solid var(--jd-border);
  border-radius: var(--jd-radius);
  padding: 0.8rem 0.95rem;
  box-shadow: var(--jd-shadow);
  height: 100%;
}
[data-testid="stMetricLabel"] p {
  font-size: 0.715rem !important;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 600;
  color: var(--jd-text-3) !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.42rem !important;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--jd-text);
}
[data-testid="stMetricDelta"] { font-size: 0.78rem; }

/* ---------- containers / cards ---------- */
.jd-panel {
  border: 1px solid var(--jd-border);
  border-radius: var(--jd-radius);
  background: var(--jd-surface);
  padding: 0.85rem 0.95rem;
  box-shadow: var(--jd-shadow);
  margin: 0.1rem 0;
}

/* ---------- inputs ---------- */
[data-testid="stFileUploaderDropzone"] {
  background: var(--jd-surface);
  border: 1.5px dashed var(--jd-border-strong);
  border-radius: var(--jd-radius);
  padding: 1.6rem 1rem;
  transition: border-color 0.15s ease, background 0.15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--jd-accent);
  background: #FBFDFC;
}
[data-testid="stFileUploaderDropzone"] span { font-size: 0.83rem; color: var(--jd-text-2); }
[data-testid="stFileUploaderDropzone"] small { color: var(--jd-text-3) !important; }
[data-testid="stFileUploaderDropzone"] button { border-radius: 8px; font-size: 0.8rem; }

[data-testid="stExpander"] {
  border: 1px solid var(--jd-border);
  border-radius: var(--jd-radius);
  background: var(--jd-surface);
  box-shadow: none;
  overflow: hidden;
}
[data-testid="stExpander"] summary {
  font-size: 0.855rem;
  font-weight: 550;
  color: var(--jd-text);
  padding: 0.55rem 0.9rem;
}
[data-testid="stExpander"] summary:hover { background: #FAFBFA; }
[data-testid="stExpander"] summary p { font-size: 0.855rem; color: var(--jd-text); }
[data-testid="stExpanderDetails"] { padding: 0.1rem 0.9rem 0.85rem; }

[data-testid="stSlider"] [data-testid="stSliderThumbValue"] { font-size: 0.76rem; }
[data-testid="stSlider"] label p { font-size: 0.82rem; color: var(--jd-text-2); }
[data-testid="stWidgetLabel"] p { font-size: 0.82rem; color: var(--jd-text-2); font-weight: 500; }

[data-testid="stDataFrame"] {
  border: 1px solid var(--jd-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--jd-surface);
}
[data-testid="stDataFrame"] [role="columnheader"] {
  background: #F7F8F7 !important;
}
[data-testid="stImage"] img {
  border-radius: 12px;
  border: 1px solid var(--jd-border);
}
[data-testid="stCameraInput"] video,
[data-testid="stCameraInput"] img { border-radius: 12px; }

/* ---------- alerts (kept semantic, styled quiet) ---------- */
[data-testid="stAlert"] {
  border-radius: 12px;
  border: 1px solid var(--jd-border);
  background: var(--jd-surface-muted);
  padding: 0.6rem 0.8rem;
}
[data-testid="stAlert"] p { font-size: 0.845rem; color: var(--jd-text-2); }
[data-testid="stAlert"] svg { width: 16px; height: 16px; }

/* ---------- custom primitives ---------- */
.jd-head { margin: 0 0 1.15rem 0; }
.jd-eyebrow {
  font-size: 0.68rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 650;
  color: var(--jd-text-3);
  margin: 0 0 0.4rem 0;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.jd-eyebrow svg { color: var(--jd-accent); }
.jd-h1 {
  font-size: 1.9rem;
  font-weight: 600;
  letter-spacing: -0.026em;
  line-height: 1.15;
  color: var(--jd-text);
  margin: 0;
}
.jd-sub {
  font-size: 0.92rem;
  color: var(--jd-text-2);
  margin: 0.4rem 0 0 0;
  max-width: 64ch;
  line-height: 1.55;
}
.jd-head-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }

.jd-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.735rem;
  font-weight: 600;
  border: 1px solid transparent;
  white-space: nowrap;
}
.jd-pill__dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.jd-pill--ok { background: var(--jd-accent-tint); color: #0B5F58; border-color: var(--jd-accent-line); }
.jd-pill--warn { background: var(--jd-warn-tint); color: #8A4B0B; border-color: var(--jd-warn-line); }
.jd-pill--muted { background: #F3F4F3; color: #5B6470; border-color: #E4E6E4; }

.jd-note {
  display: flex;
  gap: 0.55rem;
  align-items: flex-start;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--jd-border);
  border-radius: 12px;
  background: var(--jd-surface-muted);
  font-size: 0.83rem;
  line-height: 1.5;
  color: var(--jd-text-2);
  margin: 0.55rem 0;
}
.jd-note svg { flex: 0 0 auto; margin-top: 2px; color: var(--jd-text-3); }
.jd-note--warn { background: var(--jd-warn-tint); border-color: var(--jd-warn-line); }
.jd-note--warn svg { color: var(--jd-warn); }
.jd-note--ok { background: var(--jd-accent-tint); border-color: var(--jd-accent-line); }
.jd-note--ok svg { color: var(--jd-accent); }

.jd-empty {
  padding: 1.15rem 1.1rem;
  border: 1px dashed var(--jd-border-strong);
  border-radius: var(--jd-radius);
  background: var(--jd-surface-muted);
  margin: 0.35rem 0;
}
.jd-empty__icon {
  width: 32px; height: 32px;
  border-radius: 9px;
  background: var(--jd-accent-tint);
  color: var(--jd-accent);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 0.6rem;
}
.jd-empty__title { font-size: 0.9rem; font-weight: 600; color: var(--jd-text); margin: 0 0 0.15rem; }
.jd-empty__body { font-size: 0.83rem; color: var(--jd-text-2); margin: 0; line-height: 1.55; max-width: 58ch; }

.jd-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.65rem;
  margin: 0.15rem 0;
}
.jd-tile {
  border: 1px solid var(--jd-border);
  background: var(--jd-surface);
  border-radius: 12px;
  padding: 0.8rem 0.85rem;
}
.jd-tile__icon { color: var(--jd-accent); margin-bottom: 0.45rem; display: flex; }
.jd-tile__title { font-size: 0.855rem; font-weight: 600; color: var(--jd-text); margin: 0 0 0.12rem; }
.jd-tile__body { font-size: 0.79rem; color: var(--jd-text-3); margin: 0; line-height: 1.5; }

.jd-section { margin: 1.7rem 0 0.6rem; }
.jd-section__title { font-size: 0.95rem; font-weight: 600; color: var(--jd-text); margin: 0; }
.jd-section__sub { font-size: 0.79rem; color: var(--jd-text-3); margin: 0.15rem 0 0; }

.jd-meta { font-size: 0.76rem; color: var(--jd-text-3); margin: 0.35rem 0 0; }

.jd-kv { display: flex; flex-wrap: wrap; gap: 1.4rem; margin: 0.2rem 0; }
.jd-kv__item { font-size: 0.8rem; color: var(--jd-text-3); }
.jd-kv__item b { display: block; font-size: 0.86rem; color: var(--jd-text); font-weight: 600; }

.jd-list { margin: 0.35rem 0 0; padding-left: 1.05rem; }
.jd-list li { font-size: 0.855rem; color: var(--jd-text-2); line-height: 1.65; margin-bottom: 0.2rem; }

.jd-side {
  border: 1px solid var(--jd-border);
  border-radius: 12px;
  padding: 0.6rem 0.7rem;
  background: var(--jd-surface-muted);
  margin: 0.55rem 0.55rem 0.2rem;
}
.jd-side__mark {
  width: 24px; height: 24px;
  border-radius: 7px;
  background: var(--jd-accent-tint);
  color: var(--jd-accent);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 0.5rem;
}
.jd-side__label {
  font-size: 0.64rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--jd-text-3);
  font-weight: 650;
  margin: 0 0 0.15rem;
}
.jd-side__name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--jd-text);
  margin: 0 0 0.35rem;
  line-height: 1.35;
}
.jd-side__hint {
  font-size: 0.7rem;
  color: var(--jd-text-3);
  margin: 0.4rem 0 0;
  text-transform: capitalize;
}

.jd-spacer { height: 0.6rem; }
@media (max-width: 760px) {
  .jd-h1 { font-size: 1.5rem; }
  .jd-grid { grid-template-columns: 1fr; }
  .jd-head-row { gap: 0.6rem; }
}
</style>
"""


def inject_theme() -> None:
    """Apply the application stylesheet.

    Called once per page render. Only static CSS is injected -- never user or
    model-derived content -- so `unsafe_allow_html` carries no injection risk.
    """
    st.markdown(_CSS, unsafe_allow_html=True)
