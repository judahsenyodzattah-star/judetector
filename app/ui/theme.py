"""Design system for the JUDEtector interface.

The product is an analysis workspace: a dark navigation rail frames a light canvas,
work happens in bordered cards, and the image and its detections share one screen.
Paper-and-ink is retained as identity (warm canvas, white cards, one ochre marking
colour) but structure comes first — the interface must read as a built application,
not a poster.

Two rules worth knowing before editing:

* **Ochre marks; it does not decorate.** `--jd-mark` may fill the primary action,
  draw the active-navigation rule, outline focus, and colour detection marks. It may
  never become a panel, badge background or tinted section.
* **Contrast is measured, not eyeballed.** Every ink/surface pair is asserted in
  `tests/test_ui_styles.py`, including the dark rail.

Where Streamlit can express something natively — card borders and radii, button and
link colours, tab underlines, slider tracks — it is set in `.streamlit/config.toml`
rather than here. This stylesheet only holds what the theme cannot: the rail's
active state, card headers, the detection list, the dropzone and composed pieces.

`inject_theme()` emits static CSS only, so `unsafe_allow_html` carries no risk.
"""

from __future__ import annotations

import streamlit as st

__all__ = ["PALETTE", "MONO_FAMILY", "SANS_FAMILY", "inject_theme"]

# Tokens mirror `.streamlit/config.toml`, which styles Streamlit's own widgets.
PALETTE: dict[str, str] = {
    "sheet": "#F4F2ED",  # workspace canvas
    "mount": "#FFFFFF",  # cards, inputs, viewer surface
    "rail": "#1E2122",  # navigation rail (the only dark surface)
    "rail_muted": "#A9ADA9",  # rail secondary text
    "rail_text": "#EDEBE6",  # rail primary text
    "ink": "#16181A",
    "ink_secondary": "#52585C",
    "rule": "#D0CBC1",
    "mark": "#8A5A00",  # primary action, active rule, focus, detection outline
    "mark_hover": "#6F4900",
    "ok": "#1F6F4A",
    "warn": "#8A4B0B",
    "danger": "#A03024",
    "art_canvas": "#EFECE4",
    "art_shape": "#DAD5C9",
}

SANS_FAMILY = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", '
    'Arial, sans-serif'
)
MONO_FAMILY = (
    'ui-monospace, SFMono-Regular, "SF Mono", "Cascadia Mono", Menlo, Consolas, '
    'monospace'
)

_CSS = """
<style>
:root {
  --jd-sheet: #F4F2ED;
  --jd-mount: #FFFFFF;
  --jd-rail: #1E2122;
  --jd-rail-muted: #A9ADA9;
  --jd-rail-text: #EDEBE6;
  --jd-ink: #16181A;
  --jd-ink-2: #52585C;
  --jd-rule: #D0CBC1;
  --jd-mark: #8A5A00;
  --jd-mark-hover: #6F4900;
  --jd-ok: #1F6F4A;
  --jd-warn: #8A4B0B;
  --jd-danger: #A03024;
  --jd-art-canvas: #EFECE4;
  --jd-art-shape: #DAD5C9;
  --jd-focus: 0 0 0 3px rgba(138, 90, 0, 0.30);

  /* spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 */
  --jd-1: 0.25rem;
  --jd-2: 0.5rem;
  --jd-3: 0.75rem;
  --jd-4: 1rem;
  --jd-5: 1.5rem;
  --jd-6: 2rem;
  --jd-7: 3rem;

  --jd-radius: 8px;
  --jd-radius-sm: 6px;

  --jd-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
    Arial, sans-serif;
  --jd-mono: ui-monospace, SFMono-Regular, "SF Mono", "Cascadia Mono", Menlo,
    Consolas, monospace;
}

/* ---------- canvas ---------- */
.stApp, [data-testid="stAppViewContainer"] { background: var(--jd-sheet); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp select, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: var(--jd-sans);
  -webkit-font-smoothing: antialiased;
}
.stApp { color: var(--jd-ink); }
#MainMenu, footer, [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; }

.block-container {
  padding: var(--jd-5) var(--jd-6) var(--jd-7);
  max-width: 1240px;
}
@media (max-width: 900px) {
  .block-container { padding: var(--jd-4) var(--jd-4) var(--jd-6); }
}

/* ---------- type ---------- */
.stApp h1 { font-size: 1.375rem !important; font-weight: 600; letter-spacing: -0.014em; line-height: 1.25; padding: 0; }
.stApp h2 { font-size: 1.06rem !important; font-weight: 600; letter-spacing: -0.008em; }
.stApp h3 { font-size: 0.94rem !important; font-weight: 600; }
.stApp p, .stApp li { font-size: 0.88rem; line-height: 1.55; color: var(--jd-ink-2); }
.stApp strong { color: var(--jd-ink); font-weight: 600; }
[data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
  font-size: 0.72rem !important;
  color: var(--jd-ink-2) !important;
  line-height: 1.5;
}
.stApp code {
  background: var(--jd-art-canvas);
  color: var(--jd-ink);
  border-radius: 0;
  padding: 0.06em 0.32em;
  font-family: var(--jd-mono);
  font-size: 0.86em;
}
[data-testid="stMarkdownContainer"] a {
  color: var(--jd-mark);
  text-decoration: none;
  font-weight: 500;
}
[data-testid="stMarkdownContainer"] a:hover { color: var(--jd-mark-hover); text-decoration: underline; }
hr { border: 0; border-top: 1px solid var(--jd-rule); margin: var(--jd-4) 0; }

/* ---------- navigation rail ---------- */
[data-testid="stSidebar"] {
  background: var(--jd-rail);
  border-right: 1px solid #33383A;
  min-width: 224px;
}
[data-testid="stSidebar"] * { color: var(--jd-rail-text); }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: var(--jd-2); }
[data-testid="stSidebarNav"] { padding: var(--jd-2) var(--jd-2) var(--jd-3); }
[data-testid="stSidebarNavItems"] { gap: 2px; }
[data-testid="stSidebarNavLink"] {
  border-radius: var(--jd-radius-sm) !important;
  padding: 0.5rem 0.6rem !important;
  color: var(--jd-rail-muted) !important;
  font-size: 0.88rem;
  font-weight: 500;
  border-left: 2px solid transparent;
}
[data-testid="stSidebarNavLink"]:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--jd-rail-text) !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: rgba(255, 255, 255, 0.08);
  border-left-color: var(--jd-mark);
  color: #FFFFFF !important;
  font-weight: 600;
}
[data-testid="stSidebarNavLink"] span { font-size: 0.88rem; }
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {
  color: currentColor;
  font-size: 18px;
  opacity: 0.9;
}
[data-testid="stSidebarNavSeparator"] { border-color: #33383A; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: var(--jd-rail-muted) !important;
  font-size: 0.72rem !important;
}

/* rail footer: genuine model state, no invented account chrome */
.jd-rail-status {
  display: flex;
  align-items: center;
  gap: var(--jd-2);
  border-top: 1px solid #33383A;
  margin: var(--jd-3) var(--jd-2) 0;
  padding: var(--jd-3) var(--jd-2) 0;
  font-size: 0.72rem;
  color: var(--jd-rail-muted);
}
.jd-rail-status__dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--jd-rail-muted);
  flex: 0 0 auto;
}
.jd-rail-status--ready .jd-rail-status__dot { background: #4FA97A; }
.jd-rail-status--unavailable .jd-rail-status__dot { background: #D08A3E; }
.jd-rail-status b { color: var(--jd-rail-text); font-weight: 600; }

/* ---------- actions ---------- */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-ink-2);
  background: var(--jd-mount);
  color: var(--jd-ink);
  font-size: 0.88rem;
  font-weight: 550;
  padding: 0.44rem 0.85rem;
}
[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-tertiary"]:hover {
  background: var(--jd-sheet);
  border-color: var(--jd-ink);
  color: var(--jd-ink);
}
[data-testid="stBaseButton-primary"] {
  background: var(--jd-mark) !important;
  border: 1px solid var(--jd-mark) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
}
[data-testid="stBaseButton-primary"]:hover {
  background: var(--jd-mark-hover) !important;
  border-color: var(--jd-mark-hover) !important;
  color: #FFFFFF !important;
}
[data-testid="stButton"] button:focus-visible,
[data-testid="stDownloadButton"] button:focus-visible,
[data-testid="stBaseButton-secondary"]:focus-visible,
[data-testid="stBaseButton-primary"]:focus-visible,
[data-testid="stPopoverButton"]:focus-visible {
  outline: none;
  box-shadow: var(--jd-focus);
}
.stApp button:disabled, .stApp button[disabled] {
  background: var(--jd-sheet) !important;
  border-color: var(--jd-rule) !important;
  color: var(--jd-ink-2) !important;
  cursor: not-allowed !important;
}
.stApp :focus-visible { outline: 2px solid var(--jd-mark); outline-offset: 2px; }
[data-testid="stPopoverButton"] {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-rule);
  background: var(--jd-mount);
  color: var(--jd-ink);
  font-size: 0.84rem;
  font-weight: 550;
  padding: 0.36rem 0.7rem;
}
[data-testid="stPopoverButton"]:hover { background: var(--jd-sheet); border-color: var(--jd-ink-2); }

/* ---------- file uploader ----------
   Streamlit paints the dropzone <section> with `theme.colors.secondaryBg`, which is
   #FFFFFF in .streamlit/config.toml, so the resting surface is white at the theme
   level and not only by override. Everything below refines border, text and states. */
[data-testid="stFileUploaderDropzone"] {
  background: var(--jd-mount) !important;
  border: 1.5px dashed var(--jd-ink-2) !important;
  border-radius: var(--jd-radius) !important;
  padding: var(--jd-6) var(--jd-4) !important;
  flex-direction: column;
  align-items: center;
  gap: var(--jd-2);
  text-align: center;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--jd-ink) !important;
  background: var(--jd-mount) !important;
}
[data-testid="stFileUploaderDropzone"]:focus-within {
  border-color: var(--jd-mark) !important;
  box-shadow: var(--jd-focus) !important;
}
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] div {
  color: var(--jd-ink) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] div {
  color: var(--jd-ink-2) !important;
  font-size: 0.84rem !important;
  line-height: 1.5 !important;
  white-space: normal !important;
}
[data-testid="stFileUploader"] button {
  background: var(--jd-mount) !important;
  color: var(--jd-mark) !important;
  border: 1px solid var(--jd-mark) !important;
  border-radius: var(--jd-radius-sm) !important;
  font-size: 0.84rem !important;
  font-weight: 600 !important;
  padding: 0.4rem 0.8rem !important;
}
[data-testid="stFileUploader"] button:hover {
  background: var(--jd-sheet) !important;
  color: var(--jd-mark-hover) !important;
  border-color: var(--jd-mark-hover) !important;
}
[data-testid="stFileUploader"] button:focus-visible {
  outline: none !important;
  box-shadow: var(--jd-focus) !important;
}
[data-testid="stFileUploader"] button:disabled {
  background: var(--jd-sheet) !important;
  border-color: var(--jd-rule) !important;
  color: var(--jd-ink-2) !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInput"] { cursor: pointer; }
[data-testid="stWidgetLabel"] p {
  font-size: 0.84rem;
  color: var(--jd-ink);
  font-weight: 550;
}

/* ---------- tabs: underline, compact ---------- */
[data-testid="stTabs"] [role="tablist"] {
  gap: var(--jd-4);
  border-bottom: 1px solid var(--jd-rule);
}
[data-testid="stTabs"] button[role="tab"] {
  padding: 0.4rem 0 var(--jd-2);
  font-size: 0.88rem;
  font-weight: 550;
  color: var(--jd-ink-2);
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  color: var(--jd-ink);
  font-weight: 600;
}

/* ---------- metrics as a fact strip ---------- */
[data-testid="stMetric"] {
  background: transparent;
  border: 0;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  height: 100%;
}
[data-testid="stMetricLabel"] p {
  font-size: 0.72rem !important;
  letter-spacing: 0.02em;
  font-weight: 500;
  color: var(--jd-ink-2) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--jd-mono);
  font-size: 1.375rem !important;
  font-weight: 600;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink);
}

/* ---------- expander, slider, table ---------- */
[data-testid="stExpander"] {
  border: 1px solid var(--jd-rule);
  border-radius: var(--jd-radius-sm);
  background: var(--jd-mount);
  box-shadow: none;
  overflow: hidden;
}
[data-testid="stExpander"] summary {
  font-size: 0.88rem;
  font-weight: 550;
  color: var(--jd-ink);
  padding: var(--jd-2) var(--jd-3);
}
[data-testid="stExpander"] summary:hover { background: var(--jd-sheet); }
[data-testid="stExpander"] summary p { font-size: 0.88rem; color: var(--jd-ink); }
[data-testid="stExpanderDetails"] { padding: var(--jd-1) var(--jd-3) var(--jd-3); }

[data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
  font-family: var(--jd-mono);
  font-size: 0.72rem;
}
[data-testid="stSlider"] label p { font-size: 0.84rem; color: var(--jd-ink-2); }

[data-testid="stDataFrame"] {
  border: 1px solid var(--jd-rule);
  border-radius: var(--jd-radius-sm);
  overflow: hidden;
}

/* ---------- images ---------- */
[data-testid="stImage"] img {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-rule);
  display: block;
  width: 100%;
  height: auto;
}
[data-testid="stImage"] { margin: 0; }
[data-testid="stCameraInput"] video,
[data-testid="stCameraInput"] img { border-radius: var(--jd-radius-sm); }
[data-testid="stAlert"] {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-rule);
  background: var(--jd-mount);
  padding: var(--jd-2) var(--jd-3);
}
[data-testid="stAlert"] p { font-size: 0.88rem; color: var(--jd-ink-2); }

/* ---------- composed pieces ---------- */
.jd-head { margin: 0 0 var(--jd-5); }
.stApp .jd-h1 {
  font-size: 1.375rem !important;
  font-weight: 600;
  letter-spacing: -0.014em;
  line-height: 1.25;
  color: var(--jd-ink);
  margin: 0;
}
.stApp .jd-sub {
  font-size: 0.88rem;
  color: var(--jd-ink-2);
  margin: var(--jd-1) 0 0;
  max-width: 66ch;
  line-height: 1.55;
}

.jd-card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--jd-3);
  margin: 0 0 var(--jd-3);
}
.stApp .jd-card__title {
  font-size: 0.94rem;
  font-weight: 600;
  color: var(--jd-ink);
  margin: 0;
}
.stApp .jd-card__note {
  font-size: 0.72rem;
  color: var(--jd-ink-2);
  margin: 0;
}

/* detection list: the row is the unit of meaning, colour-linked to the overlay */
.jd-dets { display: flex; flex-direction: column; margin: var(--jd-2) 0 0; }
.jd-det {
  display: grid;
  grid-template-columns: 10px minmax(3rem, 1fr) minmax(4rem, 7rem) 3.6rem;
  align-items: center;
  gap: var(--jd-3);
  padding: var(--jd-2) 0;
  border-top: 1px solid var(--jd-rule);
  font-size: 0.84rem;
}
.jd-det:first-child { border-top: 0; }
.jd-det__dot { width: 10px; height: 10px; border-radius: 50%; }
.jd-det__label { color: var(--jd-ink); font-weight: 550; overflow-wrap: anywhere; }
.jd-det__bar { height: 6px; border-radius: var(--jd-radius-sm); background: var(--jd-art-canvas); overflow: hidden; }
.jd-det__bar span { display: block; height: 100%; border-radius: var(--jd-radius-sm); }
.jd-det__value {
  font-family: var(--jd-mono);
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink);
  text-align: right;
  font-size: 0.78rem;
}

.jd-empty {
  border: 1px dashed var(--jd-rule);
  border-radius: var(--jd-radius-sm);
  padding: var(--jd-6) var(--jd-4);
  text-align: center;
  background: transparent;
}
.stApp .jd-empty__title { font-size: 0.88rem; font-weight: 600; color: var(--jd-ink); margin: 0; }
.stApp .jd-empty__body {
  font-size: 0.84rem;
  color: var(--jd-ink-2);
  margin: var(--jd-1) auto 0;
  line-height: 1.55;
  max-width: 44ch;
}

.jd-note {
  border-left: 2px solid var(--jd-rule);
  padding: var(--jd-1) 0 var(--jd-1) var(--jd-3);
  font-size: 0.88rem;
  line-height: 1.55;
  color: var(--jd-ink-2);
  margin: var(--jd-3) 0;
  max-width: 68ch;
}
/* the unavailable state is marked with weight, not decoration */
.jd-note--warn { border-left-color: var(--jd-ink); color: var(--jd-ink); }

.stApp .jd-meta { font-size: 0.72rem; color: var(--jd-ink-2); margin: var(--jd-1) 0 0; }
.jd-meta--mono { font-family: var(--jd-mono); font-variant-numeric: tabular-nums; }

.jd-list { margin: var(--jd-1) 0 0; padding-left: 1.05rem; max-width: 72ch; }
.jd-list li { font-size: 0.88rem; color: var(--jd-ink-2); line-height: 1.6; margin-bottom: var(--jd-1); }

.jd-steps { display: flex; flex-wrap: wrap; gap: var(--jd-5); margin: var(--jd-2) 0 0; }
.jd-step { flex: 1 1 12rem; min-width: 0; }
.jd-step__num {
  font-family: var(--jd-mono);
  font-size: 0.72rem;
  color: var(--jd-mark);
  letter-spacing: 0.04em;
}
.jd-step__body b { display: block; font-size: 0.88rem; color: var(--jd-ink); font-weight: 600; margin-top: 2px; }
.jd-step__body span { display: block; font-size: 0.78rem; color: var(--jd-ink-2); line-height: 1.5; margin-top: 2px; }

/* specimen plate: one small, secondary reference to what the product does */
.jd-specimen { margin: 0; }
.jd-specimen__art {
  background: var(--jd-art-canvas);
  border: 1px solid var(--jd-rule);
  border-radius: var(--jd-radius-sm);
  overflow: hidden;
  line-height: 0;
}
.jd-specimen__art svg { display: block; width: 100%; height: auto; }
.stApp .jd-specimen__note {
  font-size: 0.72rem;
  color: var(--jd-ink-2);
  margin: var(--jd-2) 0 0;
}

.stApp .jd-section {
  font-size: 0.94rem !important;
  font-weight: 600;
  color: var(--jd-ink);
  margin: var(--jd-5) 0 var(--jd-1);
}
.stApp .jd-section__note { font-size: 0.78rem; color: var(--jd-ink-2); margin: 0 0 var(--jd-2); }

.jd-readout { border-top: 1px solid var(--jd-rule); margin: var(--jd-2) 0; }
.jd-readout__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--jd-4);
  padding: var(--jd-2) 0;
  border-bottom: 1px solid var(--jd-rule);
  font-size: 0.84rem;
}
.jd-readout__row span { color: var(--jd-ink-2); }
.jd-readout__row b {
  font-family: var(--jd-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 500;
  color: var(--jd-ink);
  text-align: right;
  overflow-wrap: anywhere;
}

/* help articles */
.jd-article { max-width: 72ch; }
.jd-article h3 { margin: var(--jd-5) 0 var(--jd-2); }

@media (max-width: 760px) {
  .jd-dets { font-size: 0.84rem; }
  .jd-det { grid-template-columns: 10px minmax(3rem, 1fr) 3.4rem; }
  .jd-det__bar { display: none; }
  .jd-steps { gap: var(--jd-3); }
}
</style>
"""


def inject_theme() -> None:
    """Apply the application stylesheet (static CSS only)."""
    st.markdown(_CSS, unsafe_allow_html=True)
