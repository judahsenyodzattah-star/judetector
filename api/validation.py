"""Upload and image validation.

Everything here runs before the model does, so a malformed, enormous or
unsupported upload costs memory and nothing else. The rules mirror the
prototype's guards (`app/core/image_io.py`) and add the two that only a service
needs: a hard request-size cap and a decoded pixel budget.

Deliberate choices:

* The **detected** format is authoritative, never the declared content type.
  A PNG named `.jpg` is a PNG; a script named `.png` is rejected.
* Pixel count is checked from the header *before* the pixels are decoded, so a
  decompression bomb cannot allocate first and fail later.
* `load_image` remains the single decoder, so the API and the Streamlit app can
  never disagree about what a valid image is.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from api.errors import ProblemError
from api.settings import Settings
from app.core.errors import InvalidImageError
from app.core.image_io import SUPPORTED_PIL_FORMATS, downscale, load_image

__all__ = ["READ_CHUNK_BYTES", "ValidatedImage", "read_upload", "validate_image"]

READ_CHUNK_BYTES = 64 * 1024
_SUPPORTED_LABEL = "JPG, PNG, WEBP or BMP"


@dataclass(frozen=True)
class ValidatedImage:
    """A decoded, guarded image plus the facts the response must report."""

    data: bytes
    image: Image.Image
    source_width: int
    source_height: int
    downscaled: bool


async def read_upload(upload: UploadFile, settings: Settings) -> bytes:
    """Read an upload, refusing to buffer more than the configured cap."""
    limit = settings.max_upload_mb * 1024 * 1024
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise ProblemError(
                status=413,
                type_="payload_too_large",
                title="Upload is too large",
                detail=f"Images must be {settings.max_upload_mb} MB or smaller.",
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        raise ProblemError(
            status=422,
            type_="invalid_image",
            title="No image was received",
            detail="The uploaded file was empty.",
        )
    return data


def validate_image(data: bytes, settings: Settings) -> ValidatedImage:
    """Probe, guard, decode and downscale an image, or raise a problem."""
    try:
        with Image.open(io.BytesIO(data)) as probe:
            detected = (probe.format or "").upper()
            width, height = probe.size
    except UnidentifiedImageError as exc:
        raise ProblemError(
            status=422,
            type_="invalid_image",
            title="Image could not be read",
            detail="That file could not be decoded as an image. It may be corrupt.",
        ) from exc
    except Image.DecompressionBombError as exc:  # pragma: no cover - PIL version dependent
        raise ProblemError(
            status=413,
            type_="payload_too_large",
            title="Image dimensions are too large",
            detail=f"Images must be at most {settings.max_pixels:,} pixels.",
        ) from exc
    except OSError as exc:
        raise ProblemError(
            status=422,
            type_="invalid_image",
            title="Image could not be read",
            detail="That file could not be decoded as an image. It may be corrupt.",
        ) from exc

    if detected not in SUPPORTED_PIL_FORMATS:
        raise ProblemError(
            status=415,
            type_="unsupported_media_type",
            title="Unsupported image format",
            detail=f"Detected format {detected or 'unknown'}. Supported: {_SUPPORTED_LABEL}.",
        )

    if width * height > settings.max_pixels:
        raise ProblemError(
            status=413,
            type_="payload_too_large",
            title="Image dimensions are too large",
            detail=(
                f"This image is {width * height:,} pixels; the limit is "
                f"{settings.max_pixels:,}."
            ),
        )

    try:
        image = load_image(data)
    except InvalidImageError as exc:
        raise ProblemError(
            status=422,
            type_="invalid_image",
            title="Image could not be read",
            detail="That file could not be decoded as an image. It may be corrupt.",
        ) from exc

    if image.width <= 0 or image.height <= 0:  # pragma: no cover - defensive
        raise ProblemError(
            status=422,
            type_="invalid_image",
            title="Image could not be read",
            detail="The image has no usable dimensions.",
        )

    analysed, resized = downscale(image, settings.max_image_dimension)
    return ValidatedImage(
        data=data,
        image=analysed,
        source_width=image.width,
        source_height=image.height,
        downscaled=resized,
    )


def describe_supported() -> str:
    """Human label for the accepted formats (used in documentation and errors)."""
    return _SUPPORTED_LABEL


def looks_like_path(text: str) -> bool:  # pragma: no cover - guard used in tests only
    """Cheap check used by tests: does a string mention a filesystem path?"""
    return str(Path("/")) in text and "/" in text
