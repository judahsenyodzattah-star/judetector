"""Guards for the shared stylesheet.

These are cheap, deterministic checks that catch the failure modes which are hard
to spot by reading CSS: dead Streamlit selectors, contrast regressions, and a
palette that drifts away from the Streamlit theme config.

Colour maths follows the WCAG 2.1 relative-luminance definition.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.core import config as app_config
from app.ui.theme import _CSS, PALETTE

pytestmark = pytest.mark.ui

PROJECT_ROOT = Path(app_config.PROJECT_ROOT)


# --------------------------------------------------------------------------
# Contrast
# --------------------------------------------------------------------------
def _luminance(hex_colour: str) -> float:
    value = hex_colour.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground: str, background: str) -> float:
    first, second = _luminance(foreground), _luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


TEXT_PAIRS = [
    ("body text on surface", "text", "surface"),
    ("body text on canvas", "text", "bg"),
    ("body text on the sunken fill", "text", "surface_sunken"),
    ("secondary text on surface", "text_secondary", "surface"),
    ("secondary text on canvas", "text_secondary", "bg"),
    ("secondary text on muted surface", "text_secondary", "surface_muted"),
    ("secondary text on the sunken fill", "text_secondary", "surface_sunken"),
    ("muted text on surface", "text_muted", "surface"),
    ("muted text on canvas", "text_muted", "bg"),
    ("accent text on surface", "accent_text", "surface"),
    ("accent text on the accent tint", "accent_text", "accent_tint"),
    ("accent icon on surface", "accent", "surface"),
    ("white on the accent button", "surface", "accent"),
    ("white on the accent hover", "surface", "accent_strong"),
    ("warning text on the warning tint", "warn", "warn_tint"),
]


@pytest.mark.parametrize(("name", "fg", "bg"), TEXT_PAIRS, ids=[p[0] for p in TEXT_PAIRS])
def test_text_pairs_meet_wcag_aa(name, fg, bg):
    """Ordinary text needs 4.5:1; anything less is a defect, not a preference."""
    ratio = contrast(PALETTE[fg], PALETTE[bg])
    assert ratio >= 4.5, f"{name} is {ratio:.2f}:1 (needs 4.5:1)"


def test_uploader_border_meets_non_text_contrast():
    """The dropzone border is the only affordance of a large empty region."""
    ratio = contrast(PALETTE["control_border"], PALETTE["surface"])
    assert ratio >= 3.0, f"uploader border is {ratio:.2f}:1 (needs 3:1)"


# --------------------------------------------------------------------------
# Uploader styling
# --------------------------------------------------------------------------
_CSS_RULES = re.sub(r"/\*.*?\*/", "", _CSS, flags=re.S)


def _rule(selector: str) -> str:
    """Return the declaration block for `selector`, including grouped selectors."""
    for block in re.finditer(r"([^{}]+)\{([^}]*)\}", _CSS_RULES):
        selectors = [part.strip() for part in block.group(1).split(",")]
        if selector in selectors:
            return block.group(2)
    raise AssertionError(f"no CSS rule for {selector}")


def test_uploader_uses_a_neutral_surface_not_a_saturated_fill():
    body = _rule('[data-testid="stFileUploaderDropzone"]')
    assert "var(--jd-surface)" in body
    assert "accent-tint" not in body
    assert "jd-accent;" not in body


def test_uploader_text_is_dark_on_light():
    instructions = _rule('[data-testid="stFileUploaderDropzoneInstructions"] span')
    assert "var(--jd-text-2)" in instructions
    # The instructions sit on the white dropzone, which the pair test already covers.
    assert contrast(PALETTE["text_secondary"], PALETTE["surface"]) >= 4.5


def test_uploader_defines_hover_focus_and_disabled_states():
    for selector in (
        '[data-testid="stFileUploaderDropzone"]:hover',
        '[data-testid="stFileUploaderDropzone"]:focus-within',
        '[data-testid="stFileUploader"] button:hover',
        '[data-testid="stFileUploader"] button:focus-visible',
        '[data-testid="stFileUploader"] button:disabled',
    ):
        assert _rule(selector)


def test_uploader_browse_button_is_teal_on_white():
    body = _rule('[data-testid="stFileUploader"] button')
    assert "var(--jd-accent-text)" in body
    assert "var(--jd-surface)" in body
    assert contrast(PALETTE["accent_text"], PALETTE["surface"]) >= 4.5


# --------------------------------------------------------------------------
# Responsive + focus
# --------------------------------------------------------------------------
def test_stylesheet_has_mobile_breakpoints():
    breakpoints = re.findall(r"@media \(max-width: (\d+)px\)", _CSS)
    assert "900" in breakpoints and "760" in breakpoints


def test_focus_visibility_is_styled():
    assert ":focus-visible" in _CSS
    assert "--jd-focus" in _CSS


# --------------------------------------------------------------------------
# Live selectors only
# --------------------------------------------------------------------------
def _bundle_text() -> str:
    """Concatenated Streamlit frontend bundle, or '' when unavailable."""
    candidates = sorted(
        (Path(app_config.PROJECT_ROOT).parent).glob("**/site-packages/streamlit/static/static/js/*.js")
    )
    candidates += sorted(Path("/home/user/.venv/lib").glob("python*/site-packages/streamlit/static/static/js/*.js"))
    if not candidates:
        return ""
    return "".join(path.read_text(encoding="utf-8", errors="ignore") for path in candidates[:400])


def test_every_styling_hook_exists_in_the_streamlit_bundle():
    """Dead selectors are invisible at runtime, so assert them against the bundle.

    Streamlit flattens some names into runtime strings (button kinds are built as
    ``stBaseButton-${kind}``), so those are matched by prefix.
    """
    import streamlit

    js_dir = Path(streamlit.__file__).parent / "static" / "static" / "js"
    if not js_dir.is_dir():
        pytest.skip("Streamlit frontend bundle not available in this environment")

    bundle = "".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in js_dir.glob("*.js")
    )
    testids = set(re.findall(r'\[data-testid="([^"]+)"\]', _CSS))
    assert testids, "no data-testid hooks found in the stylesheet"

    missing = []
    for testid in sorted(testids):
        probe = "stBaseButton-" if testid.startswith("stBaseButton-") else testid
        if probe not in bundle:
            missing.append(testid)
    assert not missing, f"selectors that cannot match any element: {missing}"


# --------------------------------------------------------------------------
# Palette / theme config agreement
# --------------------------------------------------------------------------
def test_streamlit_theme_config_matches_the_design_tokens():
    config_text = (PROJECT_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    expected = {
        "primaryColor": PALETTE["accent"],
        "backgroundColor": PALETTE["bg"],
        "secondaryBackgroundColor": PALETTE["surface_sunken"],
        "textColor": PALETTE["text"],
    }
    for key, value in expected.items():
        assert f'{key} = "{value}"' in config_text, f"{key} drifted from the palette"


def test_secondary_background_is_not_green_tinted():
    """A green secondary fill behind dark text was the reported contrast defect."""
    value = PALETTE["surface_sunken"].lstrip("#")
    red, green, blue = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    assert green - blue <= 6, "secondary surface has a green cast"
    assert green - red <= 6, "secondary surface has a green cast"


def test_stylesheet_only_injects_static_css():
    """No f-strings or interpolation: the sheet cannot carry user or model data."""
    source = (PROJECT_ROOT / "app" / "ui" / "theme.py").read_text(encoding="utf-8")
    css_block = source.split('_CSS = """', 1)[1].split('"""', 1)[0]
    assert "{" in css_block  # sanity: we captured the sheet
    assert "f\"" not in css_block and "f'" not in css_block
