"""Design system for the JUDEtector interface.

The product is an analysis workspace: a graphite navigation rail frames a light canvas,
work happens in a small number of bordered cards, and the image and its detections share
one screen. Paper-and-ink survives as identity (warm canvas, white cards, one ochre
marking colour) while structure leads — this must read as a built application.

Three rules worth knowing before editing:

* **Ochre marks; it does not decorate.** `--jd-mark` may fill the primary action, draw the
  active-navigation rule, outline focus, and colour detection marks. It may never become a
  panel, badge background or tinted section.
* **Contrast is measured, not eyeballed.** Every ink/surface pair is asserted in
  `tests/test_ui_styles.py`, including the rail, where inactive destinations must still
  clear AA comfortably.
* **Streamlit owns what it can own.** Card borders and radii, button colours, tab
  underlines, slider tracks and the sidebar's graphite surface are set in
  `.streamlit/config.toml`. This stylesheet only holds what the theme cannot: the rail's
  active state and spacing, card headers, the detection list, the dropzone and the
  composed blocks.

`inject_theme()` emits static CSS only, so `unsafe_allow_html` carries no risk.
"""

from __future__ import annotations

import streamlit as st

__all__ = ["MONO_FAMILY", "PALETTE", "SANS_FAMILY", "inject_theme"]

# Tokens mirror `.streamlit/config.toml`, which styles Streamlit's own widgets.
PALETTE: dict[str, str] = {
    "sheet": "#F4F2ED",  # workspace canvas
    "mount": "#FFFFFF",  # cards, inputs, viewer surface
    "rail": "#1E2122",  # navigation rail (the only dark surface)
    "rail_muted": "#CBD0CC",  # rail destinations at rest
    "rail_label": "#A9ADA9",  # rail group labels
    "rail_text": "#EDEBE6",
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
  --jd-rail-muted: #CBD0CC;
  --jd-rail-label: #A9ADA9;
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

/* One measure, centred: wide screens get margins, not stretched content. */
.block-container {
  padding: var(--jd-5) var(--jd-6) var(--jd-7);
  max-width: 1160px;
  margin: 0 auto;
}
@media (max-width: 900px) {
  .block-container { padding: var(--jd-4) var(--jd-4) var(--jd-6); }
}

/* Streamlit stacks columns at narrow widths; give the stacked blocks breathing room. */
@media (max-width: 900px) {
  [data-testid="stHorizontalBlock"] { gap: var(--jd-5); }
}

/* ---------- type ---------- */
.stApp h1 { font-size: 1.5rem !important; font-weight: 600; letter-spacing: -0.016em; line-height: 1.22; padding: 0; }
.stApp h2 { font-size: 1.0625rem !important; font-weight: 600; letter-spacing: -0.008em; }
.stApp h3 { font-size: 0.9375rem !important; font-weight: 600; }
.stApp p, .stApp li { font-size: 0.9375rem; line-height: 1.6; color: var(--jd-ink-2); }
.stApp strong { color: var(--jd-ink); font-weight: 600; }
[data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
  font-size: 0.8125rem !important;
  color: var(--jd-ink-2) !important;
  line-height: 1.55;
}
.stApp code {
  background: var(--jd-art-canvas);
  color: var(--jd-ink);
  border-radius: 0;
  padding: 0.06em 0.32em;
  font-family: var(--jd-mono);
  font-size: 0.88em;
}
[data-testid="stMarkdownContainer"] a {
  color: var(--jd-mark);
  text-decoration: none;
  font-weight: 550;
}
[data-testid="stMarkdownContainer"] a:hover { color: var(--jd-mark-hover); text-decoration: underline; }
hr { border: 0; border-top: 1px solid var(--jd-rule); margin: var(--jd-4) 0; }

/* ---------- navigation rail ---------- */
[data-testid="stSidebar"] {
  background: var(--jd-rail);
  border-right: 1px solid #33383A;
  min-width: 236px;
}
[data-testid="stSidebar"] * { color: var(--jd-rail-text); }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: var(--jd-3); }
[data-testid="stSidebarNav"] { padding: var(--jd-2) 0.625rem var(--jd-4); }
[data-testid="stSidebarNavItems"] { gap: 2px; }

[data-testid="stNavSectionHeader"] {
  padding: var(--jd-4) 0.65rem var(--jd-1);
}
[data-testid="stNavSectionHeader"] p,
[data-testid="stNavSectionHeader"] span {
  font-size: 0.75rem !important;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--jd-rail-label) !important;
}

[data-testid="stSidebarNavLink"] {
  border-radius: var(--jd-radius-sm) !important;
  padding: 0.5rem 0.65rem !important;
  min-height: 2.5rem;
  color: var(--jd-rail-muted) !important;
  font-size: 0.9375rem;
  font-weight: 500;
  border-left: 3px solid transparent;
}
[data-testid="stSidebarNavLink"]:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #FFFFFF !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: rgba(255, 255, 255, 0.10);
  border-left-color: var(--jd-mark);
  color: #FFFFFF !important;
  font-weight: 600;
}
[data-testid="stSidebarNavLink"] span { font-size: 0.9375rem; font-weight: inherit; }
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {
  color: currentColor;
  font-size: 20px;
  opacity: 1;
}
[data-testid="stSidebarNavSeparator"] { border-color: #33383A; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: var(--jd-rail-muted) !important;
  font-size: 0.75rem !important;
}

/* rail footer: one honest status light, nothing technical */
.jd-rail-status {
  display: flex;
  align-items: center;
  gap: var(--jd-2);
  border-top: 1px solid #33383A;
  margin: var(--jd-3) 0.625rem 0;
  padding: var(--jd-3) 0.25rem var(--jd-1);
  font-size: 0.75rem;
  letter-spacing: 0.01em;
  color: var(--jd-rail-muted);
}
.jd-rail-status__dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--jd-rail-label);
  flex: 0 0 auto;
}
.jd-rail-status--ready .jd-rail-status__dot { background: #57B183; }
.jd-rail-status--unavailable .jd-rail-status__dot { background: #D08A3E; }

/* ---------- actions ---------- */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-ink-2);
  background: var(--jd-mount);
  color: var(--jd-ink);
  font-size: 0.875rem;
  font-weight: 550;
  padding: 0.46rem 0.9rem;
  min-height: 2.375rem;
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
  font-size: 0.875rem;
  font-weight: 550;
  padding: 0.38rem 0.75rem;
  min-height: 2.25rem;
}
[data-testid="stPopoverButton"]:hover { background: var(--jd-sheet); border-color: var(--jd-ink-2); }

/* ---------- file uploader ----------
   Streamlit paints the dropzone <section> with `theme.colors.secondaryBg`, which is
   #FFFFFF in .streamlit/config.toml: the resting surface is white at the theme level,
   not only by override. Below, the dropzone becomes the page's primary surface and its
   browse button the only filled ochre control on Home. */
[data-testid="stFileUploaderDropzone"] {
  background: var(--jd-mount) !important;
  border: 1.5px dashed var(--jd-ink-2) !important;
  border-radius: var(--jd-radius) !important;
  padding: var(--jd-7) var(--jd-5) !important;
  flex-direction: column;
  align-items: center;
  gap: var(--jd-3);
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
  color: var(--jd-ink) !important;
  font-size: 0.9375rem !important;
  font-weight: 550 !important;
  line-height: 1.5 !important;
  white-space: normal !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploaderDropzoneInstructions"] span + span {
  color: var(--jd-ink-2) !important;
  font-size: 0.8125rem !important;
  font-weight: 400 !important;
}
/* the browse control is the page's primary action */
[data-testid="stFileUploader"] button {
  background: var(--jd-mark) !important;
  color: #FFFFFF !important;
  border: 1px solid var(--jd-mark) !important;
  border-radius: var(--jd-radius-sm) !important;
  font-size: 0.875rem !important;
  font-weight: 600 !important;
  padding: 0.5rem 1.05rem !important;
  margin-top: var(--jd-1) !important;
}
[data-testid="stFileUploader"] button:hover {
  background: var(--jd-mark-hover) !important;
  color: #FFFFFF !important;
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
  font-size: 0.875rem;
  color: var(--jd-ink);
  font-weight: 550;
}

/* ---------- tabs: underline, compact ---------- */
[data-testid="stTabs"] [role="tablist"] {
  gap: var(--jd-4);
  border-bottom: 1px solid var(--jd-rule);
}
[data-testid="stTabs"] button[role="tab"] {
  padding: 0.45rem 0 var(--jd-2);
  font-size: 0.9375rem;
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
  font-size: 0.75rem !important;
  letter-spacing: 0.02em;
  font-weight: 500;
  color: var(--jd-ink-2) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--jd-mono);
  font-size: 1.25rem !important;
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
  font-size: 0.875rem;
  font-weight: 550;
  color: var(--jd-ink);
  padding: var(--jd-2) var(--jd-3);
}
[data-testid="stExpander"] summary:hover { background: var(--jd-sheet); }
[data-testid="stExpander"] summary p { font-size: 0.875rem; color: var(--jd-ink); }
[data-testid="stExpanderDetails"] { padding: var(--jd-1) var(--jd-3) var(--jd-3); }

[data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
  font-family: var(--jd-mono);
  font-size: 0.8125rem;
}
[data-testid="stSlider"] label p { font-size: 0.875rem; color: var(--jd-ink-2); }

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
  padding: var(--jd-3) var(--jd-4);
}
[data-testid="stAlert"] p { font-size: 0.875rem; color: var(--jd-ink-2); }

/* ---------- composed pieces ---------- */
.jd-head { margin: 0 0 var(--jd-5); }
.stApp .jd-h1 {
  font-size: 1.5rem !important;
  font-weight: 600;
  letter-spacing: -0.016em;
  line-height: 1.22;
  color: var(--jd-ink);
  margin: 0;
}
.stApp .jd-sub {
  font-size: 0.9375rem;
  color: var(--jd-ink-2);
  margin: var(--jd-2) 0 0;
  max-width: 62ch;
  line-height: 1.6;
}

.jd-card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--jd-4);
  margin: 0 0 var(--jd-4);
}
.stApp .jd-card__title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--jd-ink);
  margin: 0;
}
.stApp .jd-card__note {
  font-size: 0.8125rem;
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
  font-size: 0.875rem;
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
  font-size: 0.8125rem;
}

.jd-empty {
  border: 1px dashed var(--jd-rule);
  border-radius: var(--jd-radius-sm);
  padding: var(--jd-5) var(--jd-4);
  text-align: center;
  background: transparent;
}
.stApp .jd-empty__title { font-size: 0.9375rem; font-weight: 600; color: var(--jd-ink); margin: 0; }
.stApp .jd-empty__body {
  font-size: 0.875rem;
  color: var(--jd-ink-2);
  margin: var(--jd-2) auto 0;
  line-height: 1.55;
  max-width: 34ch;
}

/* an unboxed panel: session information and other secondary blocks */
.jd-panel__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--jd-3);
  border-top: 1px solid var(--jd-rule);
  padding-top: var(--jd-3);
  margin: 0 0 var(--jd-3);
}
.stApp .jd-panel__title {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--jd-ink-2);
  margin: 0;
}
.stApp .jd-panel__note { font-size: 0.8125rem; color: var(--jd-ink-2); margin: 0; }

.jd-note {
  border-left: 2px solid var(--jd-rule);
  padding: var(--jd-1) 0 var(--jd-1) var(--jd-3);
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--jd-ink-2);
  margin: var(--jd-3) 0;
  max-width: 68ch;
}
/* the unavailable state is marked with weight, not decoration */
.jd-note--warn { border-left-color: var(--jd-ink); color: var(--jd-ink); }

.stApp .jd-meta { font-size: 0.8125rem; color: var(--jd-ink-2); margin: var(--jd-2) 0 0; line-height: 1.55; }
.jd-meta--mono { font-family: var(--jd-mono); font-variant-numeric: tabular-nums; }

.jd-list { margin: var(--jd-2) 0 0; padding-left: 1.05rem; max-width: 72ch; }
.jd-list li { font-size: 0.9375rem; color: var(--jd-ink-2); line-height: 1.6; margin-bottom: var(--jd-2); }

/* numbered steps: a list, not three competing columns */
.jd-steps { display: flex; flex-direction: column; gap: var(--jd-3); margin: var(--jd-2) 0 0; max-width: 72ch; }
.jd-step { display: flex; gap: var(--jd-3); align-items: baseline; }
.jd-step__num {
  font-family: var(--jd-mono);
  font-size: 0.8125rem;
  color: var(--jd-mark);
  letter-spacing: 0.02em;
  flex: 0 0 auto;
  min-width: 1.4rem;
}
.jd-step__body { min-width: 0; }
.jd-step__body b { display: block; font-size: 0.9375rem; color: var(--jd-ink); font-weight: 600; }
.jd-step__body span { display: block; font-size: 0.875rem; color: var(--jd-ink-2); line-height: 1.55; margin-top: 2px; }

/* the workflow as one understated, wrapping line */
.stApp .jd-flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--jd-2) var(--jd-4);
  margin: var(--jd-2) 0 0;
  font-size: 0.875rem;
  color: var(--jd-ink-2);
}
.jd-flow__item { display: inline-flex; align-items: baseline; gap: var(--jd-2); }
.jd-flow__n {
  font-family: var(--jd-mono);
  font-size: 0.75rem;
  color: var(--jd-mark);
  font-variant-numeric: tabular-nums;
}
.jd-flow__label { color: var(--jd-ink-2); }
.jd-flow__sep { color: var(--jd-rule); }

/* the latest real result, shown as a real annotated output */
.jd-last { display: flex; flex-direction: column; gap: var(--jd-2); margin: var(--jd-3) 0 0; }
.stApp .jd-last__meta {
  font-family: var(--jd-mono);
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink-2);
  margin: 0;
  overflow-wrap: anywhere;
}

/* specimen plate: retained primitive, no longer used on Home */
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
  font-size: 0.8125rem;
  color: var(--jd-ink-2);
  margin: var(--jd-2) 0 0;
}

/* developer page sections */
.stApp .jd-section {
  font-size: 1.0625rem !important;
  font-weight: 600;
  color: var(--jd-ink);
  margin: var(--jd-5) 0 var(--jd-1);
}
.stApp .jd-section__note { font-size: 0.8125rem; color: var(--jd-ink-2); margin: 0 0 var(--jd-2); }

.jd-readout { border-top: 1px solid var(--jd-rule); margin: var(--jd-2) 0; }
.jd-readout__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--jd-4);
  padding: var(--jd-2) 0;
  border-bottom: 1px solid var(--jd-rule);
  font-size: 0.875rem;
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
  .jd-dets { font-size: 0.875rem; }
  .jd-det { grid-template-columns: 10px minmax(3rem, 1fr) 3.4rem; }
  .jd-det__bar { display: none; }
  .jd-flow { gap: var(--jd-1) var(--jd-3); }
  [data-testid="stFileUploaderDropzone"] { padding: var(--jd-6) var(--jd-4) !important; }
}
</style>
"""


def inject_theme() -> None:
    """Apply the application stylesheet (static CSS only)."""
    st.markdown(_CSS, unsafe_allow_html=True)
