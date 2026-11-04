"""Happy-path contract tests for `POST /v1/detect`."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path

import pytest

from api.runtime import clear_caches
from tests.api_support import install_fake_model, make_client, png_bytes, post_image

pytestmark = pytest.mark.api


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    clear_caches()
    install_fake_model(monkeypatch)
    yield
    clear_caches()


def _client(registry_path: Path):
    return make_client(registry_path(weights=True))


def test_detect_returns_the_measured_result(api_registry):
    response = post_image(_client(api_registry), png_bytes())
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["count"] == 2
    assert len(body["detections"]) == 2
    assert body["count"] == len(body["detections"])

    first = body["detections"][0]
    assert first["label"] == "judah"
    assert first["confidence"] == 0.91
    assert first["box"] == {"x1": 40.0, "y1": 30.0, "x2": 160.0, "y2": 150.0}
    # Normalised boxes are the pixel boxes divided by the analysed dimensions.
    assert first["box_norm"]["x1"] == round(40 / 320, 6)
    assert first["box_norm"]["x2"] == round(160 / 320, 6)
    assert first["box_norm"]["y2"] == round(150 / 240, 6)
    for value in first["box_norm"].values():
        assert 0.0 <= value <= 1.0

    assert body["thresholds"] == {"confidence": 0.25, "iou": 0.45}
    assert body["model"]["id"] == "stub-model"
    assert body["model"]["kind"] == "subject_specific"
    assert body["model"]["labels"] == ["judah"]
    assert body["image"]["width"] == 320
    assert body["image"]["height"] == 240
    assert body["image"]["downscaled"] is False
    assert body["image"]["bytes"] == len(png_bytes())
    assert body["timing"]["inference_ms"] is not None
    assert body["timing"]["total_ms"] is not None
    assert body["timing"]["total_ms"] > 0


def test_detect_returns_the_annotated_png_inline(api_registry):
    body = post_image(_client(api_registry), png_bytes()).json()
    annotated = body["annotated"]
    assert annotated["mime"] == "image/png"
    assert annotated["encoding"] == "base64"
    assert (annotated["width"], annotated["height"]) == (320, 240)
    raw = base64.b64decode(annotated["data"], validate=True)
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")
    assert annotated["bytes"] == len(raw)


def test_annotation_can_be_switched_off(api_registry):
    response = post_image(_client(api_registry), png_bytes(), include_annotated="false")
    body = response.json()
    assert body["annotated"] is None
    assert body["count"] == 2
    assert len(response.content) < 20_000


def test_oversized_annotation_is_omitted_with_a_warning(api_registry):
    client = make_client(api_registry(weights=True), max_annotated_bytes=1000)
    body = post_image(client, png_bytes()).json()
    assert body["annotated"] is None
    assert body["count"] == 2
    assert body["warnings"] and "omitted" in body["warnings"][0].lower()


def test_detect_reports_timings_and_server_timing(api_registry):
    response = post_image(_client(api_registry), png_bytes())
    assert "Server-Timing" in response.headers
    assert "inference;dur=" in response.headers["Server-Timing"]
    assert "total;dur=" in response.headers["Server-Timing"]


def test_detect_sets_no_store_and_request_id(api_registry):
    response = post_image(_client(api_registry), png_bytes())
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"] == response.json()["request_id"]
    assert response.headers["ratelimit-scope"] == "instance"


def test_large_images_are_downscaled_and_reported(api_registry):
    client = _client(api_registry)
    body = post_image(client, png_bytes(5000, 400)).json()
    assert body["image"]["downscaled"] is True
    assert body["image"]["source_width"] == 5000
    assert body["image"]["width"] == 4000
    assert body["image"]["height"] == 320
    for detection in body["detections"]:
        assert detection["box"]["x2"] <= body["image"]["width"]
        assert 0.0 <= detection["box_norm"]["x2"] <= 1.0


def test_zero_detections_still_return_a_result(api_registry, monkeypatch):
    clear_caches()
    install_fake_model(monkeypatch, rows=[])
    body = post_image(_client(api_registry), png_bytes()).json()
    assert body["count"] == 0
    assert body["detections"] == []
    assert body["timing"]["inference_ms"] is not None


def test_detect_response_carries_no_paths_or_dependency_names(api_registry, tmp_path):
    response = post_image(_client(api_registry), png_bytes())
    text = response.text.lower()
    for leaked in ("best.pt", "models.json", str(tmp_path).lower(), "torch", "ultralytics"):
        assert leaked not in text


def test_base64_payload_is_not_silently_corrupt(api_registry):
    body = post_image(_client(api_registry), png_bytes()).json()
    try:
        base64.b64decode(body["annotated"]["data"], validate=True)
    except binascii.Error:  # pragma: no cover - failure path
        pytest.fail("annotated data is not valid base64")
