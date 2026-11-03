"""Interface tests using Streamlit's AppTest (no browser required).

`AppTest.from_function` executes a function's source in a fresh script context
without the calling module's imports, so each page is exercised through a tiny
temporary entry script -- exactly the way `streamlit run` would load it.

These tests cover the redesigned interface. Tests that protect detection
correctness live in test_detector.py / test_pipeline.py / test_metrics.py and are
independent of presentation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.core import config

pytestmark = pytest.mark.ui

TIMEOUT = 60
PROJECT_ROOT = Path(config.PROJECT_ROOT)
MAIN_SCRIPT = PROJECT_ROOT / "app" / "main.py"


@pytest.fixture(autouse=True)
def _clear_caches():
    """Registry/detector caches are process-wide; keep UI tests isolated."""
    from app.core.runtime import clear_detector_cache, get_registry

    get_registry.clear()
    clear_detector_cache()
    yield
    get_registry.clear()
    clear_detector_cache()


def _run_page(tmp_path: Path, module_name: str) -> AppTest:
    """Run a single view as its own Streamlit script."""
    script = tmp_path / f"page_{module_name}.py"
    script.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(PROJECT_ROOT)!r})\n"
        f"from app.views.{module_name} import render\n"
        "render()\n",
        encoding="utf-8",
    )
    app = AppTest.from_file(str(script), default_timeout=TIMEOUT)
    app.run()
    return app


def _texts(elements) -> str:
    return " ".join(str(getattr(element, "value", "")) for element in elements)


def _page_text(app: AppTest) -> str:
    """All rendered markdown for a run (custom primitives render as markdown)."""
    return _texts(app.markdown)


# --------------------------------------------------------------------------
# Entry point and navigation
# --------------------------------------------------------------------------
def test_main_entry_point_renders_overview():
    at = AppTest.from_file(str(MAIN_SCRIPT), default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, at.exception
    assert "Overview" in _page_text(at)


def test_navigation_uses_five_labelled_pages_without_emoji_icons():
    from app.ui.nav import PAGE

    titles = [page.title for page in PAGE.values()]
    assert titles == ["Overview", "Detect", "Camera", "Analytics", "About"]
    for page in PAGE.values():
        icon = page.icon or ""
        assert icon.startswith(":material/"), f"{page.title} icon is not an SVG icon: {icon}"
        assert icon.isascii(), f"{page.title} icon contains a non-ASCII (emoji) glyph"


def test_sidebar_shows_the_active_model_status():
    at = AppTest.from_file(str(MAIN_SCRIPT), default_timeout=TIMEOUT)
    at.run()
    sidebar_text = _texts(at.sidebar.markdown).lower()
    assert "judah" in sidebar_text
    assert "weights missing" in sidebar_text


# --------------------------------------------------------------------------
# Every page renders
# --------------------------------------------------------------------------
@pytest.mark.parametrize("module_name", ["home", "detect", "camera", "dashboard", "about"])
def test_each_view_renders_without_exception(tmp_path, module_name):
    at = _run_page(tmp_path, module_name)
    assert not at.exception, at.exception


def test_overview_offers_primary_workspace_actions(tmp_path):
    at = _run_page(tmp_path, "home")
    labels = [button.label for button in at.button]
    assert "Upload an image" in labels
    assert "Open camera" in labels


def test_overview_reports_model_connection_state(tmp_path):
    at = _run_page(tmp_path, "home")
    text = _page_text(at)
    assert "Model status" in text
    assert "Not connected" in text  # repository ships no weights


# --------------------------------------------------------------------------
# Detect page
# --------------------------------------------------------------------------
def test_detect_page_has_upload_controls_and_thresholds(tmp_path):
    at = _run_page(tmp_path, "detect")
    assert len(at.file_uploader) == 1
    assert len(at.slider) == 2
    labels = [slider.label for slider in at.slider]
    assert "Confidence threshold" in labels
    assert "IoU threshold (NMS)" in labels


def test_detect_page_shows_empty_state_before_upload(tmp_path):
    at = _run_page(tmp_path, "detect")
    assert "No image selected" in _page_text(at)


def test_detect_page_states_that_weights_are_missing(tmp_path):
    at = _run_page(tmp_path, "detect")
    text = _page_text(at)
    assert "Model not connected" in text
    assert "Detection is unavailable until model weights are connected" in text


def test_scope_limitation_is_stated_on_working_pages(tmp_path):
    at = _run_page(tmp_path, "detect")
    text = _page_text(at).lower()
    assert "subject-specific" in text
    assert "not a validated general-purpose face detector" in text


def test_changing_confidence_slider_reruns_cleanly(tmp_path):
    at = _run_page(tmp_path, "detect")
    at.slider[0].set_value(0.75).run()
    assert not at.exception, at.exception
    assert at.slider[0].value == pytest.approx(0.75)


# --------------------------------------------------------------------------
# Camera page
# --------------------------------------------------------------------------
def test_camera_page_offers_snapshot_capture_only(tmp_path):
    at = _run_page(tmp_path, "camera")
    assert len(at.camera_input) == 1
    text = _page_text(at)
    assert "Snapshot capture" in text
    assert "Live video detection is not supported" in text


def test_camera_page_shows_awaiting_capture_state(tmp_path):
    at = _run_page(tmp_path, "camera")
    assert "Awaiting capture" in _page_text(at)


# --------------------------------------------------------------------------
# End-to-end detection through the Detect page
# --------------------------------------------------------------------------
def _write_single_model_registry(tmp_path: Path, weights: Path) -> Path:
    registry_path = tmp_path / "models.json"
    registry_path.write_text(
        json.dumps(
            {
                "default_model_id": "fixture-model",
                "models": [
                    {
                        "id": "fixture-model",
                        "display_name": "Fixture model",
                        "weights": str(weights),
                        "kind": "subject_specific",
                        "declared_labels": ["judah"],
                        "dataset": {"total_images": 4, "classes": ["judah"]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return registry_path


def test_detect_page_runs_end_to_end_and_reports_real_scores(tmp_path, monkeypatch, png_bytes):
    """Upload -> inference -> boxes, count and confidence scores, using a fake model."""
    from app.core import runtime
    from app.core.detector import UltralyticsDetector
    from tests.conftest import FakeModel

    weights = tmp_path / "best.pt"
    weights.write_bytes(b"stub")
    registry_path = _write_single_model_registry(tmp_path, weights)
    monkeypatch.setenv(config.ENV_REGISTRY_PATH, str(registry_path))

    rows = [(40, 30, 160, 150, 0.91, 0), (180, 60, 290, 200, 0.62, 0)]
    fake_model = FakeModel(rows)

    def fake_build(spec, **_kwargs):
        return UltralyticsDetector(
            spec.id,
            spec.weights_path,
            display_name=spec.display_name,
            declared_labels=spec.declared_labels,
            model_loader=lambda _path: fake_model,
        )

    monkeypatch.setattr(runtime, "build_detector", fake_build)

    at = _run_page(tmp_path, "detect")
    at.file_uploader[0].upload("sample.png", png_bytes, "image/png").run()
    assert not at.exception, at.exception

    metrics = {metric.label: metric.value for metric in at.metric}
    assert metrics["Detections"] == "2"
    assert metrics["Mean confidence"] == "76.5%"  # (0.91 + 0.62) / 2
    assert metrics["Confidence range"] == "0.62 – 0.91"

    # Original and annotated images are both displayed.
    assert len(at.get("image")) == 2
    assert len(at.get("download_button")) == 1

    # The run is recorded for Analytics, from real inference output.
    recorded = at.session_state.get("detection_runs")
    assert recorded and recorded[0]["face_count"] == 2
    assert recorded[0]["labels"] == ["judah"]

    # The subject-specific limitation remains visible alongside results.
    assert "subject-specific" in _page_text(at).lower()


def test_detect_page_fabricates_nothing_when_weights_are_missing(tmp_path, png_bytes):
    """The critical honesty test: an upload with no model yields an error, not boxes."""
    at = _run_page(tmp_path, "detect")
    at.file_uploader[0].upload("sample.png", png_bytes, "image/png").run()
    assert not at.exception, at.exception

    assert "Model weights are not available" in _texts(at.error)
    assert "Detections" not in [metric.label for metric in at.metric]
    assert not at.session_state.get("detection_runs")
    assert len(at.get("download_button")) == 0
    assert len(at.get("image")) == 0


# --------------------------------------------------------------------------
# Analytics honesty rules
# --------------------------------------------------------------------------
def test_analytics_shows_no_metrics_when_none_are_recorded(tmp_path):
    at = _run_page(tmp_path, "dashboard")
    assert "No evaluation metrics recorded" in _page_text(at)
    labels = [metric.label for metric in at.metric]
    assert "mAP@0.5" not in labels
    assert "Precision" not in labels
    assert "Recall" not in labels


def test_analytics_has_no_session_activity_before_any_run(tmp_path):
    at = _run_page(tmp_path, "dashboard")
    assert "No detections yet in this session" in _page_text(at)


def test_analytics_displays_recorded_metrics_verbatim(tmp_path, monkeypatch):
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"stub")
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "model_id": "fixture-model",
                "split": "test",
                "evaluated_on": "2026-11-15",
                "source": "unit test fixture",
                "metrics": {"mAP50": 0.834, "precision": 0.81, "recall": 0.79},
            }
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "models.json"
    registry_path.write_text(
        json.dumps(
            {
                "default_model_id": "fixture-model",
                "models": [
                    {
                        "id": "fixture-model",
                        "display_name": "Fixture model",
                        "weights": str(weights),
                        "kind": "subject_specific",
                        "declared_labels": ["judah"],
                        "metrics_file": str(metrics_path),
                        "dataset": {"total_images": 4, "classes": ["judah"]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(config.ENV_REGISTRY_PATH, str(registry_path))

    at = _run_page(tmp_path, "dashboard")
    assert not at.exception, at.exception

    values = {metric.label: metric.value for metric in at.metric}
    assert values["mAP@0.5"] == "0.8340"
    assert values["Precision"] == "0.8100"
    assert values["Recall"] == "0.7900"


def test_analytics_flags_an_invalid_metrics_record(tmp_path, monkeypatch):
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"stub")
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"model_id": "fixture-model", "metrics": {"mAP50": 91.4}}), encoding="utf-8"
    )
    registry_path = tmp_path / "models.json"
    registry_path.write_text(
        json.dumps(
            {
                "default_model_id": "fixture-model",
                "models": [
                    {
                        "id": "fixture-model",
                        "display_name": "Fixture model",
                        "weights": str(weights),
                        "declared_labels": ["judah"],
                        "metrics_file": str(metrics_path),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(config.ENV_REGISTRY_PATH, str(registry_path))

    at = _run_page(tmp_path, "dashboard")
    assert "metrics record is invalid" in _texts(at.error).lower()


def test_analytics_summarises_session_activity(tmp_path):
    at = _run_page(tmp_path, "dashboard")
    at.session_state["detection_runs"] = [
        {
            "source": "upload",
            "filename": "example.jpg",
            "model_id": "judah-face-v1",
            "face_count": 3,
            "image_width": 640,
            "image_height": 480,
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "mean_confidence": 0.8,
            "min_confidence": 0.61,
            "max_confidence": 0.94,
            "inference_ms": 120.0,
            "labels": ["judah"],
            "timestamp": "2026-11-03T10:00:00+00:00",
        }
    ]
    at.run()
    assert not at.exception, at.exception
    metrics = {metric.label: metric.value for metric in at.metric}
    assert metrics["Runs"] == "1"
    assert metrics["Total detections"] == "3"
    assert metrics["Mean confidence"] == "80.0%"


# --------------------------------------------------------------------------
# About page: product content, no academic details
# --------------------------------------------------------------------------
def test_about_page_states_detection_is_not_recognition(tmp_path):
    at = _run_page(tmp_path, "about")
    assert "Detection is not recognition" in _page_text(at)


def test_about_page_documents_model_limitations(tmp_path):
    at = _run_page(tmp_path, "about")
    text = _page_text(at).lower()
    assert "model limitations" in text
    assert "not a validated general-purpose face detector" in text
    assert "not a face-recognition system" in text


def test_about_page_keeps_technical_dataset_detail_in_an_expander(tmp_path):
    at = _run_page(tmp_path, "about")
    text = _page_text(at)
    assert "711" in text
    assert "judah" in text
    assert len(at.expander) >= 1


@pytest.mark.parametrize(
    "academic_detail",
    ["PUIT/23110016", "Senyo-Dzattah", "Pentecost University", "BSc Information Technology"],
)
def test_application_contains_no_academic_details(tmp_path, academic_detail):
    """Student, programme and institution details must not appear in the product."""
    at_main = AppTest.from_file(str(MAIN_SCRIPT), default_timeout=TIMEOUT)
    at_main.run()

    rendered = _page_text(at_main) + _texts(at_main.sidebar.markdown)
    assert academic_detail not in rendered

    for page in ("about", "home", "dashboard", "detect", "camera"):
        at = _run_page(tmp_path, page)
        page_rendered = _page_text(at) + _texts(at.sidebar.markdown)
        assert academic_detail not in page_rendered, f"{academic_detail} leaked into {page}"
