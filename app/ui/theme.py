"""Design system for the JUDEtector interface — the proof sheet.

The interface behaves like a proof sheet rather than a dashboard: the page is a
neutral sheet, images are mounted prints with a hairline registration mark, and a
monospace caption strip states the facts about each one. Colour is reserved for
marking — the ochre of a chinagraph pencil — and appears only where the model has
marked an image or where a reader can act.

Two rules worth knowing before editing:

* **Ochre is not a surface.** `--jd-mark` may fill an action, underline the active
  navigation entry, draw a focus ring or outline a detection. It may never become a
  panel, a badge background or a tinted section.
* **Contrast is measured, not eyeballed.** Every ink/surface pair is asserted in
  `tests/test_ui_styles.py`; interactive boundaries use `--jd-ink-2` (7.2:1) rather
  than the decorative `--jd-rule` (1.6:1).

As much of the palette as Streamlit can carry lives in `.streamlit/config.toml`.
This stylesheet holds what the theme cannot express: the mount, the caption strip,
the readout, the flow rule, and the internals of the uploader and expander.

`inject_theme()` emits static CSS only, so `unsafe_allow_html` carries no risk.
"""

from __future__ import annotations

import streamlit as st

__all__ = ["PALETTE", "MONO_FAMILY", "SANS_FAMILY", "inject_theme"]


# Tokens mirror `.streamlit/config.toml`, which styles Streamlit's own widgets.
PALETTE: dict[str, str] = {
    "sheet": "#F4F2ED",  # page ground
    "mount": "#FFFFFF",  # image mounts, input surfaces, widget fills
    "ink": "#16181A",  # text, primary action fill
    "ink_secondary": "#52585C",  # secondary text, interactive borders
    "rule": "#D0CBC1",  # hairlines, registration marks (decorative only)
    "mark": "#8A5A00",  # marking colour: actions, active state, focus, annotations
    "mark_hover": "#6F4900",
    "art_canvas": "#EFECE4",  # specimen plate ground (neutral, unmarked)
    "art_shape": "#DAD5C9",  # specimen figure (neutral, unmarked)
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
  --jd-ink: #16181A;
  --jd-ink-2: #52585C;
  --jd-rule: #D0CBC1;
  --jd-mark: #8A5A00;
  --jd-mark-hover: #6F4900;
  --jd-art-canvas: #EFECE4;
  --jd-art-shape: #DAD5C9;
  --jd-focus: 0 0 0 3px rgba(138, 90, 0, 0.30);

  /* spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 */
  --jd-1: 0.25rem;
  --jd-2: 0.5rem;
  --jd-3: 0.75rem;
  --jd-4: 1rem;
  --jd-5: 1.5rem;
  --jd-6: 2rem;
  --jd-7: 3rem;
  --jd-8: 4rem;
  --jd-9: 6rem;

  /* square corners: a printed sheet, not a component library */
  --jd-radius: 2px;

  --jd-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
    Arial, sans-serif;
  --jd-mono: ui-monospace, SFMono-Regular, "SF Mono", "Cascadia Mono", Menlo,
    Consolas, monospace;
}

/* ---------- sheet ---------- */
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
  padding: var(--jd-6) var(--jd-8) var(--jd-8);
  max-width: 1120px;
}
@media (max-width: 900px) {
  .block-container { padding: var(--jd-4) var(--jd-4) var(--jd-7); }
}

/* ---------- type ---------- */
.stApp h1 { font-size: 1.5rem !important; font-weight: 600; letter-spacing: -0.018em; line-height: 1.24; padding: 0; }
.stApp h2 { font-size: 1.06rem !important; font-weight: 600; letter-spacing: -0.008em; }
.stApp h3 { font-size: 0.94rem !important; font-weight: 600; }
.stApp p, .stApp li { font-size: 0.94rem; line-height: 1.62; color: var(--jd-ink-2); }
.stApp strong { color: var(--jd-ink); font-weight: 600; }
[data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
  font-size: 0.78rem !important;
  color: var(--jd-ink-2) !important;
  line-height: 1.5;
}
.stApp code {
  background: var(--jd-art-canvas);
  color: var(--jd-ink);
  border-radius: var(--jd-radius);
  padding: 0.06em 0.32em;
  font-family: var(--jd-mono);
  font-size: 0.86em;
}
[data-testid="stMarkdownContainer"] a {
  color: var(--jd-mark);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}
[data-testid="stMarkdownContainer"] a:hover { color: var(--jd-mark-hover); }
hr { border: 0; border-top: 1px solid var(--jd-rule); margin: var(--jd-5) 0; }

/* ---------- navigation ---------- */
[data-testid="stSidebar"] {
  background: var(--jd-mount);
  border-right: 1px solid var(--jd-rule);
  min-width: 214px;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: var(--jd-3); }
[data-testid="stSidebarNav"] { padding: var(--jd-2) var(--jd-3) var(--jd-3); }
[data-testid="stSidebarNavItems"] { gap: 1px; }
[data-testid="stSidebarNavLink"] {
  border-radius: var(--jd-radius) !important;
  padding: 0.42rem 0.6rem !important;
  color: var(--jd-ink-2) !important;
  font-size: 0.88rem;
  font-weight: 500;
  border-left: 2px solid transparent;
}
[data-testid="stSidebarNavLink"]:hover { background: var(--jd-sheet); color: var(--jd-ink) !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: transparent;
  border-left-color: var(--jd-mark);
  color: var(--jd-ink) !important;
  font-weight: 600;
}
[data-testid="stSidebarNavLink"] span { font-size: 0.88rem; }
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {
  color: currentColor;
  font-size: 18px;
  opacity: 0.8;
}
[data-testid="stSidebarNavSeparator"] { border-color: var(--jd-rule); }

/* ---------- actions ---------- */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
  border-radius: var(--jd-radius);
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
[data-testid="stBaseButton-primary"]:focus-visible {
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

/* ---------- file uploader ----------
   Streamlit paints the dropzone <section> with `theme.colors.secondaryBg`, which is
   #FFFFFF in .streamlit/config.toml, so the resting surface is white at the theme
   level and not only by override. Everything below refines border, text and states. */
[data-testid="stFileUploaderDropzone"] {
  background: var(--jd-mount) !important;
  border: 1.5px dashed var(--jd-ink-2) !important;
  border-radius: var(--jd-radius) !important;
  padding: var(--jd-5) var(--jd-4) !important;
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
  border-radius: var(--jd-radius) !important;
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
  font-size: 0.88rem;
  color: var(--jd-ink);
  font-weight: 550;
}

/* ---------- expander, slider, table ---------- */
[data-testid="stExpander"] {
  border: 1px solid var(--jd-rule);
  border-radius: var(--jd-radius);
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
  font-size: 0.78rem;
}
[data-testid="stSlider"] label p { font-size: 0.84rem; color: var(--jd-ink-2); }

[data-testid="stDataFrame"] {
  border: 1px solid var(--jd-rule);
  border-radius: var(--jd-radius);
  overflow: hidden;
}

/* ---------- prints: Streamlit images are mounted like the drawn plates ---------- */
[data-testid="stImage"] {
  position: relative;
  margin: 0;
  padding: var(--jd-2);
  background: var(--jd-mount);
  border: 1px solid var(--jd-rule);
  border-radius: var(--jd-radius);
}
[data-testid="stImage"]::before,
[data-testid="stImage"]::after {
  content: "";
  position: absolute;
  width: 9px;
  height: 9px;
  border: 0 solid var(--jd-rule);
  pointer-events: none;
}
[data-testid="stImage"]::before { top: -5px; left: -5px; border-top-width: 1px; border-left-width: 1px; }
[data-testid="stImage"]::after { bottom: -5px; right: -5px; border-bottom-width: 1px; border-right-width: 1px; }
[data-testid="stImage"] img {
  border: 0;
  border-radius: var(--jd-radius);
  display: block;
  width: 100%;
  height: auto;
}
[data-testid="stCameraInput"] video,
[data-testid="stCameraInput"] img { border-radius: var(--jd-radius); }
[data-testid="stAlert"] {
  border-radius: var(--jd-radius);
  border: 1px solid var(--jd-rule);
  background: var(--jd-mount);
  padding: var(--jd-2) var(--jd-3);
}
[data-testid="stAlert"] p { font-size: 0.88rem; color: var(--jd-ink-2); }

/* ---------- metrics (developer page only) ---------- */
[data-testid="stMetric"] {
  background: transparent;
  border: 0;
  border-top: 1px solid var(--jd-rule);
  border-radius: 0;
  padding: var(--jd-3) 0 0;
  box-shadow: none;
  height: 100%;
}
[data-testid="stMetricLabel"] p {
  font-family: var(--jd-mono);
  font-size: 0.72rem !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-weight: 500;
  color: var(--jd-ink-2) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--jd-mono);
  font-size: 1.06rem !important;
  font-weight: 500;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink);
}

/* ---------- composed pieces ---------- */
.jd-head { margin: 0 0 var(--jd-6); }
.stApp .jd-h1 {
  font-size: 1.5rem !important;
  font-weight: 600;
  letter-spacing: -0.018em;
  line-height: 1.24;
  color: var(--jd-ink);
  margin: 0;
}
.stApp .jd-sub {
  font-size: 0.94rem;
  color: var(--jd-ink-2);
  margin: var(--jd-2) 0 0;
  max-width: 56ch;
  line-height: 1.6;
}
.jd-plate {
  position: relative;
  background: var(--jd-mount);
  border: 1px solid var(--jd-rule);
  border-radius: var(--jd-radius);
  padding: var(--jd-2);
  margin: 0;
}
/* restrained registration marks: two corners, hairlines, outside the mount */
.jd-plate::before,
.jd-plate::after {
  content: "";
  position: absolute;
  width: 9px;
  height: 9px;
  border: 0 solid var(--jd-rule);
  pointer-events: none;
}
.jd-plate::before { top: -5px; left: -5px; border-top-width: 1px; border-left-width: 1px; }
.jd-plate::after { bottom: -5px; right: -5px; border-bottom-width: 1px; border-right-width: 1px; }
.jd-plate__art { background: var(--jd-art-canvas); border-radius: var(--jd-radius); overflow: hidden; line-height: 0; }
.jd-plate__art svg { display: block; width: 100%; height: auto; }

.jd-caption {
  display: flex;
  flex-wrap: wrap;
  gap: var(--jd-1) var(--jd-4);
  align-items: baseline;
  border-top: 1px solid var(--jd-rule);
  margin-top: var(--jd-2);
  padding-top: var(--jd-2);
  font-family: var(--jd-mono);
  font-size: 0.78rem;
  color: var(--jd-ink);
}
.jd-caption__field { display: inline-flex; gap: var(--jd-1); align-items: baseline; min-width: 0; }
.jd-caption__label {
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--jd-ink-2);
}
.jd-caption__value { color: var(--jd-ink); overflow-wrap: anywhere; }

/* fixed-column readout: label left, mono value right, aligned down the block */
.jd-readout {
  display: grid;
  grid-template-columns: minmax(7.5rem, 9.5rem) 1fr;
  column-gap: var(--jd-4);
  row-gap: var(--jd-2);
  align-items: baseline;
  border-top: 1px solid var(--jd-rule);
  padding-top: var(--jd-3);
  margin: var(--jd-3) 0;
  max-width: 30rem;
}
.jd-readout__label {
  font-family: var(--jd-mono);
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--jd-ink-2);
}
.jd-readout__value {
  font-family: var(--jd-mono);
  font-size: 0.88rem;
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink);
  text-align: right;
  overflow-wrap: anywhere;
}

.stApp .jd-flow {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--jd-2) var(--jd-4);
  border-top: 1px solid var(--jd-rule);
  margin-top: var(--jd-7);
  padding-top: var(--jd-3);
  font-size: 0.78rem;
  color: var(--jd-ink-2);
}

/* section: a rule and a title, no card */
.jd-section {
  border-top: 1px solid var(--jd-rule);
  margin: var(--jd-6) 0 var(--jd-3);
  padding-top: var(--jd-2);
}
.stApp .jd-section__title {
  font-size: 1.06rem;
  font-weight: 600;
  letter-spacing: -0.008em;
  color: var(--jd-ink);
  margin: 0;
}
.stApp .jd-section__sub {
  font-size: 0.88rem;
  color: var(--jd-ink-2);
  margin: var(--jd-1) 0 0;
}

.jd-note {
  border-left: 2px solid var(--jd-rule);
  padding: var(--jd-1) 0 var(--jd-1) var(--jd-3);
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--jd-ink-2);
  margin: var(--jd-3) 0;
  max-width: 62ch;
}
/* the unavailable state is marked with weight, not colour */
.jd-note--warn { border-left-color: var(--jd-ink); color: var(--jd-ink); }

.jd-empty {
  border-top: 1px solid var(--jd-rule);
  padding-top: var(--jd-3);
  margin: var(--jd-4) 0;
}
.stApp .jd-empty__title { font-size: 0.94rem; font-weight: 600; color: var(--jd-ink); margin: 0; }
.stApp .jd-empty__body {
  font-size: 0.88rem;
  color: var(--jd-ink-2);
  margin: var(--jd-1) 0 0;
  line-height: 1.6;
  max-width: 56ch;
}

.stApp .jd-meta {
  font-size: 0.78rem;
  color: var(--jd-ink-2);
  margin: var(--jd-2) 0 0;
}

.jd-list { margin: var(--jd-2) 0 0; padding-left: 1.05rem; max-width: 66ch; }
.jd-list li { font-size: 0.94rem; color: var(--jd-ink-2); line-height: 1.65; margin-bottom: var(--jd-1); }

.jd-steps { margin: var(--jd-3) 0 0; max-width: 66ch; }
.jd-step { display: flex; gap: var(--jd-3); padding: var(--jd-2) 0; align-items: baseline; }
.jd-step + .jd-step { border-top: 1px solid var(--jd-rule); }
.jd-step__num {
  flex: 0 0 auto;
  font-family: var(--jd-mono);
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink-2);
  min-width: 1.1rem;
}
.jd-step__body b { display: block; font-size: 0.94rem; color: var(--jd-ink); font-weight: 600; }
.jd-step__body span {
  display: block;
  font-size: 0.88rem;
  color: var(--jd-ink-2);
  line-height: 1.6;
  margin-top: 2px;
}

/* ---------- landing ---------- */
.stApp .jd-display {
  font-size: 2.4rem !important;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.08;
  color: var(--jd-ink);
  margin: 0;
  max-width: 20ch;
}
.stApp .jd-intro {
  font-size: 1.06rem;
  line-height: 1.6;
  color: var(--jd-ink-2);
  margin: var(--jd-3) 0 0;
  max-width: 54ch;
}
@media (max-width: 860px) {
  .stApp .jd-display { font-size: 2rem !important; max-width: none; }
}
.stApp .jd-plate__note {
  font-family: var(--jd-mono);
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  color: var(--jd-ink-2);
  margin: var(--jd-3) 0 0;
}
.stApp .jd-plate-label {
  font-family: var(--jd-mono);
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--jd-ink-2);
  margin: var(--jd-2) 0 0;
  border-top: 1px solid var(--jd-rule);
  padding-top: var(--jd-2);
}

/* ---------- footer ---------- */
.jd-footer {
  border-top: 1px solid var(--jd-rule);
  margin-top: var(--jd-6);
  padding-top: var(--jd-3);
}
.stApp .jd-footer__brand {
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: -0.005em;
  color: var(--jd-ink);
}
.stApp .jd-footer__note {
  font-size: 0.78rem;
  line-height: 1.55;
  color: var(--jd-ink-2);
  margin: var(--jd-1) 0 0;
  max-width: 60ch;
}

@media (max-width: 760px) {
  .jd-readout { grid-template-columns: 1fr; row-gap: var(--jd-1); }
  .jd-readout__value { text-align: left; }
  .jd-flow { flex-direction: column; gap: var(--jd-1); }
  .jd-footer { margin-top: var(--jd-5); }
}
</style>
"""


def inject_theme() -> None:
    """Apply the application stylesheet (static CSS only)."""
    st.markdown(_CSS, unsafe_allow_html=True)
