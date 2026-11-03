"""Shared fixtures.

No real face images and no real weights are used anywhere in the test suite:
fixtures are synthetic images and a fake Ultralytics-shaped model, so tests are
fast, licence-clean and runnable without PyTorch.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - safety net for odd runners
    sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------
@pytest.fixture
def rgb_image() -> Image.Image:
    """A small blank canvas; boxes drawn on it are easy to detect visually."""
    return Image.new("RGB", (320, 240), "white")


@pytest.fixture
def rgba_image() -> Image.Image:
    return Image.new("RGBA", (40, 30), (255, 0, 0, 128))


@pytest.fixture
def png_bytes(rgb_image: Image.Image) -> bytes:
    import io

    buffer = io.BytesIO()
    rgb_image.save(buffer, format="PNG")
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Fake Ultralytics model (duck-typed to the real API surface we rely on)
# --------------------------------------------------------------------------
class FakeBoxes:
    def __init__(self, rows, with_confidence: bool = True):
        self.xyxy = [[row[0], row[1], row[2], row[3]] for row in rows]
        self.conf = [row[4] for row in rows] if with_confidence else []
        self.cls = [row[5] if len(row) > 5 else 0 for row in rows]


class FakeResult:
    def __init__(self, rows, with_confidence: bool = True):
        self.boxes = FakeBoxes(rows, with_confidence=with_confidence)


class FakeModel:
    """Mimics `YOLO(...)`: has `.names` and is callable returning [result]."""

    def __init__(self, rows=(), names=None, with_confidence: bool = True):
        self.names = names if names is not None else {0: "judah"}
        self._rows = list(rows)
        self._with_confidence = with_confidence
        self.calls: list[dict] = []

    def __call__(self, source, conf=0.25, iou=0.45, verbose=False, **kwargs):
        self.calls.append({"source": source, "conf": conf, "iou": iou, "kwargs": kwargs})
        return [FakeResult(self._rows, with_confidence=self._with_confidence)]


@pytest.fixture
def detection_rows():
    """Two detections in pixel coordinates: (x1, y1, x2, y2, confidence, class)."""
    return [
        (10.0, 20.0, 110.0, 120.0, 0.90, 0),
        (200.0, 50.0, 280.0, 140.0, 0.55, 0),
    ]


@pytest.fixture
def fake_model(detection_rows) -> FakeModel:
    return FakeModel(detection_rows)


@pytest.fixture
def fake_loader(fake_model: FakeModel):
    """A `model_loader` callable that returns the fake model instead of YOLO."""

    def _load(_weights: str) -> FakeModel:
        return fake_model

    return _load


@pytest.fixture
def weights_file(tmp_path: Path) -> Path:
    """A stand-in .pt file. Contents are irrelevant: the loader is faked."""
    path = tmp_path / "best.pt"
    path.write_bytes(b"not-a-real-checkpoint")
    return path


@pytest.fixture
def registry_payload() -> dict:
    """Minimal valid registry payload for parsing tests."""
    return {
        "schema_version": 1,
        "default_model_id": "model-a",
        "models": [
            {
                "id": "model-a",
                "display_name": "Model A",
                "weights": "models/a/best.pt",
                "kind": "subject_specific",
                "is_general_purpose": False,
                "declared_labels": ["judah"],
                "dataset": {"total_images": 10},
            },
            {
                "id": "model-b",
                "display_name": "Model B",
                "weights": "models/b/best.pt",
                "kind": "general_purpose",
                "is_general_purpose": True,
                "enabled": False,
                "declared_labels": ["face"],
            },
        ],
    }
