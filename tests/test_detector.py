"""Detector contract and -- critically -- the no-fabrication guarantees."""

from __future__ import annotations

import importlib.util

import pytest
from PIL import Image

from app.core.detector import Detection, DetectionResult, UltralyticsDetector
from app.core.errors import ModelLoadError, ModelUnavailableError
from tests.conftest import FakeModel


def _detector(weights, loader, *, labels=("judah",)):
    return UltralyticsDetector(
        model_id="test-model",
        weights_path=weights,
        display_name="Test model",
        declared_labels=labels,
        model_loader=loader,
    )


# --------------------------------------------------------------------------
# Availability / loading
# --------------------------------------------------------------------------
def test_missing_weights_means_unavailable(tmp_path, fake_loader):
    detector = _detector(tmp_path / "absent.pt", fake_loader)
    assert detector.is_available() is False
    assert detector.is_ready() is False


def test_load_with_missing_weights_raises_with_path(tmp_path, fake_loader):
    missing = tmp_path / "absent.pt"
    detector = _detector(missing, fake_loader)
    with pytest.raises(ModelUnavailableError) as excinfo:
        detector.load()
    assert str(missing) in str(excinfo.value)
    assert "JUDETECTOR_MODEL_PATH" in str(excinfo.value)


def test_predict_before_load_raises(weights_file, fake_loader):
    detector = _detector(weights_file, fake_loader)
    image = Image.new("RGB", (32, 32), "white")
    with pytest.raises(ModelUnavailableError):
        detector.predict(image, confidence=0.25, iou=0.45)


def test_load_is_idempotent_and_sets_ready(weights_file, fake_loader):
    detector = _detector(weights_file, fake_loader)
    detector.load()
    detector.load()
    assert detector.is_ready() is True


def test_load_reads_labels_from_the_model_file(weights_file):
    model = FakeModel(names={0: "judah", 1: "other"})
    detector = _detector(weights_file, lambda _p: model, labels=("stale",))
    assert detector.labels_source == "declared"
    detector.load()
    assert detector.labels == ("judah", "other")
    assert detector.labels_source == "model"


def test_labels_source_unknown_without_declared_or_loaded(weights_file, fake_loader):
    detector = _detector(weights_file, fake_loader, labels=())
    assert detector.labels == ()
    assert detector.labels_source == "unknown"


def test_loader_failure_is_wrapped_as_model_load_error(weights_file):
    def broken(_weights):
        raise RuntimeError("corrupt checkpoint")

    detector = _detector(weights_file, broken)
    with pytest.raises(ModelLoadError) as excinfo:
        detector.load()
    assert "corrupt checkpoint" in str(excinfo.value)


@pytest.mark.skipif(
    importlib.util.find_spec("ultralytics") is not None,
    reason="ultralytics is installed; the missing-package path cannot be exercised",
)
def test_default_loader_reports_missing_ml_stack(weights_file):
    """With weights present but no ultralytics installed, the error must be actionable."""
    detector = _detector(weights_file, loader=None)
    with pytest.raises(ModelUnavailableError) as excinfo:
        detector.load()
    assert "requirements-model.txt" in str(excinfo.value)


# --------------------------------------------------------------------------
# Inference / parsing
# --------------------------------------------------------------------------
def test_predict_returns_detections_from_model_output(weights_file, fake_loader, rgb_image):
    detector = _detector(weights_file, fake_loader)
    detector.load()
    result = detector.predict(rgb_image, confidence=0.3, iou=0.5)

    assert isinstance(result, DetectionResult)
    assert result.count == 2
    assert [d.label for d in result.detections] == ["judah", "judah"]
    assert result.detections[0].box_xyxy == (10.0, 20.0, 110.0, 120.0)
    assert result.detections[0].confidence == pytest.approx(0.90)
    assert result.image_width == 320
    assert result.image_height == 240


def test_predict_forwards_thresholds_to_the_model(weights_file, fake_model, rgb_image):
    detector = _detector(weights_file, lambda _p: fake_model)
    detector.load()
    detector.predict(rgb_image, confidence=0.42, iou=0.33)
    call = fake_model.calls[-1]
    assert call["conf"] == pytest.approx(0.42)
    assert call["iou"] == pytest.approx(0.33)


def test_predict_records_non_negative_inference_time(weights_file, fake_loader, rgb_image):
    detector = _detector(weights_file, fake_loader)
    detector.load()
    result = detector.predict(rgb_image, confidence=0.25, iou=0.45)
    assert result.inference_ms >= 0.0


def test_empty_model_output_yields_zero_detections(weights_file, rgb_image):
    detector = _detector(weights_file, lambda _p: FakeModel(rows=()))
    detector.load()
    result = detector.predict(rgb_image, confidence=0.25, iou=0.45)
    assert result.count == 0
    assert result.mean_confidence is None
    assert result.records() == []


def test_boxes_without_confidences_are_rejected_not_invented(weights_file, rgb_image):
    model = FakeModel(rows=[(1, 2, 3, 4, 0.9, 0)], with_confidence=False)
    detector = _detector(weights_file, lambda _p: model)
    detector.load()
    with pytest.raises(ModelLoadError) as excinfo:
        detector.predict(rgb_image, confidence=0.25, iou=0.45)
    assert "confidence" in str(excinfo.value).lower()


def test_unknown_class_index_falls_back_to_a_neutral_label(weights_file, rgb_image):
    model = FakeModel(rows=[(1, 2, 3, 4, 0.9, 7)])
    detector = _detector(weights_file, lambda _p: model)
    detector.load()
    result = detector.predict(rgb_image, confidence=0.25, iou=0.45)
    assert result.detections[0].label == "class_7"


@pytest.mark.parametrize("bad", [-0.1, 1.5, 2])
def test_invalid_confidence_is_rejected(weights_file, fake_loader, rgb_image, bad):
    detector = _detector(weights_file, fake_loader)
    detector.load()
    with pytest.raises(ValueError):
        detector.predict(rgb_image, confidence=bad, iou=0.45)


def test_non_image_input_is_rejected(weights_file, fake_loader):
    detector = _detector(weights_file, fake_loader)
    detector.load()
    with pytest.raises(TypeError):
        detector.predict("not-an-image", confidence=0.25, iou=0.45)


# --------------------------------------------------------------------------
# Result value object
# --------------------------------------------------------------------------
def test_result_statistics():
    result = DetectionResult(
        detections=(
            Detection((0, 0, 10, 10), 0.80, "judah"),
            Detection((5, 5, 30, 40), 0.40, "judah"),
        )
    )
    assert result.count == 2
    assert result.mean_confidence == pytest.approx(0.60)
    assert result.min_confidence == pytest.approx(0.40)
    assert result.max_confidence == pytest.approx(0.80)
    assert result.labels_present == ("judah",)


def test_record_shape_is_stable():
    record = Detection((10, 20, 40, 60), 0.123456, "judah").to_record()
    assert set(record) == {"label", "confidence", "x1", "y1", "width", "height"}
    assert record["confidence"] == 0.1235  # rounded for display only
    assert record["width"] == 30.0
    assert record["height"] == 40.0


def test_model_info_reports_provenance(weights_file, fake_loader):
    detector = _detector(weights_file, fake_loader)
    info = detector.model_info()
    assert info["model_id"] == "test-model"
    assert info["weights_present"] is True
    assert info["loaded"] is False
    assert info["labels_source"] == "declared"
