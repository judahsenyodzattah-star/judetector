"""Image decoding, guarding and encoding.

Kept separate from rendering and detection so each piece stays testable and the
guards (size cap, format check) apply once, consistently, for uploads and
camera snapshots alike.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

from PIL import Image, UnidentifiedImageError

from app.core import config
from app.core.errors import InvalidImageError

__all__ = [
    "SUPPORTED_PIL_FORMATS",
    "load_image",
    "ensure_rgb",
    "downscale",
    "to_png_bytes",
    "describe_image",
]

SUPPORTED_PIL_FORMATS: tuple[str, ...] = ("JPEG", "PNG", "WEBP", "BMP")


def load_image(data: bytes | BinaryIO | Path) -> Image.Image:
    """Decode an upload into an RGB PIL image, or raise InvalidImageError."""
    try:
        if isinstance(data, Path):
            if not data.is_file():
                raise InvalidImageError(f"File not found: {data}")
            stream: object = data
        elif isinstance(data, (bytes, bytearray)):
            if not data:
                raise InvalidImageError("The uploaded file is empty.")
            stream = io.BytesIO(bytes(data))
        else:
            stream = data
            if hasattr(stream, "seek"):
                stream.seek(0)  # type: ignore[union-attr]

        with Image.open(stream) as opened:  # type: ignore[arg-type]
            opened.load()
            if opened.format and opened.format.upper() not in SUPPORTED_PIL_FORMATS:
                raise InvalidImageError(
                    f"Unsupported image format '{opened.format}'. "
                    f"Supported: {', '.join(SUPPORTED_PIL_FORMATS)}."
                )
            image = opened.copy()
    except InvalidImageError:
        raise
    except UnidentifiedImageError as exc:
        raise InvalidImageError(
            "That file could not be read as an image. It may be corrupt or not an image file."
        ) from exc
    except OSError as exc:
        raise InvalidImageError(f"Could not read the image: {exc}") from exc

    return ensure_rgb(image)


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Normalise to RGB (handles L, RGBA, CMYK, P, LA) without altering pixels' meaning."""
    if image.mode == "RGB":
        return image
    if image.mode in {"RGBA", "LA", "P"}:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return image.convert("RGB")


def downscale(
    image: Image.Image, max_dimension: int | None = None
) -> tuple[Image.Image, bool]:
    """Downscale so the longest side is <= max_dimension. Returns (image, resized)."""
    limit = max_dimension or config.MAX_IMAGE_DIMENSION
    if limit <= 0:
        return image, False
    longest = max(image.width, image.height)
    if longest <= limit:
        return image, False
    scale = limit / float(longest)
    new_size = (max(1, int(round(image.width * scale))), max(1, int(round(image.height * scale))))
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    return resized, True


def to_png_bytes(image: Image.Image) -> bytes:
    """Encode an RGB image as PNG for download."""
    buffer = io.BytesIO()
    ensure_rgb(image).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def describe_image(image: Image.Image) -> str:
    return f"{image.width} × {image.height} px, {image.mode}"
