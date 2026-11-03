"""Design system for the JUDEtector interface.

A single source of truth for visual language: colour tokens, typography, spacing
and control styling. Views import from here instead of styling themselves, so the
interface stays consistent and restyling is a one-file change.

Contrast rule: every text colour used on a surface is at least 4.5:1 against that
surface, and no large saturated fill is ever placed behind dark text. The pairs are
asserted in `tests/test_ui_styles.py`, so a future palette edit cannot quietly
regress accessibility.
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
    "surface_sunken": "#F5F4F1",
    "border": "#E6E4DF",
    "border_strong": "#D9D5CD",
    "text": "#16191C",
    "text_secondary": "#5B6470",
    "text_muted": "#69707B",
    "accent": "#0F766E",
    "accent_strong": "#115E59",
    "accent_text": "#0B5F58",
    "accent_tint": "#EAF6F3",
    "accent_line": "#CBE9E3",
    "control_border": "#958D81",
    "warn": "#8A4B0B",
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
  --jd-surface-sunken: #F5F4F1;
  --jd-border: #E6E4DF;
  --jd-border-strong: #D9D5CD;
  --jd-text: #16191C;
  --jd-text-2: #5B6470;
  --jd-text-3: #69707B;
  --jd-accent: #0F766E;
  --jd-accent-strong: #115E59;
  --jd-accent-text: #0B5F58;
  --jd-accent-tint: #EAF6F3;
  --jd-accent-line: #CBE9E3;
  --jd-control-border: #958D81;
  --jd-warn: #8A4B0B;
  --jd-warn-tint: #FEF8EE;
  --jd-warn-line: #F0E1C6;
  --jd-radius: 14px;
  --jd-radius-sm: 10px;
  --jd-focus: 0 0 0 3px rgba(15, 118, 110, 0.18);
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
  padding: 1.9rem 2.4rem 4.5rem;
  max-width: 1040px;
}
@media (max-width: 900px) {
  .block-container { padding: 0.9rem 1rem 3rem; }
}

/* ---------- typography ---------- */
.stApp h1 {
  font-size: 1.72rem !important;
  font-weight: 600;
  letter-spacing: -0.024em;
  color: var(--jd-text);
  padding: 0;
}
.stApp h2 { font-size: 1.05rem !important; font-weight: 600; letter-spacing: -0.012em; }
.stApp h3 { font-size: 0.96rem !important; font-weight: 600; }
.stApp p, .stApp li { font-size: 0.9rem; line-height: 1.62; color: var(--jd-text-2); }
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
[data-testid="stMarkdownContainer"] a { color: var(--jd-accent-text); text-decoration: none; }
[data-testid="stMarkdownContainer"] a:hover { text-decoration: underline; }
hr { border-color: var(--jd-border); margin: 1.4rem 0; }

/* ---------- sidebar + navigation ---------- */
[data-testid="stSidebar"] {
  background: var(--jd-surface);
  border-right: 1px solid var(--jd-border);
  min-width: 226px;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 0.55rem; }
[data-testid="stSidebarNav"] { padding: 0.3rem 0.55rem 0.4rem; }
[data-testid="stSidebarNavItems"] { gap: 1px; }
[data-testid="stSidebarNavLink"] {
  border-radius: var(--jd-radius-sm);
  padding: 0.42rem 0.55rem !important;
  color: var(--jd-text-2) !important;
  font-size: 0.87rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
}
[data-testid="stSidebarNavLink"]:hover { background: var(--jd-surface-sunken); color: var(--jd-text) !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: var(--jd-accent-tint);
  color: var(--jd-accent-text) !important;
  font-weight: 600;
}
[data-testid="stSidebarNavLink"] span { font-size: 0.87rem; }
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {
  color: currentColor;
  font-size: 19px;
}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {
  color: var(--jd-accent-text) !important;
}
[data-testid="stSidebarNavSeparator"] { border-color: var(--jd-border); }

/* ---------- buttons ---------- */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
  border-radius: var(--jd-radius-sm);
  font-size: 0.855rem;
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
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-tertiary"]:hover {
  background: var(--jd-surface-sunken);
  border-color: #C7C2B8;
  color: var(--jd-text);
}
[data-testid="stButton"] button:focus-visible,
[data-testid="stDownloadButton"] button:focus-visible,
[data-testid="stBaseButton-secondary"]:focus-visible {
  outline: none;
  box-shadow: var(--jd-focus);
  border-color: var(--jd-accent);
}

[data-testid="stBaseButton-primary"] {
  background: var(--jd-accent) !important;
  border: 1px solid var(--jd-accent) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  box-shadow: 0 1px 2px rgba(15, 118, 110, 0.18) !important;
}
[data-testid="stBaseButton-primary"]:hover {
  background: var(--jd-accent-strong) !important;
  border-color: var(--jd-accent-strong) !important;
  color: #FFFFFF !important;
}
[data-testid="stBaseButton-primary"]:focus-visible {
  outline: none !important;
  box-shadow: var(--jd-focus) !important;
}

.stApp button:disabled, .stApp button[disabled] {
  opacity: 1 !important;
  background: var(--jd-surface-sunken) !important;
  border-color: var(--jd-border) !important;
  color: var(--jd-text-3) !important;
  cursor: not-allowed !important;
  box-shadow: none !important;
}
.stApp :focus-visible { outline: 2px solid var(--jd-accent); outline-offset: 2px; }

/* ---------- file uploader ----------
   Neutral white surface, dashed hairline, dark text. Teal is used only for the
   browse button, the hover/focus border and the drag-active outline. */
[data-testid="stFileUploaderDropzone"] {
  background: var(--jd-surface) !important;
  border: 1.5px dashed var(--jd-control-border) !important;
  border-radius: var(--jd-radius) !important;
  padding: 1.5rem 1.1rem !important;
  flex-direction: column;
  align-items: center;
  gap: 0.7rem;
  text-align: center;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--jd-accent) !important;
  background: #FDFFFE !important;
}
[data-testid="stFileUploaderDropzone"]:focus-within {
  border-color: var(--jd-accent) !important;
  box-shadow: var(--jd-focus) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] { text-align: center; }
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] div {
  color: var(--jd-text-2) !important;
  font-size: 0.82rem !important;
  line-height: 1.5 !important;
  white-space: normal !important;
}
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] p {
  color: var(--jd-text) !important;
}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploader"] button {
  background: var(--jd-surface) !important;
  color: var(--jd-accent-text) !important;
  border: 1px solid var(--jd-accent-line) !important;
  border-radius: var(--jd-radius-sm) !important;
  font-size: 0.83rem !important;
  font-weight: 600 !important;
  padding: 0.42rem 0.85rem !important;
  box-shadow: none !important;
  transition: background 0.15s ease, border-color 0.15s ease;
}
[data-testid="stFileUploaderDropzone"] button:hover,
[data-testid="stFileUploader"] button:hover {
  background: var(--jd-accent-tint) !important;
  border-color: var(--jd-accent) !important;
  color: var(--jd-accent-text) !important;
}
[data-testid="stFileUploaderDropzone"] button:focus-visible,
[data-testid="stFileUploader"] button:focus-visible {
  outline: none !important;
  box-shadow: var(--jd-focus) !important;
  border-color: var(--jd-accent) !important;
}
[data-testid="stFileUploaderDropzone"] button:disabled,
[data-testid="stFileUploader"] button:disabled {
  background: var(--jd-surface-sunken) !important;
  border-color: var(--jd-border) !important;
  color: var(--jd-text-3) !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInput"] { cursor: pointer; }
[data-testid="stWidgetLabel"] p { font-size: 0.84rem; color: var(--jd-text); font-weight: 550; }

/* ---------- expanders ---------- */
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
[data-testid="stExpander"] summary:hover { background: var(--jd-surface-muted); }
[data-testid="stExpander"] summary p { font-size: 0.855rem; color: var(--jd-text); }
[data-testid="stExpanderDetails"] { padding: 0.1rem 0.9rem 0.85rem; }

[data-testid="stSlider"] [data-testid="stSliderThumbValue"] { font-size: 0.76rem; }
[data-testid="stSlider"] label p { font-size: 0.82rem; color: var(--jd-text-2); }

/* ---------- data, images, camera ---------- */
[data-testid="stDataFrame"] {
  border: 1px solid var(--jd-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--jd-surface);
}
[data-testid="stDataFrame"] [role="columnheader"] { background: #F7F8F7 !important; }
[data-testid="stImage"] img {
  border-radius: 12px;
  border: 1px solid var(--jd-border);
  background: var(--jd-surface);
}
[data-testid="stCameraInput"] video,
[data-testid="stCameraInput"] img { border-radius: 12px; }

/* ---------- metrics ---------- */
[data-testid="stMetric"] {
  background: var(--jd-surface);
  border: 1px solid var(--jd-border);
  border-radius: var(--jd-radius);
  padding: 0.75rem 0.9rem;
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
  font-size: 1.35rem !important;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--jd-text);
}
[data-testid="stMetricDelta"] { font-size: 0.78rem; }

/* ---------- alerts (quiet, semantic) ---------- */
[data-testid="stAlert"] {
  border-radius: 12px;
  border: 1px solid var(--jd-border);
  background: var(--jd-surface-muted);
  padding: 0.6rem 0.8rem;
}
[data-testid="stAlert"] p { font-size: 0.845rem; color: var(--jd-text-2); }
[data-testid="stAlert"] svg { width: 16px; height: 16px; }

/* ---------- custom primitives ---------- */
.jd-head { margin: 0 0 1.1rem 0; }
.jd-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.68rem;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  font-weight: 650;
  color: var(--jd-text-3);
  margin-bottom: 0.35rem;
}
.jd-eyebrow svg { color: var(--jd-accent); }
.jd-h1 {
  font-size: 1.72rem;
  font-weight: 600;
  letter-spacing: -0.026em;
  color: var(--jd-text);
  margin: 0;
  line-height: 1.2;
}
.jd-sub {
  font-size: 0.9rem;
  color: var(--jd-text-2);
  margin: 0.35rem 0 0;
  max-width: 62ch;
  line-height: 1.55;
}
.jd-head-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }

.jd-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--jd-border);
  background: var(--jd-surface);
  color: var(--jd-text-2);
  white-space: nowrap;
}
.jd-pill__dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.jd-pill--ok { background: var(--jd-accent-tint); color: var(--jd-accent-text); border-color: var(--jd-accent-line); }
.jd-pill--warn { background: var(--jd-warn-tint); color: var(--jd-warn); border-color: var(--jd-warn-line); }
.jd-pill--muted { background: var(--jd-surface-sunken); color: var(--jd-text-2); border-color: var(--jd-border); }

.jd-note {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  border: 1px solid var(--jd-border);
  background: var(--jd-surface-muted);
  border-radius: 12px;
  padding: 0.6rem 0.75rem;
  font-size: 0.845rem;
  color: var(--jd-text-2);
  line-height: 1.55;
  margin: 0.55rem 0;
}
.jd-note svg { flex: 0 0 auto; margin-top: 2px; color: var(--jd-text-3); }
.jd-note--warn { background: var(--jd-warn-tint); border-color: var(--jd-warn-line); color: var(--jd-warn); }
.jd-note--warn svg { color: var(--jd-warn); }
.jd-note--ok { background: var(--jd-accent-tint); border-color: var(--jd-accent-line); color: var(--jd-accent-text); }
.jd-note--ok svg { color: var(--jd-accent); }

.jd-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid var(--jd-border);
  background: var(--jd-surface-muted);
  border-radius: var(--jd-radius);
  padding: 1.6rem 1.2rem;
  margin: 0.7rem 0;
}
.jd-empty__icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--jd-surface);
  border: 1px solid var(--jd-border);
  color: var(--jd-text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.6rem;
}
.jd-empty__title { font-size: 0.9rem; font-weight: 600; color: var(--jd-text); margin: 0 0 0.2rem; }
.jd-empty__body { font-size: 0.83rem; color: var(--jd-text-2); margin: 0; line-height: 1.55; max-width: 46ch; }



.jd-section { margin: 1.5rem 0 0.55rem; }
.jd-section__title { font-size: 0.95rem; font-weight: 600; color: var(--jd-text); margin: 0; }
.jd-section__sub { font-size: 0.79rem; color: var(--jd-text-3); margin: 0.15rem 0 0; }

.jd-meta { font-size: 0.76rem; color: var(--jd-text-3); margin: 0.35rem 0 0; }

.jd-kv { display: flex; flex-wrap: wrap; gap: 1.4rem; margin: 0.2rem 0; }
.jd-kv__item { font-size: 0.8rem; color: var(--jd-text-3); }
.jd-kv__item b { display: block; font-size: 0.86rem; color: var(--jd-text); font-weight: 600; }

.jd-list { margin: 0.35rem 0 0; padding-left: 1.05rem; }
.jd-list li { font-size: 0.855rem; color: var(--jd-text-2); line-height: 1.65; margin-bottom: 0.2rem; }

.jd-steps { display: flex; flex-direction: column; gap: 0.5rem; margin: 0.3rem 0 0; }
.jd-step { display: flex; gap: 0.6rem; align-items: flex-start; }
.jd-step__num {
  flex: 0 0 auto;
  width: 20px; height: 20px;
  border-radius: 6px;
  background: var(--jd-accent-tint);
  color: var(--jd-accent-text);
  border: 1px solid var(--jd-accent-line);
  font-size: 0.72rem;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin-top: 1px;
}
.jd-step__text { font-size: 0.86rem; color: var(--jd-text-2); line-height: 1.55; }
.jd-step__text b { color: var(--jd-text); font-weight: 600; }

.jd-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.15rem 0.6rem 0.9rem;
}
.jd-brand__mark {
  width: 26px; height: 26px;
  border-radius: 8px;
  background: var(--jd-accent);
  color: #FFFFFF;
  display: flex; align-items: center; justify-content: center;
}
.jd-brand__name { font-size: 0.92rem; font-weight: 650; letter-spacing: -0.01em; color: var(--jd-text); margin: 0; line-height: 1.2; }
.jd-brand__tag { font-size: 0.68rem; color: var(--jd-text-3); margin: 0; letter-spacing: 0.02em; }

@media (max-width: 760px) {
  .jd-h1 { font-size: 1.45rem; }
  .jd-head-row { gap: 0.6rem; }
  .jd-empty { padding: 1.2rem 1rem; }
}
</style>
"""


def inject_theme() -> None:
    """Apply the application stylesheet.

    Called once per page render. Only static CSS is injected -- never user or
    model-derived content -- so `unsafe_allow_html` carries no injection risk.
    """
    st.markdown(_CSS, unsafe_allow_html=True)
