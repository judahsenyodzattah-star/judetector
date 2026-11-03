"""Icon-system guards.

One family, one set of rules: a 24px grid, a single 2px stroke, round caps and
joins, three sizes by context, and colour inherited from the design tokens. These
tests keep that true as icons are added, and keep Material glyphs confined to the
one place Streamlit requires them (native navigation).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.core import config as app_config
from app.ui.icons import (
    ICON_DISPLAY,
    ICON_INLINE,
    ICON_NAMES,
    ICON_STROKE,
    ICON_UI,
    svg,
)

pytestmark = pytest.mark.ui

APP_DIR = Path(app_config.PROJECT_ROOT) / "app"
ALLOWED_SIZES = {ICON_INLINE, ICON_UI, ICON_DISPLAY}


def _app_sources() -> list[Path]:
    return sorted(APP_DIR.rglob("*.py"))


# --------------------------------------------------------------------------
# Glyph contract
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ICON_NAMES)
def test_every_icon_uses_the_shared_grid_and_stroke(name):
    markup = svg(name)
    assert 'viewBox="0 0 24 24"' in markup
    assert f'stroke-width="{ICON_STROKE:g}"' in markup
    assert 'stroke-linecap="round"' in markup
    assert 'stroke-linejoin="round"' in markup
    assert 'fill="none"' in markup


@pytest.mark.parametrize("name", ICON_NAMES)
def test_every_icon_is_decorative_and_colour_inheriting(name):
    markup = svg(name)
    assert 'stroke="currentColor"' in markup
    assert 'aria-hidden="true"' in markup
    assert markup.isascii(), f"{name} contains a non-ASCII glyph"


def test_icon_sizes_are_a_three_step_scale():
    assert (ICON_INLINE, ICON_UI, ICON_DISPLAY) == (16, 20, 24)
    assert ICON_INLINE < ICON_UI < ICON_DISPLAY
    assert svg("scan").count('width="20"') == 1


def test_unknown_icon_falls_back_instead_of_emitting_broken_markup():
    assert svg("does-not-exist") == svg("info")


def test_icon_paths_are_lucide_shapes_only():
    """No emoji, no bitmaps, no foreign markup inside the glyph bodies."""
    for name in ICON_NAMES:
        body = svg(name)
        assert "<path" in body or "<circle" in body or "<rect" in body or "<line" in body
        assert "<img" not in body and "<text" not in body


# --------------------------------------------------------------------------
# Call sites
# --------------------------------------------------------------------------
def test_call_sites_use_the_size_scale_only():
    """A stray `svg("x", 13)` would break the visual rhythm, so it fails here."""
    offenders = []
    pattern = re.compile(r"svg\(\s*[\"'][a-z-]+[\"']\s*,\s*([A-Za-z_][A-Za-z0-9_]*|\d+)\s*\)")
    for path in _app_sources():
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            argument = match.group(1)
            if argument.isdigit() and int(argument) not in ALLOWED_SIZES:
                offenders.append(f"{path.name}: {match.group(0)}")
            elif not argument.isdigit() and argument not in {"ICON_INLINE", "ICON_UI", "ICON_DISPLAY"}:
                offenders.append(f"{path.name}: {match.group(0)}")
    assert not offenders, f"sizes outside the scale: {offenders}"


def test_icon_names_used_by_pages_exist():
    known = set(ICON_NAMES)
    used: set[str] = set()
    pattern = re.compile(r"svg\(\s*[\"']([a-z-]+)[\"']")
    for path in _app_sources():
        used.update(pattern.findall(path.read_text(encoding="utf-8")))
    assert used <= known, f"unknown icons referenced: {sorted(used - known)}"


def test_material_glyphs_are_confined_to_navigation():
    """Page content uses Lucide only; Material appears where Streamlit requires it."""
    allowed = {APP_DIR / "ui" / "nav.py"}
    usage = re.compile(r"""icon\s*=\s*["']:material/""")
    offenders = [
        path.name
        for path in _app_sources()
        if path not in allowed and usage.search(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, f"Material icons used outside navigation: {offenders}"


def test_navigation_icons_are_the_documented_closest_matches():
    from app.ui.nav import DEVELOPER, ENTRIES

    expected = {
        "home": ":material/home:",
        "detect": ":material/image_search:",
        "camera": ":material/photo_camera:",
        "help": ":material/help:",
    }
    assert {entry.key: entry.icon for entry in ENTRIES} == expected
    assert DEVELOPER.icon == ":material/terminal:"
    for entry in (*ENTRIES, DEVELOPER):
        # Material Symbols Rounded is a 24px grid with rounded terminals, which is
        # why it is the closest supported neighbour of the Lucide family.
        assert entry.icon.startswith(":material/")
        assert entry.icon.isascii()


def test_no_emoji_anywhere_in_the_application():
    emoji = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF]")
    offenders = []
    for path in _app_sources():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if emoji.search(line):
                offenders.append(f"{path.name}:{number}")
    assert not offenders, f"emoji found in application source: {offenders}"
