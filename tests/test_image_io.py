"""Image decoding, guarding and encoding."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.core.errors import InvalidImageError
from app.core.image_io import (
    describe_image,
    downscale,
    ensure_rgb,
    load_image,
    to_png_bytes,
)


def test_load_png_bytes(png_bytes):
    image = load_image(png_bytes)
    assert image.mode == "RGB"
    assert image.size == (320, 240)


def test_load_from_path(tmp_path, png_bytes):
    path = tmp_path / "img.png"
    path.write_bytes(png_bytes)
    assert load_image(path).size == (320, 240)


def test_missing_path_raises(tmp_path):
    with pytest.raises(InvalidImageError):
        load_image(tmp_path / "nope.png")


def test_empty_bytes_raises():
    with pytest.raises(InvalidImageError):
        load_image(b"")


def test_non_image_bytes_raises():
    with pytest.raises(InvalidImageError):
        load_image(b"this is definitely not an image")


def test_rgba_is_composited_to_rgb(rgba_image):
    converted = ensure_rgb(rgba_image)
    assert converted.mode == "RGB"
    assert converted.size == rgba_image.size


def test_grayscale_is_converted():
    grey = Image.new("L", (10, 10), 128)
    assert ensure_rgb(grey).mode == "RGB"


def test_downscale_leaves_small_images_alone(rgb_image):
    result, resized = downscale(rgb_image, max_dimension=1000)
    assert resized is False
    assert result is rgb_image


def test_downscale_respects_limit_and_aspect_ratio():
    large = Image.new("RGB", (8000, 4000), "white")
    result, resized = downscale(large, max_dimension=1000)
    assert resized is True
    assert max(result.size) == 1000
    assert result.size == (1000, 500)
    assert result.size[0] / result.size[1] == pytest.approx(2.0, rel=1e-3)


def test_downscale_handles_tall_images():
    tall = Image.new("RGB", (500, 5000), "white")
    result, resized = downscale(tall, max_dimension=1000)
    assert resized is True
    assert max(result.size) == 1000


def test_png_round_trip(rgb_image):
    data = to_png_bytes(rgb_image)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert load_image(data).size == rgb_image.size


def test_describe_image(rgb_image):
    assert "320" in describe_image(rgb_image)
    assert "RGB" in describe_image(rgb_image)


def test_max_dimension_config_is_used_by_default():
    from app.core import config

    huge = Image.new("RGB", (config.MAX_IMAGE_DIMENSION + 500, 100), "white")
    result, resized = downscale(huge)
    assert resized is True
    assert max(result.size) == config.MAX_IMAGE_DIMENSION


def test_path_object_support_with_unicode_name(tmp_path, png_bytes):
    path = Path(tmp_path) / "ñandú image.png"
    path.write_bytes(png_bytes)
    assert load_image(path).size == (320, 240)
