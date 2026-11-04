"""Upload guards, error taxonomy and the honest unavailable path."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from api.runtime import clear_caches
from api.settings import Settings
from tests.api_support import install_fake_model, make_client, png_bytes, post_image

pytestmark = pytest.mark.api


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    clear_caches()
    install_fake_model(monkeypatch)
    yield
    clear_caches()


def _client(registry_path: Path, **overrides):
    return make_client(registry_path(weights=True), **overrides)


def _assert_problem(response, status: int, type_: str) -> dict:
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == type_
    assert body["status"] == status
    assert body["detail"]
    assert body["request_id"] == response.headers["x-request-id"]
    return body


def test_default_upload_limit_is_25_mb():
    assert Settings().max_upload_mb == 25
    assert Settings().max_upload_bytes == 25 * 1024 * 1024
    # The request guard allows multipart overhead on top of the file cap.
    assert Settings().max_request_bytes > Settings().max_upload_bytes


def test_oversized_upload_is_rejected_while_streaming(api_registry):
    client = _client(api_registry, max_upload_mb=1)
    body = _assert_problem(post_image(client, png_bytes() + b"0" * (1024 * 1024)), 413, "payload_too_large")
    assert "1 MB" in body["detail"]


def test_oversized_request_is_rejected_before_parsing(api_registry):
    client = _client(api_registry)
    response = client.post(
        "/v1/detect",
        content=b"0" * (Settings().max_upload_bytes + 1024 * 1024),
        headers={"content-type": "multipart/form-data; boundary=boundary"},
    )
    body = _assert_problem(response, 413, "payload_too_large")
    assert "too large" in body["title"].lower()


def test_unsupported_format_is_415(api_registry):
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, format="GIF")
    _assert_problem(post_image(_client(api_registry), buffer.getvalue()), 415, "unsupported_media_type")


def test_corrupt_bytes_are_422(api_registry):
    _assert_problem(post_image(_client(api_registry), b"this is not an image"), 422, "invalid_image")


def test_truncated_png_is_422(api_registry):
    truncated = png_bytes()[:120]
    _assert_problem(post_image(_client(api_registry), truncated), 422, "invalid_image")


def test_empty_upload_is_422(api_registry):
    _assert_problem(post_image(_client(api_registry), b""), 422, "invalid_image")


def test_pixel_budget_is_enforced_before_decoding(api_registry):
    client = _client(api_registry, max_pixels=10_000)
    body = _assert_problem(post_image(client, png_bytes(320, 240)), 413, "payload_too_large")
    assert "pixels" in body["detail"]


def test_thresholds_are_validated(api_registry):
    client = _client(api_registry)
    body = _assert_problem(
        post_image(client, png_bytes(), confidence=2.0), 422, "invalid_request"
    )
    assert "confidence" in body["detail"]
    _assert_problem(post_image(client, png_bytes(), iou=0.0), 422, "invalid_request")


def test_model_unavailable_returns_503_without_detections(api_registry):
    """The critical honesty test: no weights, no boxes — and no invented metadata."""
    client = make_client(api_registry(weights=False))
    response = post_image(client, png_bytes())
    body = _assert_problem(response, 503, "model_unavailable")
    assert "detections" not in response.text
    assert "confidence" not in response.text
    assert body["detail"]
    for leaked in ("weights", "best.pt", "torch", "ultralytics"):
        assert leaked not in response.text.lower()


def test_model_load_failure_is_reported_honestly(api_registry, monkeypatch):
    clear_caches()
    install_fake_model(monkeypatch, loader_error=RuntimeError("CUDA exploded at /private/path"))
    response = post_image(_client(api_registry), png_bytes())
    body = _assert_problem(response, 503, "model_unavailable")
    assert "CUDA" not in response.text
    assert "/private/path" not in response.text
    assert body["request_id"]


def test_inference_failure_is_500_and_masked(api_registry, monkeypatch):
    clear_caches()

    class ExplodingModel:
        names = {0: "judah"}

        def __call__(self, *_args, **_kwargs):
            raise ValueError("tensor mismatch at /private/path")

    from app.core.detector import UltralyticsDetector

    def fake_build(spec, **_kwargs):
        return UltralyticsDetector(
            spec.id,
            spec.weights_path,
            declared_labels=spec.declared_labels,
            model_loader=lambda _path: ExplodingModel(),
        )

    monkeypatch.setattr("api.runtime.build_detector", fake_build)
    response = post_image(_client(api_registry), png_bytes())
    _assert_problem(response, 500, "inference_failed")
    assert "tensor mismatch" not in response.text
    assert "/private/path" not in response.text


def test_confidence_and_iou_are_echoed_as_applied(api_registry):
    body = post_image(_client(api_registry), png_bytes(), confidence=0.5, iou=0.3).json()
    assert body["thresholds"] == {"confidence": 0.5, "iou": 0.3}
