"""Inline SVG icon set — Lucide geometry, MIT licensed.

One family, one set of rules, applied everywhere an icon is drawn in page content:

* **24px grid** — every glyph is drawn on a 24×24 canvas and scaled by size.
* **2px stroke** — no glyph overrides the stroke weight.
* **Round caps and joins** — matching Lucide's default line endings.
* **Three sizes by context** — :data:`ICON_INLINE` (beside text), :data:`ICON_UI`
  (empty states, steps, notices) and :data:`ICON_DISPLAY` (hero/feature marks).
* **Colour inherited** — `stroke="currentColor"`, so icons take their colour from
  the design tokens around them and never introduce a second palette.

Icons are emoji-free and inline, so they need no network request and cannot render
as tofu. Streamlit's native navigation is the one place an inline SVG cannot go:
`st.Page(icon=...)` accepts only emoji or ``:material/name:``, and replacing the
native navigation with hand-rolled links would cost URL routing, keyboard support
and the mobile drawer. The navigation therefore uses the closest Material Symbols
Rounded glyph, while everything inside the pages uses this Lucide set.
"""

from __future__ import annotations

from typing import Final

__all__ = ["ICON_DISPLAY", "ICON_INLINE", "ICON_NAMES", "ICON_STROKE", "ICON_UI", "svg"]

#: Icon sizes, by context. Keeping this list short is what makes a mixed interface
#: look deliberate rather than assembled.
ICON_INLINE: Final[int] = 16
ICON_UI: Final[int] = 20
ICON_DISPLAY: Final[int] = 24

#: Single stroke weight for the whole family.
ICON_STROKE: Final[float] = 2.0

# 24x24 stroke glyphs, one string of child markup per icon.
_PATHS: Final[dict[str, str]] = {
    "scan": (
        '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>'
        '<path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>'
        '<line x1="7" y1="12" x2="17" y2="12"/>'
    ),
    "image": (
        '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>'
        '<circle cx="9" cy="9" r="2"/>'
        '<path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>'
    ),
    "camera": (
        '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>'
        '<circle cx="12" cy="13" r="3"/>'
    ),
    "upload": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'
    ),
    "download": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'
    ),
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "alert-circle": (
        '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>'
        '<line x1="12" y1="16" x2="12.01" y2="16"/>'
    ),
    "alert-triangle": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    "help": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>'
    ),
    "shield": (
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 '
        '1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
    ),
    "lock": (
        '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    ),
    "cpu": (
        '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/>'
        '<path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/>'
        '<path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>'
    ),
    "chart": (
        '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>'
    ),
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
}

ICON_NAMES: Final[tuple[str, ...]] = tuple(_PATHS)


def svg(name: str, size: int = ICON_UI) -> str:
    """Return an inline SVG string for `name`.

    Unknown names fall back to `info` rather than emitting broken markup. The SVG
    is decorative (`aria-hidden`); the adjacent text always carries the meaning.
    """
    body = _PATHS.get(name, _PATHS["info"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{ICON_STROKE:g}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" focusable="false">{body}</svg>'
    )
