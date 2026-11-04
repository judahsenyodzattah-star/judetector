"""Parity: the API must report exactly what the Python pipeline reports.

These tests run the same image through `POST /v1/detect` and through
`app.components.pipeline.analyse_image` directly, with independent detectors, and
compare the numbers. If the API ever starts rounding, reordering or inventing a
value, this fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from api.runtime import clear_caches
from api.settings import Settings
from app.components.pipeline import analyse_image
from app.core.detector import UltralyticsDetector
from app.core.image_io import downscale, load_image
from app.core.registry import load_registry
from tests.api_support import DETECTION_ROWS, install_fake_model, make_client, png_bytes, post_image
from tests.conftest import FakeModel

pytestmark = pytest.mark.api


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    clear_caches()
    install_fake_model(monkeypatch)
    yield
    clear_caches()


def _pipeline_result(
    registry_path: Path,
    data: bytes,
    *,
    confidence: float = 0.25,
    iou: float = 0.45,
    rows=None,
    max_dimension: int | None = None,
):
    """Run the prototype's pipeline directly, independently of the API."""
    spec = load_registry(registry_path).default()
    image = load_image(data)
    limit = Settings().max_image_dimension if max_dimension is None else max_dimension
    image, _ = downscale(image, limit)
    detector = UltralyticsDetector(
        spec.id,
        spec.weights_path,
        declared_labels=spec.declared_labels,
        model_loader=lambda _path: FakeModel(DETECTION_ROWS if rows is None else rows),
    )
    outcome = analyse_image(image, spec, detector, confidence=confidence, iou=iou)
    assert outcome.ok, outcome.error_message
    return outcome.result


def test_detections_match_the_pipeline_exactly(api_registry):
    registry_path = api_registry(weights=True)
    data = png_bytes()

    api_body = post_image(make_client(registry_path), data).json()
    expected = _pipeline_result(registry_path, data)

    assert api_body["count"] == expected.count
    assert len(api_body["detections"]) == len(expected.records())

    for reported, record in zip(api_body["detections"], expected.records(), strict=True):
        assert reported["label"] == record["label"]
        assert reported["confidence"] == record["confidence"]
        assert reported["box"]["x1"] == record["x1"]
        assert reported["box"]["y1"] == record["y1"]
        assert round(reported["box"]["x2"] - reported["box"]["x1"], 1) == record["width"]
        assert round(reported["box"]["y2"] - reported["box"]["y1"], 1) == record["height"]
        # The detector reports no init-time confidence; the pipeline is the source.
        assert expected.mean_confidence is not None
        assert (
            pytest.approx(reported["confidence"], abs=1e-9)
            == record["confidence"]
        )


def test_thresholds_and_model_information_match(api_registry):
    registry_path = api_registry(weights=True)
    body = post_image(make_client(registry_path), png_bytes(), confidence=0.4, iou=0.2).json()
    expected = _pipeline_result(registry_path, png_bytes(), confidence=0.4, iou=0.2)

    assert body["thresholds"] == {
        "confidence": expected.confidence_threshold,
        "iou": expected.iou_threshold,
    }
    assert body["model"]["id"] == expected.model_id
    assert (body["image"]["width"], body["image"]["height"]) == (
        expected.image_width,
        expected.image_height,
    )


def test_zero_detections_match_the_pipeline(api_registry, monkeypatch):
    clear_caches()
    install_fake_model(monkeypatch, rows=[])
    registry_path = api_registry(weights=True)
    data = png_bytes()

    body = post_image(make_client(registry_path), data).json()
    expected = _pipeline_result(registry_path, data, rows=[])

    assert body["count"] == 0 == expected.count
    assert body["detections"] == []
    assert body["image"]["width"] == expected.image_width


def test_normalised_boxes_are_the_pixel_boxes_over_the_analysed_dimensions(api_registry):
    body = post_image(make_client(api_registry(weights=True)), png_bytes(5000, 400)).json()
    width, height = body["image"]["width"], body["image"]["height"]
    assert (width, height) == (4000, 320)

    for detection in body["detections"]:
        box, norm = detection["box"], detection["box_norm"]
        assert norm["x1"] == pytest.approx(box["x1"] / width, abs=1e-6)
        assert norm["y1"] == pytest.approx(box["y1"] / height, abs=1e-6)
        assert norm["x2"] == pytest.approx(box["x2"] / width, abs=1e-6)
        assert norm["y2"] == pytest.approx(box["y2"] / height, abs=1e-6)


def test_parity_holds_for_a_downscaled_image(api_registry):
    registry_path = api_registry(weights=True)
    data = png_bytes(5000, 400)

    body = post_image(make_client(registry_path), data).json()
    expected = _pipeline_result(registry_path, data)

    assert body["image"]["downscaled"] is True
    assert body["count"] == expected.count
    for reported, record in zip(body["detections"], expected.records(), strict=True):
        assert reported["box"]["x1"] == record["x1"]
        assert reported["confidence"] == record["confidence"]
