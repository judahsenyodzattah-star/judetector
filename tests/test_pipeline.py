"""The shared Detect/Camera pipeline: success and every failure path."""

from __future__ import annotations

from app.components.pipeline import analyse_image
from app.core.detector import UltralyticsDetector
from app.core.errors import ModelUnavailableError
from app.core.registry import ModelSpec
from tests.conftest import FakeModel


def _spec(weights, *, general=False):
    return ModelSpec(
        id="test-model",
        display_name="Test model",
        weights_path=weights,
        declared_labels=("judah",),
        is_general_purpose=general,
    )


def test_successful_analysis_returns_result_and_processed_image(weights_file, fake_loader, rgb_image):
    spec = _spec(weights_file)
    detector = UltralyticsDetector("test-model", weights_file, model_loader=fake_loader)

    outcome = analyse_image(rgb_image, spec, detector, confidence=0.25, iou=0.45)

    assert outcome.ok is True
    assert outcome.result is not None and outcome.result.count == 2
    assert outcome.processed is not None
    assert outcome.processed.size == rgb_image.size
    assert outcome.processed.tobytes() != rgb_image.tobytes()  # boxes actually drawn
    assert outcome.count == 2


def test_missing_weights_yields_unavailable_outcome(tmp_path, rgb_image):
    spec = _spec(tmp_path / "absent.pt")
    detector = UltralyticsDetector("test-model", tmp_path / "absent.pt")
    outcome = analyse_image(rgb_image, spec, detector, confidence=0.25, iou=0.45)

    assert outcome.ok is False
    assert outcome.unavailable is True
    assert outcome.result is None
    assert outcome.processed is None
    assert "will not display detections" in outcome.error_message


def test_loader_raising_unavailable_is_reported(weights_file, rgb_image):
    def unavailable(_path):
        raise ModelUnavailableError("ultralytics missing")

    spec = _spec(weights_file)
    detector = UltralyticsDetector("test-model", weights_file, model_loader=unavailable)
    outcome = analyse_image(rgb_image, spec, detector, confidence=0.25, iou=0.45)

    assert outcome.ok is False
    assert outcome.unavailable is True
    assert outcome.error_message == "ultralytics missing"


def test_inference_error_is_reported_not_hidden(weights_file, rgb_image):
    class ExplodingModel(FakeModel):
        def __call__(self, *args, **kwargs):
            raise RuntimeError("CUDA on fire")

    spec = _spec(weights_file)
    detector = UltralyticsDetector("test-model", weights_file, model_loader=lambda _p: ExplodingModel())
    outcome = analyse_image(rgb_image, spec, detector, confidence=0.25, iou=0.45)

    assert outcome.ok is False
    assert outcome.unavailable is False
    assert "Detection failed" in outcome.error_title
    assert "CUDA on fire" in outcome.error_message


def test_zero_detection_result_is_still_a_success(weights_file, rgb_image):
    spec = _spec(weights_file)
    detector = UltralyticsDetector(
        "test-model", weights_file, model_loader=lambda _p: FakeModel(rows=())
    )
    outcome = analyse_image(rgb_image, spec, detector, confidence=0.25, iou=0.45)

    assert outcome.ok is True
    assert outcome.count == 0
    assert outcome.processed is not None
    # nothing drawn -> identical pixels
    assert outcome.processed.tobytes() == rgb_image.tobytes()


def test_detector_is_loaded_once_across_calls(weights_file, fake_model, rgb_image):
    spec = _spec(weights_file)
    detector = UltralyticsDetector("test-model", weights_file, model_loader=lambda _p: fake_model)
    analyse_image(rgb_image, spec, detector, confidence=0.25, iou=0.45)
    analyse_image(rgb_image, spec, detector, confidence=0.5, iou=0.45)
    assert detector.is_ready() is True
    assert len(fake_model.calls) == 2


def test_general_purpose_flag_does_not_change_pipeline(weights_file, fake_loader, rgb_image):
    spec = _spec(weights_file, general=True)
    detector = UltralyticsDetector(
        "test-model", weights_file, model_loader=fake_loader, is_general_purpose=True
    )
    outcome = analyse_image(rgb_image, spec, detector, confidence=0.25, iou=0.45)
    assert outcome.ok is True
