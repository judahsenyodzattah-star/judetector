"""Design system for the JUDEtector interface.

One stylesheet, one type scale, one spacing scale. The visual language is
deliberately plain: warm off-white canvas, charcoal ink, a single teal accent used
only for interactive meaning, hairline rules instead of cards, and no decorative
fills or icons.

Two rules worth knowing before editing:

* **No tinted resting surfaces.** Pale teal is reserved for hover/active states of
  interactive elements. Nothing sits on a coloured panel.
* **Contrast is measured, not eyeballed.** Every ink/surface pair is asserted in
  `tests/test_ui_styles.py`; muted ink is dark enough to clear 4.5:1 on the canvas,
  and the uploader's control border clears 3:1.

The stylesheet is injected with `inject_theme()` and contains only static CSS, so
`unsafe_allow_html` carries no injection risk.
"""

from __future__ import annotations

import streamlit as st

__all__ = ["PALETTE", "inject_theme"]


# Tokens mirror `.streamlit/config.toml`, which styles Streamlit's own widgets.
PALETTE: dict[str, str] = {
    "bg": "#FAFAF8",
    "surface": "#FFFFFF",
    "sunken": "#F4F2EE",
    "active": "#EDEAE3",
    "line": "#E3E0D9",
    "line_strong": "#CFCAC0",
    "ink": "#15181A",
    "ink_secondary": "#4C545B",
    "ink_muted": "#6B7278",
    "accent": "#0F766E",
    "accent_hover": "#115E59",
    "accent_ink": "#0B5F58",
    "accent_tint": "#EAF6F3",
    "control_border": "#948C7F",
    "art_canvas": "#F1EDE4",
    "art_shape": "#D7CDBC",
    "warn": "#8A4B0B",
}

_CSS = """
<style>
:root {
  --jd-bg: #FAFAF8;
  --jd-surface: #FFFFFF;
  --jd-sunken: #F4F2EE;
  --jd-active: #EDEAE3;
  --jd-line: #E3E0D9;
  --jd-line-strong: #CFCAC0;
  --jd-ink: #15181A;
  --jd-ink-2: #4C545B;
  --jd-ink-3: #6B7278;
  --jd-accent: #0F766E;
  --jd-accent-hover: #115E59;
  --jd-accent-ink: #0B5F58;
  --jd-accent-tint: #EAF6F3;
  --jd-control-border: #948C7F;
  --jd-art-canvas: #F1EDE4;
  --jd-art-shape: #D7CDBC;
  --jd-warn: #8A4B0B;

  /* spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 */
  --jd-1: 0.25rem;
  --jd-2: 0.5rem;
  --jd-3: 0.75rem;
  --jd-4: 1rem;
  --jd-5: 1.5rem;
  --jd-6: 2rem;
  --jd-7: 3rem;
  --jd-8: 4rem;

  --jd-radius: 10px;
  --jd-radius-sm: 7px;
  --jd-focus: 0 0 0 3px rgba(15, 118, 110, 0.22);
}

/* ---------- canvas ---------- */
.stApp, [data-testid="stAppViewContainer"] { background: var(--jd-bg); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp select, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.stApp { color: var(--jd-ink); }

#MainMenu, footer, [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; }

.block-container {
  padding: var(--jd-6) var(--jd-6) var(--jd-8);
  max-width: 1060px;
}
@media (max-width: 900px) {
  .block-container { padding: var(--jd-4) var(--jd-4) var(--jd-7); }
}

/* ---------- type scale ---------- */
.stApp h1 {
  font-size: 1.55rem !important;
  font-weight: 600;
  letter-spacing: -0.021em;
  line-height: 1.25;
  color: var(--jd-ink);
  padding: 0;
}
.stApp h2 { font-size: 1.05rem !important; font-weight: 600; letter-spacing: -0.012em; }
.stApp h3 { font-size: 0.94rem !important; font-weight: 600; }
.stApp p, .stApp li {
  font-size: 0.94rem;
  line-height: 1.62;
  color: var(--jd-ink-2);
}
.stApp strong { color: var(--jd-ink); font-weight: 600; }
.stApp h1 code, .stApp h2 code, .stApp h3 code { font-size: 0.9em; }
[data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
  font-size: 0.78rem !important;
  color: var(--jd-ink-3) !important;
  line-height: 1.5;
}
.stApp code {
  background: var(--jd-sunken);
  color: var(--jd-ink);
  border-radius: 4px;
  padding: 0.06em 0.32em;
  font-size: 0.85em;
}
[data-testid="stMarkdownContainer"] a {
  color: var(--jd-accent-ink);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
}
[data-testid="stMarkdownContainer"] a:hover { color: var(--jd-accent-hover); }
hr { border: 0; border-top: 1px solid var(--jd-line); margin: var(--jd-5) 0; }

/* ---------- sidebar + navigation ---------- */
[data-testid="stSidebar"] {
  background: var(--jd-surface);
  border-right: 1px solid var(--jd-line);
  min-width: 218px;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: var(--jd-3); }
[data-testid="stSidebarNav"] { padding: var(--jd-2) var(--jd-3) var(--jd-3); }
[data-testid="stSidebarNavItems"] { gap: 2px; }
[data-testid="stSidebarNavLink"] {
  border-radius: var(--jd-radius-sm) !important;
  padding: 0.4rem 0.5rem !important;
  color: var(--jd-ink-2) !important;
  font-size: 0.88rem;
  font-weight: 500;
  transition: background 0.12s ease, color 0.12s ease;
}
[data-testid="stSidebarNavLink"]:hover {
  background: var(--jd-sunken);
  color: var(--jd-ink) !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: var(--jd-active);
  box-shadow: inset 2px 0 0 var(--jd-accent);
  color: var(--jd-ink) !important;
  font-weight: 600;
}
[data-testid="stSidebarNavLink"] span { font-size: 0.88rem; }
[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {
  color: currentColor;
  font-size: 18px;
  opacity: 0.85;
}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {
  color: var(--jd-ink) !important;
}
[data-testid="stSidebarNavSeparator"] { border-color: var(--jd-line); }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { padding: 0 var(--jd-3); }

/* ---------- buttons ---------- */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-line-strong);
  background: var(--jd-surface);
  color: var(--jd-ink);
  font-size: 0.84rem;
  font-weight: 550;
  padding: 0.44rem 0.85rem;
  transition: background 0.12s ease, border-color 0.12s ease;
}
[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-tertiary"]:hover {
  background: var(--jd-sunken);
  border-color: var(--jd-control-border);
  color: var(--jd-ink);
}
[data-testid="stButton"] button:focus-visible,
[data-testid="stDownloadButton"] button:focus-visible,
[data-testid="stBaseButton-secondary"]:focus-visible,
[data-testid="stBaseButton-primary"]:focus-visible {
  outline: none;
  box-shadow: var(--jd-focus);
}
[data-testid="stBaseButton-primary"] {
  background: var(--jd-accent) !important;
  border: 1px solid var(--jd-accent) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
}
[data-testid="stBaseButton-primary"]:hover {
  background: var(--jd-accent-hover) !important;
  border-color: var(--jd-accent-hover) !important;
  color: #FFFFFF !important;
}
.stApp button:disabled, .stApp button[disabled] {
  background: var(--jd-sunken) !important;
  border-color: var(--jd-line) !important;
  color: var(--jd-ink-3) !important;
  cursor: not-allowed !important;
}
.stApp :focus-visible { outline: 2px solid var(--jd-accent); outline-offset: 2px; }

/* ---------- file uploader ----------
   Streamlit paints the dropzone with `theme.colors.secondaryBg`, which is set to
   #FFFFFF in .streamlit/config.toml, so the resting surface is white at the theme
   level and not only by override. Everything below refines border, text and states. */
[data-testid="stFileUploaderDropzone"] {
  background: var(--jd-surface) !important;
  border: 1.5px dashed var(--jd-control-border) !important;
  border-radius: var(--jd-radius) !important;
  padding: var(--jd-5) var(--jd-4) !important;
  flex-direction: column;
  align-items: center;
  gap: var(--jd-2);
  text-align: center;
  transition: border-color 0.12s ease, background 0.12s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--jd-accent) !important;
  background: var(--jd-surface) !important;
}
[data-testid="stFileUploaderDropzone"]:focus-within {
  border-color: var(--jd-accent) !important;
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
  background: var(--jd-surface) !important;
  color: var(--jd-accent-ink) !important;
  border: 1px solid var(--jd-accent) !important;
  border-radius: var(--jd-radius-sm) !important;
  font-size: 0.84rem !important;
  font-weight: 600 !important;
  padding: 0.4rem 0.8rem !important;
}
[data-testid="stFileUploader"] button:hover {
  background: var(--jd-accent-tint) !important;
  color: var(--jd-accent-ink) !important;
  border-color: var(--jd-accent-hover) !important;
}
[data-testid="stFileUploader"] button:focus-visible {
  outline: none !important;
  box-shadow: var(--jd-focus) !important;
}
[data-testid="stFileUploader"] button:disabled {
  background: var(--jd-sunken) !important;
  border-color: var(--jd-line) !important;
  color: var(--jd-ink-3) !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInput"] { cursor: pointer; }
[data-testid="stWidgetLabel"] p {
  font-size: 0.88rem;
  color: var(--jd-ink);
  font-weight: 550;
}

/* ---------- expanders ---------- */
[data-testid="stExpander"] {
  border: 1px solid var(--jd-line);
  border-radius: var(--jd-radius);
  background: var(--jd-surface);
  box-shadow: none;
  overflow: hidden;
}
[data-testid="stExpander"] summary {
  font-size: 0.84rem;
  font-weight: 550;
  color: var(--jd-ink);
  padding: var(--jd-2) var(--jd-3);
}
[data-testid="stExpander"] summary:hover { background: var(--jd-sunken); }
[data-testid="stExpander"] summary p { font-size: 0.84rem; color: var(--jd-ink); }
[data-testid="stExpanderDetails"] { padding: var(--jd-1) var(--jd-3) var(--jd-3); }

[data-testid="stSlider"] [data-testid="stSliderThumbValue"] { font-size: 0.78rem; }
[data-testid="stSlider"] label p { font-size: 0.84rem; color: var(--jd-ink-2); }

/* ---------- data, images, camera ---------- */
[data-testid="stDataFrame"] {
  border: 1px solid var(--jd-line);
  border-radius: var(--jd-radius-sm);
  overflow: hidden;
}
[data-testid="stDataFrame"] [role="columnheader"] { background: var(--jd-sunken) !important; }
[data-testid="stImage"] img {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-line);
  display: block;
}
[data-testid="stCameraInput"] video,
[data-testid="stCameraInput"] img { border-radius: var(--jd-radius-sm); }
[data-testid="stAlert"] {
  border-radius: var(--jd-radius-sm);
  border: 1px solid var(--jd-line);
  background: var(--jd-surface);
  padding: var(--jd-2) var(--jd-3);
}
[data-testid="stAlert"] p { font-size: 0.88rem; color: var(--jd-ink-2); }

/* ---------- metrics: numbers, not cards ---------- */
[data-testid="stMetric"] {
  background: transparent;
  border: 0;
  border-top: 1px solid var(--jd-line);
  border-radius: 0;
  padding: var(--jd-3) 0 0;
  box-shadow: none;
  height: 100%;
}
[data-testid="stMetricLabel"] p {
  font-size: 0.78rem !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--jd-ink-3) !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.55rem !important;
  font-weight: 600;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink);
}
[data-testid="stMetricDelta"] { font-size: 0.78rem; }

/* ---------- text pieces ---------- */
.jd-head { margin: 0 0 var(--jd-5); }
.stApp .jd-h1 {
  font-size: 1.55rem !important;
  font-weight: 600;
  letter-spacing: -0.021em;
  line-height: 1.25;
  color: var(--jd-ink);
  margin: 0;
}
.stApp .jd-sub {
  font-size: 0.94rem;
  color: var(--jd-ink-2);
  margin: var(--jd-2) 0 0;
  max-width: 54ch;
  line-height: 1.6;
}

/* section label: a hairline and small caps, no card */
.jd-section {
  border-top: 1px solid var(--jd-line);
  margin: var(--jd-6) 0 var(--jd-3);
  padding-top: var(--jd-3);
}
.stApp .jd-section__title {
  font-size: 0.78rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 600;
  color: var(--jd-ink-3);
  margin: 0;
}
.stApp .jd-section__sub {
  font-size: 0.84rem;
  color: var(--jd-ink-3);
  margin: var(--jd-1) 0 0;
}

.jd-note {
  border-left: 2px solid var(--jd-line-strong);
  padding: var(--jd-1) 0 var(--jd-1) var(--jd-3);
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--jd-ink-2);
  margin: var(--jd-3) 0;
}
.jd-note--warn { border-left-color: var(--jd-warn); }
.jd-note--ok { border-left-color: var(--jd-accent); }

.jd-empty {
  border-top: 1px solid var(--jd-line);
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

.stApp .jd-meta { font-size: 0.78rem; color: var(--jd-ink-3); margin: var(--jd-2) 0 0; }

.jd-kv { display: flex; flex-wrap: wrap; gap: var(--jd-5); margin: var(--jd-2) 0; }
.jd-kv__item { font-size: 0.78rem; color: var(--jd-ink-3); }
.jd-kv__item b {
  display: block;
  font-size: 0.84rem;
  color: var(--jd-ink);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.jd-list { margin: var(--jd-2) 0 0; padding-left: 1.05rem; }
.jd-list li { font-size: 0.94rem; color: var(--jd-ink-2); line-height: 1.65; margin-bottom: var(--jd-1); }

.jd-steps { margin: var(--jd-3) 0 0; }
.jd-step { display: flex; gap: var(--jd-3); padding: var(--jd-2) 0; align-items: baseline; }
.jd-step + .jd-step { border-top: 1px solid var(--jd-line); }
.jd-step__num {
  flex: 0 0 auto;
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
  color: var(--jd-ink-3);
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

/* ---------- landing page ---------- */
.jd-intro-grid { display: flex; gap: var(--jd-7); align-items: flex-start; }
.jd-intro-grid__copy { flex: 1 1 56%; min-width: 0; }
.jd-intro-grid__aside { flex: 1 1 44%; min-width: 0; }
.stApp .jd-display {
  font-size: 2.75rem !important;
  font-weight: 600;
  letter-spacing: -0.032em;
  line-height: 1.06;
  color: var(--jd-ink);
  margin: 0;
  max-width: 18ch;
}
.stApp .jd-intro {
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--jd-ink-2);
  margin: var(--jd-4) 0 0;
  max-width: 46ch;
}
@media (max-width: 860px) {
  .jd-intro-grid { flex-direction: column; gap: var(--jd-5); }
  .stApp .jd-display { font-size: 2.1rem !important; max-width: none; }
  .jd-intro-grid__copy, .jd-intro-grid__aside { flex: 1 1 auto; width: 100%; }
}

.jd-specimen {
  border: 1px solid var(--jd-line);
  border-radius: var(--jd-radius);
  background: var(--jd-surface);
  padding: var(--jd-2);
}
.jd-specimen__art {
  border-radius: var(--jd-radius-sm);
  overflow: hidden;
  background: var(--jd-art-canvas);
  line-height: 0;
}
.jd-specimen__art svg { width: 100%; height: auto; display: block; }
.stApp .jd-specimen__note {
  font-size: 0.78rem;
  color: var(--jd-ink-3);
  margin: var(--jd-2) var(--jd-1) var(--jd-1);
  text-align: left;
}

.stApp .jd-workflow {
  border-top: 1px solid var(--jd-line);
  margin-top: var(--jd-6);
  padding-top: var(--jd-3);
  font-size: 0.84rem;
  color: var(--jd-ink-3);
  letter-spacing: 0.01em;
}
.jd-workflow b { color: var(--jd-ink-2); font-weight: 550; }

/* ---------- footer ---------- */
.jd-footer {
  border-top: 1px solid var(--jd-line);
  margin-top: var(--jd-7);
  padding-top: var(--jd-3);
}
.stApp .jd-footer__brand {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--jd-ink);
  letter-spacing: -0.005em;
}
.stApp .jd-footer__note {
  font-size: 0.78rem;
  line-height: 1.55;
  color: var(--jd-ink-3);
  margin: var(--jd-1) 0 0;
  max-width: 60ch;
}

@media (max-width: 760px) {
  .jd-specimen { margin-top: var(--jd-2); }
  .jd-footer { margin-top: var(--jd-6); }
}
</style>
"""


def inject_theme() -> None:
    """Apply the application stylesheet (static CSS only)."""
    st.markdown(_CSS, unsafe_allow_html=True)
