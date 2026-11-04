"""Shared helpers for the API contract tests."""

from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from api.main import create_app
from api.settings import Settings
from tests.conftest import FakeModel

DETECTION_ROWS = [(40, 30, 160, 150, 0.91, 0), (180, 60, 290, 200, 0.62, 0)]


def png_bytes(width: int = 320, height: int = 240) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def make_client(registry_path: Path | None, **overrides) -> TestClient:
    """Build a TestClient with explicit settings (no environment leakage)."""
    overrides.setdefault("environment", "test")
    settings = Settings(registry_path=registry_path, **overrides)
    return TestClient(create_app(settings), raise_server_exceptions=False)


def install_fake_model(monkeypatch, rows=None, *, loader_error: Exception | None = None) -> FakeModel:
    """Make the API's detector factory return a fake Ultralytics-shaped model."""
    from app.core.detector import UltralyticsDetector

    fake = FakeModel(DETECTION_ROWS if rows is None else rows)

    def fake_build(spec, **_kwargs):
        def _loader(_path: str):
            if loader_error is not None:
                raise loader_error
            return fake

        return UltralyticsDetector(
            spec.id,
            spec.weights_path,
            display_name=spec.display_name,
            declared_labels=spec.declared_labels,
            model_loader=_loader,
        )

    monkeypatch.setattr("api.runtime.build_detector", fake_build)
    return fake


def post_image(
    client: TestClient,
    data: bytes,
    *,
    headers: dict[str, str] | None = None,
    filename: str = "sample.png",
    **form,
):
    payload = {"confidence": 0.25, "iou": 0.45, **form}
    return client.post(
        "/v1/detect",
        files={"file": (filename, data, "image/png")},
        data=payload,
        headers=headers or {},
    )
