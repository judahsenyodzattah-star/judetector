"""Bounding-box rendering with Pillow.

Pillow (RGB) is used rather than OpenCV on purpose: it removes the classic
BGR/RGB channel-swap defect in Streamlit apps and drops a heavy dependency.
Coordinates are clamped to the image so a box can never crash the draw call.
"""

from __future__ import annotations

from collections.abc import Sequence

from PIL import Image, ImageDraw, ImageFont

from app.core.detector import Detection
from app.core.image_io import ensure_rgb

__all__ = ["BOX_COLOURS", "draw_detections", "side_by_side", "confidence_colour"]

# Colourblind-aware, high-contrast palette; cycled by detection index.
BOX_COLOURS: tuple[str, ...] = (
    "#00A86B",  # green
    "#1F6FEB",  # blue
    "#D97706",  # amber
    "#C2185B",  # magenta
    "#6D28D9",  # violet
    "#0F766E",  # teal
)


def confidence_colour(confidence: float) -> str:
    """Green >= 0.66, amber >= 0.4, red below that."""
    if confidence >= 0.66:
        return "#00A86B"
    if confidence >= 0.40:
        return "#D97706"
    return "#DC2626"


def _line_width(image: Image.Image) -> int:
    return max(2, int(round(min(image.width, image.height) / 300)))


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 9.2 has no size argument
        return ImageFont.load_default()


def draw_detections(
    image: Image.Image,
    detections: Sequence[Detection],
    *,
    line_width: int | None = None,
    show_labels: bool = True,
    colour_by_confidence: bool = False,
) -> Image.Image:
    """Return a new RGB image with boxes drawn. The input is never mutated."""
    canvas = ensure_rgb(image).copy()
    if not detections:
        return canvas

    draw = ImageDraw.Draw(canvas)
    width = line_width or _line_width(canvas)
    font_size = max(12, int(round(min(canvas.width, canvas.height) / 32)))
    font = _font(font_size)

    for index, detection in enumerate(detections):
        x1, y1, x2, y2 = detection.box_xyxy
        left, right = sorted((float(x1), float(x2)))
        top, bottom = sorted((float(y1), float(y2)))
        left = max(0.0, min(left, canvas.width - 1))
        right = max(0.0, min(right, canvas.width - 1))
        top = max(0.0, min(top, canvas.height - 1))
        bottom = max(0.0, min(bottom, canvas.height - 1))
        box = (left, top, right, bottom)

        colour = (
            confidence_colour(detection.confidence)
            if colour_by_confidence
            else BOX_COLOURS[index % len(BOX_COLOURS)]
        )
        draw.rectangle(box, outline=colour, width=width)

        if not show_labels:
            continue

        caption = f"{detection.label} {detection.confidence:.2f}".strip()
        text_top = max(0.0, top - font_size - 6)
        try:
            text_box = draw.textbbox((0, 0), caption, font=font)
            text_width = text_box[2] - text_box[0]
            text_height = text_box[3] - text_box[1]
        except Exception:  # noqa: BLE001 - older Pillow fallback
            text_width, text_height = 8 * len(caption), font_size

        padding = 3
        plate = (
            left,
            text_top,
            min(left + text_width + 2 * padding, canvas.width - 1),
            min(text_top + text_height + 2 * padding, canvas.height - 1),
        )
        if plate[2] > plate[0] and plate[3] > plate[1]:
            draw.rectangle(plate, fill=colour)
        draw.text(
            (left + padding, text_top + padding),
            caption,
            fill="#FFFFFF",
            font=font,
        )

    return canvas


def side_by_side(
    original: Image.Image,
    processed: Image.Image,
    *,
    background: str = "#F4F7F9",
    gap: int = 16,
) -> Image.Image:
    """Compose original and processed images into one comparison figure."""
    left = ensure_rgb(original)
    right = ensure_rgb(processed)
    if right.height != left.height:
        target_width = max(1, int(round(right.width * left.height / right.height)))
        right = right.resize((target_width, left.height), Image.Resampling.LANCZOS)

    gap = max(0, gap)
    canvas = Image.new(
        "RGB",
        (left.width + gap + right.width, max(left.height, right.height)),
        background,
    )
    canvas.paste(left, (0, 0))
    canvas.paste(right, (left.width + gap, 0))
    return canvas
