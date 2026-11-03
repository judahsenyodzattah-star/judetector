"""Guards for the shared stylesheet.

These are deterministic checks for the failures that are invisible by reading CSS:
dead Streamlit selectors, contrast regressions, off-scale type, a palette that drifts
from the theme config, and the tinted-surface habit this interface deliberately
avoids.

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
_CSS_RULES = re.sub(r"/\*.*?\*/", "", _CSS, flags=re.S)


# --------------------------------------------------------------------------
# Contrast
# --------------------------------------------------------------------------
def _luminance(hex_colour: str) -> float:
    value = hex_colour.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground: str, background: str) -> float:
    first, second = _luminance(foreground), _luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


TEXT_PAIRS = [
    ("ink on surface", "ink", "surface"),
    ("ink on canvas", "ink", "bg"),
    ("ink on sunken", "ink", "sunken"),
    ("ink on active", "ink", "active"),
    ("secondary ink on surface", "ink_secondary", "surface"),
    ("secondary ink on canvas", "ink_secondary", "bg"),
    ("secondary ink on sunken", "ink_secondary", "sunken"),
    ("muted ink on surface", "ink_muted", "surface"),
    ("muted ink on canvas", "ink_muted", "bg"),
    ("accent ink on surface", "accent_ink", "surface"),
    ("accent ink on hover tint", "accent_ink", "accent_tint"),
    ("white on primary button", "surface", "accent"),
    ("white on primary hover", "surface", "accent_hover"),
]


@pytest.mark.parametrize(("name", "fg", "bg"), TEXT_PAIRS, ids=[pair[0] for pair in TEXT_PAIRS])
def test_text_pairs_meet_wcag_aa(name, fg, bg):
    ratio = contrast(PALETTE[fg], PALETTE[bg])
    assert ratio >= 4.5, f"{name} is {ratio:.2f}:1 (needs 4.5:1)"


def test_uploader_border_meets_non_text_contrast():
    ratio = contrast(PALETTE["control_border"], PALETTE["surface"])
    assert ratio >= 3.0, f"uploader border is {ratio:.2f}:1 (needs 3:1)"


def test_illustration_outline_meets_non_text_contrast():
    ratio = contrast(PALETTE["accent"], PALETTE["art_canvas"])
    assert ratio >= 3.0, f"illustration outline is {ratio:.2f}:1 (needs 3:1)"


# --------------------------------------------------------------------------
# Uploader: the defect this suite exists for
# --------------------------------------------------------------------------
def _rule(selector: str) -> str:
    """Return the declaration block for `selector`, including grouped selectors."""
    for block in re.finditer(r"([^{}]+)\{([^}]*)\}", _CSS_RULES):
        selectors = [part.strip() for part in block.group(1).split(",")]
        if selector in selectors:
            return block.group(2)
    raise AssertionError(f"no CSS rule for {selector}")


def test_uploader_surface_is_white_at_the_theme_level():
    """Streamlit paints the dropzone with `theme.colors.secondaryBg`.

    Setting that to white in config.toml is what removes the coloured surface at the
    source; the CSS below only refines it.
    """
    config_text = (PROJECT_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert 'secondaryBackgroundColor = "#FFFFFF"' in config_text


def test_streamlit_paints_the_dropzone_with_the_token_we_control():
    """Pin the root cause of the reported green-surface defect to the installed bundle.

    In `FileUploader.<hash>.js` the `<section data-testid="stFileUploaderDropzone">`
    styled-component sets `backgroundColor: theme.colors.secondaryBg`, and the
    instructions span uses `colors.fadedText60` — Streamlit's grey. `secondaryBg` is
    fed by `secondaryBackgroundColor` in `.streamlit/config.toml`, so that token, not
    an extra CSS rule, is what colours the dropzone. If a Streamlit upgrade changes
    either fact, this fails and the white-surface guarantee needs revisiting.
    """
    import streamlit

    js_dir = Path(streamlit.__file__).parent / "static" / "static" / "js"
    if not js_dir.is_dir():
        pytest.skip("Streamlit frontend bundle not available in this environment")

    source = None
    for path in js_dir.glob("FileUploader*.js"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "stFileUploaderDropzone" in text:
            source = text
            break
    assert source is not None, "could not locate the file uploader component"

    dropzone = source.split("stFileUploaderDropzone", 1)[0]
    assert "secondaryBg" in dropzone[-2500:], "dropzone background token changed"
    assert "fadedText60" in source, "instruction text no longer uses the faded token"


def test_uploader_surface_is_white_in_css_too():
    body = _rule('[data-testid="stFileUploaderDropzone"]')
    assert "background: var(--jd-surface) !important" in body
    assert "accent" not in body.replace("--jd-surface", "")


def test_every_nested_uploader_text_colour_clears_aa_on_white():
    """Label, instructions and button text are each checked against the surface."""
    checks = {
        '[data-testid="stFileUploaderDropzone"] p': PALETTE["ink"],
        '[data-testid="stFileUploaderDropzoneInstructions"] span': PALETTE["ink_secondary"],
        '[data-testid="stFileUploader"] button': PALETTE["accent_ink"],
    }
    for selector, colour in checks.items():
        body = _rule(selector)
        assert "color" in body, f"{selector} sets no colour"
        assert contrast(colour, PALETTE["surface"]) >= 4.5, f"{selector} falls below AA"


def test_uploader_keeps_teal_off_resting_surfaces():
    """Teal is an interaction colour: hover and focus only, never a resting fill."""
    for block in re.finditer(r"([^{}]+)\{([^}]*)\}", _CSS_RULES):
        if "var(--jd-accent-tint)" not in block.group(2):
            continue
        selectors = block.group(1).strip()
        assert ":hover" in selectors or ":focus" in selectors, (
            f"tinted resting surface reintroduced: {selectors.strip()}"
        )


def test_uploader_defines_hover_focus_and_disabled_states():
    for selector in (
        '[data-testid="stFileUploaderDropzone"]:hover',
        '[data-testid="stFileUploaderDropzone"]:focus-within',
        '[data-testid="stFileUploader"] button:hover',
        '[data-testid="stFileUploader"] button:focus-visible',
        '[data-testid="stFileUploader"] button:disabled',
    ):
        assert _rule(selector)


def test_uploader_browse_button_is_a_teal_outline_on_white():
    body = _rule('[data-testid="stFileUploader"] button')
    assert "var(--jd-accent-ink)" in body
    assert "var(--jd-surface)" in body
    assert "border: 1px solid var(--jd-accent)" in body


# --------------------------------------------------------------------------
# Type scale and cascade
# --------------------------------------------------------------------------
def test_paragraph_classes_outrank_the_global_text_rule():
    """`.stApp p` sets body size, so class rules on <p>/<h1> must be scoped."""
    sources = [PROJECT_ROOT / "app" / "ui" / "components.py"] + sorted(
        (PROJECT_ROOT / "app" / "views").glob("*.py")
    )
    paragraph_classes = set()
    for path in sources:
        text = path.read_text(encoding="utf-8")
        paragraph_classes.update(re.findall(r'<(?:p|h1)\s+class="(jd-[a-z_-]+)"', text))

    assert paragraph_classes, "no paragraph-level design-system classes found"
    for class_name in sorted(paragraph_classes):
        for block in re.finditer(r"([^{}]+)\{([^}]*)\}", _CSS_RULES):
            selectors = [part.strip() for part in block.group(1).split(",")]
            if "font-size" not in block.group(2):
                continue
            if not any(f".{class_name}" in selector for selector in selectors):
                continue
            assert any(
                f".{class_name}" in selector and selector.startswith(".stApp")
                for selector in selectors
            ), f".{class_name} sets font-size but is outranked by `.stApp p`"


# Eight steps: micro label, small, control, body, lead, page title, mobile display,
# display. 2.1rem is the display headline's small-screen size.
TYPE_SCALE = {0.78, 0.84, 0.88, 0.94, 1.05, 1.55, 2.1, 2.75}


def test_type_scale_is_a_fixed_set_of_steps():
    """Exactly eight sizes, no one-off values."""
    sizes = {float(value) for value in re.findall(r"font-size:\s*([\d.]+)rem", _CSS_RULES)}
    assert sizes == TYPE_SCALE, f"off-scale type: {sorted(sizes ^ TYPE_SCALE)}"


def test_stylesheet_has_mobile_breakpoints():
    breakpoints = re.findall(r"@media \(max-width: (\d+)px\)", _CSS)
    assert "900" in breakpoints and "760" in breakpoints


def test_focus_visibility_is_styled():
    assert ":focus-visible" in _CSS
    assert "--jd-focus" in _CSS


# --------------------------------------------------------------------------
# Live selectors only
# --------------------------------------------------------------------------
def test_every_styling_hook_exists_in_the_streamlit_bundle():
    """Dead selectors are invisible at runtime, so assert them against the bundle.

    Streamlit builds some names at runtime (button kinds are
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
        "secondaryBackgroundColor": PALETTE["surface"],
        "textColor": PALETTE["ink"],
    }
    for key, value in expected.items():
        assert f'{key} = "{value}"' in config_text, f"{key} drifted from the palette"


def test_no_surface_token_carries_a_green_cast():
    """The reported defect was a green surface behind grey text.

    Neutral means green is not the dominant channel; warm off-whites (red == green)
    are allowed, green-dominant surfaces are not.
    """
    for token in ("surface", "bg", "sunken", "active"):
        value = PALETTE[token].lstrip("#")
        red, green, blue = (int(value[i : i + 2], 16) for i in (0, 2, 4))
        assert green <= max(red, blue) + 1, f"{token} has a green cast"


def test_stylesheet_only_injects_static_css():
    source = (PROJECT_ROOT / "app" / "ui" / "theme.py").read_text(encoding="utf-8")
    css_block = source.split('_CSS = """', 1)[1].split('"""', 1)[0]
    assert "{" in css_block
    assert "f\"" not in css_block and "f'" not in css_block
