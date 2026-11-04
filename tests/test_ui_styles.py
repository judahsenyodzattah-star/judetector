"""Guards for the shared stylesheet — the application design language.

These are the failures that are invisible by reading CSS: dead Streamlit selectors,
contrast regressions, off-scale type, a palette that drifts from the theme config,
the marking colour leaking onto surfaces, and the uploader's rendered treatment.

Colour maths follows the WCAG 2.1 relative-luminance definition.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.core import config as app_config
from app.core.rendering import BOX_COLOURS
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
    ("rail text on the rail", "rail_text", "rail"),
    ("rail secondary text on the rail", "rail_muted", "rail"),
    ("ink on mount", "ink", "mount"),
    ("ink on sheet", "ink", "sheet"),
    ("ink on artwork", "ink", "art_canvas"),
    ("secondary ink on mount", "ink_secondary", "mount"),
    ("secondary ink on sheet", "ink_secondary", "sheet"),
    ("secondary ink on artwork", "ink_secondary", "art_canvas"),
    ("marking colour on mount", "mark", "mount"),
    ("marking colour on sheet", "mark", "sheet"),
    ("white on the primary action", "mount", "mark"),
    ("white on the primary action hover", "mount", "mark_hover"),
]


@pytest.mark.parametrize(("name", "fg", "bg"), TEXT_PAIRS, ids=[pair[0] for pair in TEXT_PAIRS])
def test_text_pairs_meet_wcag_aa(name, fg, bg):
    ratio = contrast(PALETTE[fg], PALETTE[bg])
    assert ratio >= 4.5, f"{name} is {ratio:.2f}:1 (needs 4.5:1)"


def test_the_rail_reads_as_the_only_dark_surface():
    """The frame is dark, the workspace is light: that contrast is the hierarchy."""
    for surface in ("sheet", "mount", "art_canvas"):
        assert _luminance(PALETTE[surface]) > 0.8, f"{surface} is not a light surface"
    assert _luminance(PALETTE["rail"]) < 0.05, "the rail is not dark"
    assert contrast(PALETTE["rail_text"], PALETTE["rail"]) >= 7.0


def test_the_active_destination_is_marked_not_filled():
    """Ochre appears as a 2px rule on the active rail item, never as its background."""
    body = _rule('[data-testid="stSidebarNavLink"][aria-current="page"]')
    assert "border-left-color: var(--jd-mark)" in body
    background = re.search(r"background:\s*([^;]+);", body)
    assert background is not None, "the active item has no background declaration"
    assert "var(--jd-mark)" not in background.group(1)


def test_interactive_boundaries_clear_non_text_contrast():
    """The uploader frame and every widget border use ink-2, not the hairline rule."""
    assert contrast(PALETTE["ink_secondary"], PALETTE["mount"]) >= 3.0
    assert contrast(PALETTE["ink_secondary"], PALETTE["sheet"]) >= 3.0


def test_the_hairline_rule_is_decorative_only():
    """`rule` is a separator and registration mark; it must never bound a control."""
    assert contrast(PALETTE["rule"], PALETTE["mount"]) < 3.0
    assert "var(--jd-rule)" not in _rule('[data-testid="stFileUploaderDropzone"]')


def test_artwork_outline_reads_against_its_plate():
    assert contrast(PALETTE["mark"], PALETTE["art_canvas"]) >= 3.0


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

    Setting that to white in config.toml removes the coloured surface at the source;
    the CSS below only refines it.
    """
    config_text = (PROJECT_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert 'secondaryBackgroundColor = "#FFFFFF"' in config_text


def test_streamlit_paints_the_dropzone_with_the_token_we_control():
    """Pin the root cause of the reported green-surface defect to the installed bundle.

    In `FileUploader.<hash>.js` the `<section data-testid="stFileUploaderDropzone">`
    styled-component sets `backgroundColor: theme.colors.secondaryBg`, and the
    instructions span uses `colors.fadedText60`. `secondaryBg` is fed by
    `secondaryBackgroundColor`, so that token — not an extra CSS rule — is what
    colours the dropzone. If a Streamlit upgrade changes either fact, this fails.
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
    assert "background: var(--jd-mount) !important" in body
    assert "--jd-mark" not in body


def test_every_nested_uploader_text_colour_clears_aa_on_white():
    """Label, instructions and button text are each checked against the surface."""
    checks = {
        '[data-testid="stFileUploaderDropzone"] p': (PALETTE["ink"], PALETTE["mount"]),
        '[data-testid="stFileUploaderDropzoneInstructions"] span': (
            PALETTE["ink"],
            PALETTE["mount"],
        ),
        '[data-testid="stFileUploaderDropzoneInstructions"] small': (
            PALETTE["ink_secondary"],
            PALETTE["mount"],
        ),
        '[data-testid="stFileUploader"] button': ("#FFFFFF", PALETTE["mark"]),
    }
    for selector, (colour, background) in checks.items():
        body = _rule(selector)
        assert "color" in body, f"{selector} sets no colour"
        assert contrast(colour, background) >= 4.5, f"{selector} falls below AA"


def test_uploader_defines_hover_focus_and_disabled_states():
    for selector in (
        '[data-testid="stFileUploaderDropzone"]:hover',
        '[data-testid="stFileUploaderDropzone"]:focus-within',
        '[data-testid="stFileUploader"] button:hover',
        '[data-testid="stFileUploader"] button:focus-visible',
        '[data-testid="stFileUploader"] button:disabled',
    ):
        assert _rule(selector)


def test_uploader_browse_button_is_the_primary_action():
    """The uploader's own control is the page's filled primary action.

    Ochre is allowed to fill it because it is the single primary action on Home; the
    dropzone surface itself stays white.
    """
    body = _rule('[data-testid="stFileUploader"] button')
    assert "background: var(--jd-mark) !important" in body
    assert "color: #FFFFFF !important" in body
    assert "border: 1px solid var(--jd-mark) !important" in body
    hover = _rule('[data-testid="stFileUploader"] button:hover')
    assert "var(--jd-mark-hover)" in hover
    assert contrast("#FFFFFF", PALETTE["mark"]) >= 4.5


# --------------------------------------------------------------------------
# The marking colour is a marking colour
# --------------------------------------------------------------------------
MARK_SURFACE_ALLOWLIST = {
    # The two primary actions in the product: Analyse image / Open this result, and the
    # uploader's own browse control, which is the primary action on Home.
    '[data-testid="stBaseButton-primary"]',
    '[data-testid="stBaseButton-primary"]:hover',
    '[data-testid="stFileUploader"] button',
    '[data-testid="stFileUploader"] button:hover',
}


def test_the_marking_colour_never_fills_a_surface():
    """Ochre belongs on actions, active states, focus rings and annotations only."""
    offenders = []
    for block in re.finditer(r"([^{}]+)\{([^}]*)\}", _CSS_RULES):
        selectors = [part.strip() for part in block.group(1).split(",")]
        body = block.group(2)
        if not re.search(r"background(?:-color)?:\s*var\(--jd-mark", body):
            continue
        if not all(selector in MARK_SURFACE_ALLOWLIST for selector in selectors):
            offenders.append(", ".join(selectors))
    assert not offenders, f"ochre used as a surface: {offenders}"


def test_neutral_pieces_contain_no_marking_colour():
    for selector in (
        ".jd-card__head",
        ".jd-dets",
        ".jd-det",
        ".jd-readout",
        ".jd-note",
        ".jd-empty",
        ".jd-specimen__art",
    ):
        assert "--jd-mark" not in _rule(selector), f"{selector} should stay neutral"


def test_the_interface_accent_is_not_one_of_the_models_box_colours():
    """A reader must not confuse the page accent with a drawn detection."""
    mark = PALETTE["mark"].lstrip("#")
    rgb = tuple(int(mark[i : i + 2], 16) for i in (0, 2, 4))
    for colour in BOX_COLOURS:
        other = tuple(int(colour.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        distance = sum((a - b) ** 2 for a, b in zip(rgb, other)) ** 0.5
        assert distance >= 60, f"{PALETTE['mark']} is too close to box colour {colour}"


# --------------------------------------------------------------------------
# Type, spacing, radii
# --------------------------------------------------------------------------
# Seven text steps: micro label, caption, small, body/card title, section,
# metric value, page title.
TYPE_SCALE = {0.75, 0.8125, 0.875, 0.9375, 1.0625, 1.25, 1.5}


def test_type_scale_is_a_fixed_set_of_steps():
    sizes = {float(value) for value in re.findall(r"font-size:\s*([\d.]+)rem", _CSS_RULES)}
    assert sizes == TYPE_SCALE, f"off-scale type: {sorted(sizes ^ TYPE_SCALE)}"


def test_spacing_scale_is_the_declared_one():
    expected = ["0.25", "0.5", "0.75", "1", "1.5", "2", "3"]
    found = [
        re.search(rf"--jd-{index}:\s*([\d.]+)rem;", _CSS).group(1)
        for index in range(1, 8)
    ]
    assert found == expected


def test_corners_use_the_two_step_radius_scale():
    """8px for cards, 6px for controls; circles and code are the only exceptions."""
    assert "--jd-radius: 8px" in _CSS
    assert "--jd-radius-sm: 6px" in _CSS
    radii = set(re.findall(r"border-radius:\s*([^;]+);", _CSS_RULES))
    allowed = {
        "var(--jd-radius)",
        "var(--jd-radius) !important",
        "var(--jd-radius-sm)",
        "var(--jd-radius-sm) !important",
        "0",
        "50%",
    }
    assert radii <= allowed, f"stray radii: {radii - allowed}"


def test_paragraph_classes_outrank_the_global_text_rule():
    """`.stApp p` sets body size, so class rules on <p>/<h1> must be scoped above it."""
    sources = [PROJECT_ROOT / "app" / "ui" / "components.py"] + sorted(
        (PROJECT_ROOT / "app" / "views").glob("*.py")
    )
    paragraph_classes = set()
    for path in sources:
        text = path.read_text(encoding="utf-8")
        paragraph_classes.update(re.findall(r'<(?:p|h1|h2)\s+class="(jd-[a-z_-]+)"', text))

    assert paragraph_classes, "no paragraph-level design-system classes found"
    for class_name in sorted(paragraph_classes):
        # Match the class itself, not a longer class that starts with it
        # (`.jd-flow` must not match `.jd-flow__n`).
        pattern = re.compile(rf"\.{re.escape(class_name)}(?![-\w])")
        for block in re.finditer(r"([^{}]+)\{([^}]*)\}", _CSS_RULES):
            selectors = [part.strip() for part in block.group(1).split(",")]
            if "font-size" not in block.group(2):
                continue
            matching = [selector for selector in selectors if pattern.search(selector)]
            if not matching:
                continue
            assert any(
                pattern.search(selector) and selector.startswith(".stApp")
                for selector in matching
            ), f".{class_name} sets font-size but is outranked by `.stApp p`"


# --------------------------------------------------------------------------
# No fashionable effects
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "token", ["gradient", "backdrop-filter", "filter:", "text-shadow", "animation", "@keyframes"]
)
def test_no_decorative_effects(token):
    assert token not in _CSS


def test_shadows_are_focus_rings_only():
    shadows = set(re.findall(r"box-shadow:\s*([^;]+);", _CSS_RULES))
    assert shadows <= {"var(--jd-focus)", "var(--jd-focus) !important", "none"}, (
        f"decorative shadow: {shadows}"
    )


def test_motion_is_limited_to_colour():
    assert not re.search(r"(?<!text-)transform", _CSS)
    assert "transition" not in _CSS


# --------------------------------------------------------------------------
# Live selectors only
# --------------------------------------------------------------------------
def test_every_styling_hook_exists_in_the_streamlit_bundle():
    """Dead selectors are invisible at runtime, so assert them against the bundle."""
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
        "primaryColor": PALETTE["mark"],
        "backgroundColor": PALETTE["sheet"],
        "secondaryBackgroundColor": PALETTE["mount"],
        "textColor": PALETTE["ink"],
        "borderColor": PALETTE["rule"],
        "baseRadius": "8px",
        "buttonRadius": "6px",
        "baseFontSize": 14,
    }
    for key, value in expected.items():
        rendered = f'"{value}"' if isinstance(value, str) else str(value)
        assert f"{key} = {rendered}" in config_text, f"{key} drifted from the palette"

    # The rail is themed natively, not painted over Streamlit's internals.
    sidebar_block = config_text.split("[theme.sidebar]", 1)[1]
    assert f'backgroundColor = "{PALETTE["rail"]}"' in sidebar_block
    assert f'textColor = "{PALETTE["rail_text"]}"' in sidebar_block


def test_no_surface_token_carries_a_colour_cast():
    """The reported defect was a green surface behind grey text; surfaces stay neutral."""
    for token in ("sheet", "mount", "art_canvas", "art_shape", "rail", "rail_text", "rail_muted"):
        value = PALETTE[token].lstrip("#")
        red, green, blue = (int(value[i : i + 2], 16) for i in (0, 2, 4))
        assert max(red, green, blue) - min(red, green, blue) <= 24, f"{token} is tinted"


def test_stylesheet_only_injects_static_css():
    source = (PROJECT_ROOT / "app" / "ui" / "theme.py").read_text(encoding="utf-8")
    css_block = source.split('_CSS = """', 1)[1].split('"""', 1)[0]
    assert "{" in css_block
    assert "f\"" not in css_block and "f'" not in css_block
