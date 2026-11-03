"""Interface tests using Streamlit's AppTest (no browser required).

`AppTest.from_function` executes a function's source in a fresh script context
without the calling module's imports, so each page is exercised through a tiny
temporary entry script -- exactly the way `streamlit run` would load it.
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


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def test_main_entry_point_renders_home():
    at = AppTest.from_file(str(MAIN_SCRIPT), default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, at.exception
    assert "JUDEtector" in _texts(at.title)


def test_sidebar_shows_the_active_model():
    at = AppTest.from_file(str(MAIN_SCRIPT), default_timeout=TIMEOUT)
    at.run()
    assert "judah" in _texts(at.sidebar.markdown).lower()


# --------------------------------------------------------------------------
# Every page renders
# --------------------------------------------------------------------------
@pytest.mark.parametrize("module_name", ["home", "detect", "camera", "dashboard", "about"])
def test_each_view_renders_without_exception(tmp_path, module_name):
    at = _run_page(tmp_path, module_name)
    assert not at.exception, at.exception


def test_home_lists_registered_models(tmp_path):
    at = _run_page(tmp_path, "home")
    assert "Registered models" in _texts(at.subheader)


def test_detect_page_has_upload_controls_and_thresholds(tmp_path):
    at = _run_page(tmp_path, "detect")
    assert len(at.file_uploader) == 1
    assert len(at.slider) == 2
    labels = [slider.label for slider in at.slider]
    assert "Confidence threshold" in labels
    assert "IoU threshold (NMS)" in labels


def test_detect_page_prompts_before_any_analysis(tmp_path):
    at = _run_page(tmp_path, "detect")
    assert "Upload an image to begin" in _texts(at.info)


def test_detect_page_states_that_weights_are_missing(tmp_path):
    at = _run_page(tmp_path, "detect")
    assert "weights missing" in _texts(at.sidebar.caption).lower()


def test_scope_warning_is_shown_for_the_subject_model(tmp_path):
    at = _run_page(tmp_path, "detect")
    warning_text = _texts(at.warning).lower()
    assert "subject-specific" in warning_text
    assert "not a validated" in warning_text


def test_camera_page_explains_snapshot_scope(tmp_path):
    at = _run_page(tmp_path, "camera")
    assert len(at.camera_input) == 1
    combined = (_texts(at.info) + " " + _texts(at.caption)).lower()
    assert "snapshot mode" in combined


def test_changing_confidence_slider_reruns_cleanly(tmp_path):
    at = _run_page(tmp_path, "detect")
    at.slider[0].set_value(0.75).run()
    assert not at.exception, at.exception
    assert at.slider[0].value == pytest.approx(0.75)


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

    # Original and processed images are both displayed.
    assert len(at.get("image")) == 2  # original + processed
    assert len(at.get("download_button")) == 1

    # The run is recorded for the Dashboard, from real inference output.
    recorded = at.session_state.get("detection_runs")
    assert recorded and recorded[0]["face_count"] == 2
    assert recorded[0]["labels"] == ["judah"]

    # Labels shown come from the model, and the subject-specific caveat is present.
    assert "subject-specific" in _texts(at.warning).lower()


def test_detect_page_fabricates_nothing_when_weights_are_missing(tmp_path, png_bytes):
    """The critical honesty test: an upload with no model yields an error, not boxes."""
    at = _run_page(tmp_path, "detect")
    at.file_uploader[0].upload("sample.png", png_bytes, "image/png").run()
    assert not at.exception, at.exception

    assert "Model weights are not available" in _texts(at.error)
    assert "Detections" not in [metric.label for metric in at.metric]
    assert not at.session_state.get("detection_runs")
    assert len(at.get("download_button")) == 0


# --------------------------------------------------------------------------
# Dashboard honesty rules
# --------------------------------------------------------------------------
def test_dashboard_shows_no_metrics_when_none_are_recorded(tmp_path):
    at = _run_page(tmp_path, "dashboard")
    assert "No evaluation metrics recorded" in _texts(at.info)
    labels = [metric.label for metric in at.metric]
    assert "mAP@0.5" not in labels
    assert "Precision" not in labels
    assert "Recall" not in labels


def test_dashboard_has_no_session_statistics_before_any_run(tmp_path):
    at = _run_page(tmp_path, "dashboard")
    assert "No detections yet in this session" in _texts(at.info)


def test_dashboard_displays_recorded_metrics_verbatim(tmp_path, monkeypatch):
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


def test_dashboard_flags_an_invalid_metrics_record(tmp_path, monkeypatch):
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


# --------------------------------------------------------------------------
# About page
# --------------------------------------------------------------------------
def test_about_page_contains_student_details(tmp_path):
    at = _run_page(tmp_path, "about")
    combined = _texts(at.markdown)
    assert "PUIT/23110016" in combined
    assert "Senyo-Dzattah Judah Agbemavor" in combined
    assert "Pentecost University" in combined


def test_about_page_states_detection_is_not_recognition(tmp_path):
    at = _run_page(tmp_path, "about")
    assert "Detection is not recognition" in _texts(at.markdown)


def test_about_page_reports_dataset_scope(tmp_path):
    at = _run_page(tmp_path, "about")
    combined = _texts(at.markdown)
    assert "711" in combined
    assert "judah" in combined
