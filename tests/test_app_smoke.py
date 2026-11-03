"""Interface tests using Streamlit's AppTest (no browser required).

`AppTest.from_function` executes a function's source in a fresh script context
without the calling module's imports, so each page is exercised through a tiny
temporary entry script -- exactly the way `streamlit run` would load it.

These tests describe the *end-user* product: Detect, Camera and Help. The
developer page is exercised separately. Tests that protect detection correctness
live in test_detector.py / test_pipeline.py / test_metrics.py and are independent
of presentation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.components.results import readout_fields
from app.core import config

pytestmark = pytest.mark.ui

TIMEOUT = 60
PROJECT_ROOT = Path(config.PROJECT_ROOT)
MAIN_SCRIPT = PROJECT_ROOT / "app" / "main.py"

# Vocabulary that belongs to developers, never to the end-user interface.
TECHNICAL_TERMS = (
    "weights",
    "best.pt",
    "pip install",
    "requirements-model",
    "models.json",
    "registry",
    "ultralytics",
    "torch",
    "mAP",
    "config/",
    "MODEL_INTEGRATION",
)


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
    """Rendered markdown for a run, excluding the injected stylesheet."""
    return " ".join(
        str(element.value)
        for element in app.markdown
        if not str(element.value).lstrip().startswith("<style")
    )


def _visible_text(app: AppTest) -> str:
    """Page text with all markup removed — what a reader actually sees."""
    return re.sub(r"<[^>]+>", " ", _page_text(app))


def _interactive_text(app: AppTest) -> str:
    """Everything a reader can see: markdown, captions, buttons, alerts, labels."""
    parts = [
        _page_text(app),
        _texts(app.caption),
        _texts(app.button),
        _texts(app.error),
        _texts(app.info),
        _texts(app.warning),
        _texts(app.file_uploader),
        _texts(app.camera_input),
        _texts(app.slider),
    ]
    return " ".join(parts).lower()


# --------------------------------------------------------------------------
# Information architecture
# --------------------------------------------------------------------------
def test_visible_navigation_is_task_oriented():
    from app.ui.nav import ENTRIES

    assert [entry.title for entry in ENTRIES] == ["Home", "Detect", "Camera", "Help"]
    assert [entry.url_path for entry in ENTRIES] == ["home", "detect", "camera", "help"]
    assert all(not entry.hidden for entry in ENTRIES)


def test_home_is_the_single_default_route():
    from app.ui.nav import DEVELOPER, ENTRIES

    defaults = [entry.key for entry in (*ENTRIES, DEVELOPER) if entry.default]
    assert defaults == ["home"]


def test_navigation_icons_are_svg_not_emoji():
    from app.ui.nav import DEVELOPER, ENTRIES

    for entry in (*ENTRIES, DEVELOPER):
        assert entry.icon.startswith(":material/"), f"{entry.title} is not an SVG icon"
        assert entry.icon.isascii(), f"{entry.title} uses a non-ASCII (emoji) glyph"


def test_developer_page_is_hidden_but_routable():
    from app.ui.nav import DEVELOPER, ENTRIES

    assert DEVELOPER.title == "Developer"
    assert DEVELOPER.hidden is True
    assert DEVELOPER.url_path == "developer"
    assert DEVELOPER.key not in [entry.key for entry in ENTRIES]


def _run_main() -> AppTest:
    at = AppTest.from_file(str(MAIN_SCRIPT), default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, at.exception
    return at


def test_main_entry_point_opens_the_landing_page():
    at = _run_main()
    text = _page_text(at)
    assert "See exactly what the model sees." in text
    assert "Upload an image or take a snapshot" in text


# --------------------------------------------------------------------------
# Landing page
# --------------------------------------------------------------------------
def test_home_is_one_headline_one_sentence_one_action(tmp_path):
    at = _run_page(tmp_path, "home")
    text = _page_text(at)
    assert "See exactly what the model sees." in text
    assert "Upload an image or take a snapshot" in text
    # Exactly one button, and it is the primary action.
    assert [button.label for button in at.button] == ["Analyse an image"]
    assert at.button[0].proto.type == "primary"


def test_home_has_no_marketing_scaffolding(tmp_path):
    """The landing-page formula is deliberately absent."""
    at = _run_page(tmp_path, "home")
    visible = _visible_text(at)
    lowered = visible.lower()
    for phrase in (
        "image analysis, simplified",
        "get started free",
        "trusted by",
        "powered by ai",
        "state of the art",
        "cutting-edge",
        "seamless",
        "revolutionary",
        "supercharge",
        "unlock",
        "effortless",
    ):
        assert phrase not in lowered, f"marketing phrase on Home: {phrase!r}"
    # One primary action, not a pair of competing CTAs, and no emoji headings.
    assert len(at.button) == 1
    assert not re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", visible)


def test_home_illustration_is_declared_as_an_illustration(tmp_path):
    at = _run_page(tmp_path, "home")
    captions = _texts(at.caption)
    assert "Illustration, not an actual detection result." in captions
    # No invented scores, counts, timings or percentages anywhere on the page.
    visible = _visible_text(at) + " " + captions
    assert "%" not in visible
    assert not re.search(r"\d+(\.\d+)?\s*(ms|fps|faces?|detections?)\b", visible, re.I)
    lowered = visible.lower()
    assert "confidence" not in re.sub(r"confidence score", "", lowered)


def test_home_states_the_flow_once(tmp_path):
    at = _run_page(tmp_path, "home")
    text = _page_text(at)
    for station in ("Upload or capture", "Analyse", "Review", "Download"):
        assert station in text
    assert "How it works" not in text


def test_home_mounts_the_specimen_twice(tmp_path):
    """Original and annotated, labelled, in that order."""
    at = _run_page(tmp_path, "home")
    text = _page_text(at)
    assert text.count("jd-plate\"") == 2
    assert "Original" in text and "Annotated" in text
    assert text.index(">Original<") < text.index(">Annotated<")


def test_home_plates_differ_only_by_the_marking():
    """The annotated plate is the same specimen plus one marking rectangle.

    This is the promise the caption makes, so it is asserted on the artwork rather
    than trusted: strip the marking and the two drawings must be identical, and the
    marking must use the marking colour and nothing else.
    """
    from app.ui.theme import PALETTE
    from app.views.home import specimen_svg

    original = specimen_svg(annotated=False)
    annotated = specimen_svg(annotated=True)
    marking = (
        f'<rect x="126" y="40" width="68" height="76" fill="none" '
        f'stroke="{PALETTE["mark"]}" stroke-width="3"/>'
    )
    assert marking in annotated
    assert annotated.replace(marking, "") == original
    assert PALETTE["mark"] not in original
    # No numbers, scores or units are drawn on the artwork.
    assert not re.search(r"\\d", original + annotated)


def test_home_footer_has_brand_privacy_and_help_link(tmp_path):
    at = _run_page(tmp_path, "home")
    text = _page_text(at)
    assert "JUDEtector" in text
    assert "never stored" in text
    assert "Detection is not recognition" in text
    assert [link.label for link in at.get("page_link")] == ["Use the camera instead", "Help"]


def test_help_page_explains_the_flow_in_three_steps(tmp_path):
    at = _run_page(tmp_path, "help")
    text = _page_text(at)
    for title in ("Upload or capture", "Analyse", "Review and download"):
        assert title in text
    assert "How it works" in text


def test_primary_action_navigates_to_detect():
    """Clicking the landing action in the running app must land on Detect."""
    at = _run_main()
    labels = [button.label for button in at.button]
    assert "Analyse an image" in labels

    at.button[labels.index("Analyse an image")].click().run()
    assert not at.exception, at.exception
    assert at.file_uploader, "'Analyse an image' did not land on a page with an uploader"
    assert "See exactly what the model sees." not in _page_text(at)


def test_sidebar_carries_no_model_diagnostics():
    at = AppTest.from_file(str(MAIN_SCRIPT), default_timeout=TIMEOUT)
    at.run()
    sidebar = _texts(at.sidebar.markdown).lower()
    for term in ("weights", "judah", "model", "registry", "ultralytics"):
        assert term not in sidebar, f"'{term}' leaked into the sidebar"


# --------------------------------------------------------------------------
# Every page renders
# --------------------------------------------------------------------------
@pytest.mark.parametrize("module_name", ["home", "detect", "camera", "help", "dev"])
def test_each_view_renders_without_exception(tmp_path, module_name):
    at = _run_page(tmp_path, module_name)
    assert not at.exception, at.exception


# --------------------------------------------------------------------------
# Detect: the first-run experience
# --------------------------------------------------------------------------
def test_home_has_no_technical_detail(tmp_path):
    text = _interactive_text(_run_page(tmp_path, "home"))
    for term in TECHNICAL_TERMS:
        assert term not in text, f"'{term}' appears on the Home page"


def test_detect_offers_an_upload_control_and_no_technical_detail(tmp_path):
    at = _run_page(tmp_path, "detect")
    assert len(at.file_uploader) == 1
    assert at.file_uploader[0].label == "Image file"
    # Secondary controls stay out of the way until an image exists.
    assert len(at.get("expander")) == 0
    text = _interactive_text(at)
    for term in TECHNICAL_TERMS:
        assert term not in text, f"'{term}' appears in the user-facing Detect page"
    assert "upload" in text


def test_detect_explains_accepted_files_and_size_limit(tmp_path):
    text = _page_text(_run_page(tmp_path, "detect"))
    assert "JPG, PNG, WEBP or BMP" in text
    assert "25 MB" in text


def test_detect_moves_thresholds_into_a_collapsed_advanced_panel(tmp_path, png_bytes):
    at = _run_page(tmp_path, "detect")
    # Nothing to configure until there is an image to analyse.
    assert len(at.get("expander")) == 0

    at.file_uploader[0].upload("sample.png", png_bytes, "image/png").run()
    expanders = list(at.expander)
    assert len(expanders) == 1
    assert expanders[0].label == "Advanced settings"
    assert expanders[0].proto.expanded is False
    labels = [slider.label for slider in at.slider]
    assert "Confidence threshold" in labels
    assert any("IoU" in label for label in labels)


# --------------------------------------------------------------------------
# End-to-end detection through the Detect page
# --------------------------------------------------------------------------
def _write_single_model_registry(tmp_path: Path, weights: Path, **extra) -> Path:
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
                        **extra,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return registry_path


def _install_fake_model(monkeypatch, rows):
    from app.core import runtime
    from app.core.detector import UltralyticsDetector
    from tests.conftest import FakeModel

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
    return fake_model


def test_detect_runs_end_to_end_and_reports_real_scores(tmp_path, monkeypatch, png_bytes):
    """Upload -> Analyse -> boxes, count and confidence scores, using a fake model."""
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"stub")
    registry_path = _write_single_model_registry(tmp_path, weights)
    monkeypatch.setenv(config.ENV_REGISTRY_PATH, str(registry_path))
    _install_fake_model(monkeypatch, [(40, 30, 160, 150, 0.91, 0), (180, 60, 290, 200, 0.62, 0)])

    at = _run_page(tmp_path, "detect")
    at.file_uploader[0].upload("sample.png", png_bytes, "image/png").run()
    assert not at.exception, at.exception

    # Nothing is analysed until the user asks for it.
    labels = [button.label for button in at.button]
    assert "Analyse image" in labels
    assert not at.metric

    at.button[0].click().run()
    assert not at.exception, at.exception

    result = at.session_state["detect_analysis"]["outcome"].result
    assert readout_fields(result) == [
        ("Detections", "2"),
        ("Mean confidence", "76.5%"),  # (0.91 + 0.62) / 2
        ("Confidence range", "62.0% – 91.0%"),
        ("Threshold", "0.25"),
        ("Overlap", "0.45"),
    ]

    # The same values are on screen, in the fixed-column readout.
    text = _page_text(at)
    for label, value in readout_fields(result):
        assert label in text and value in text

    # Preview, original and annotated images are all displayed.
    assert len(at.get("image")) == 3
    assert len(at.get("download_button")) == 1

    # Coordinates and timings stay in the collapsed detail section.
    assert "Detection details" in [expander.label for expander in at.expander]

    recorded = at.session_state.get("detection_runs")
    assert recorded and recorded[0]["face_count"] == 2
    assert recorded[0]["labels"] == ["judah"]


def test_detect_fabricates_nothing_when_analysis_is_unavailable(tmp_path, png_bytes):
    """The critical honesty test: an upload with no model yields no boxes."""
    at = _run_page(tmp_path, "detect")
    at.file_uploader[0].upload("sample.png", png_bytes, "image/png").run()
    at.button[0].click().run()
    assert not at.exception, at.exception

    text = _page_text(at)
    assert "Image analysis is temporarily unavailable" in text
    # No readout at all: nothing to count, nothing to score.
    assert "Detections" not in text
    assert "Mean confidence" not in text

    # The cause is preserved for developers, not shown to the user.
    for term in TECHNICAL_TERMS:
        assert term not in _interactive_text(at), f"'{term}' leaked into the failure state"
    error = at.session_state.get("last_analysis_error")
    assert error and error["unavailable"] is True
    assert "weights" in error["message"].lower()

    assert not at.session_state.get("detection_runs")
    assert len(at.get("download_button")) == 0
    assert len(at.get("image")) == 1  # the user's own preview only


# --------------------------------------------------------------------------
# Camera
# --------------------------------------------------------------------------
def test_camera_offers_snapshot_capture_only(tmp_path):
    """One frame per capture, stated once, with no settings competing for attention."""
    at = _run_page(tmp_path, "camera")
    assert len(at.camera_input) == 1
    text = _page_text(at)
    assert "One still frame per capture. Live video is not analysed." in text
    # The collapsed settings panel appears only once there is something to analyse.
    assert len(at.get("expander")) == 0


def test_camera_has_no_technical_detail(tmp_path):
    at = _run_page(tmp_path, "camera")
    text = _interactive_text(at)
    for term in TECHNICAL_TERMS:
        assert term not in text, f"'{term}' appears on the Camera page"


# --------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------
def test_help_explains_the_three_step_workflow(tmp_path):
    at = _run_page(tmp_path, "help")
    text = _page_text(at)
    for step in ("Upload or capture", "Analyse", "Review and download"):
        assert step in text


def test_help_states_detection_is_not_recognition(tmp_path):
    at = _run_page(tmp_path, "help")
    assert "Detection is not recognition" in _page_text(at)


def test_help_documents_honest_limitations(tmp_path):
    text = _page_text(_run_page(tmp_path, "help")).lower()
    assert "subject-specific" in text
    assert "not a validated general-purpose face detector" in text
    assert "not an face-recognition" not in text
    assert "not a face-recognition system" in text


def test_help_mentions_privacy(tmp_path):
    text = _page_text(_run_page(tmp_path, "help")).lower()
    assert "not stored" in text


# --------------------------------------------------------------------------
# Developer page
# --------------------------------------------------------------------------
def test_developer_page_says_it_is_not_access_controlled(tmp_path):
    at = _run_page(tmp_path, "dev")
    text = (_page_text(at) + _texts(at.caption)).lower()
    assert "not protected by it" in text
    assert "anyone with the url" in text


def test_developer_page_holds_the_technical_detail_removed_from_the_product(tmp_path):
    at = _run_page(tmp_path, "dev")
    text = _page_text(at).lower()
    assert "weights path" in text
    assert "runtime" in text
    assert "session activity" in text


def test_developer_page_shows_the_last_analysis_error(tmp_path):
    at = _run_page(tmp_path, "dev")
    at.session_state["last_analysis_error"] = {
        "at": "2026-11-03T10:00:00+00:00",
        "source": "upload",
        "title": "Model weights are not available",
        "message": "No weights file was found at 'models/judah-face-v1/best.pt'.",
        "unavailable": True,
    }
    at.run()
    text = _page_text(at) + _texts(at.code)
    assert "Last analysis error" in text
    assert "No weights file was found" in text


def test_developer_page_shows_no_metrics_when_none_are_recorded(tmp_path):
    at = _run_page(tmp_path, "dev")
    assert "No evaluation metrics recorded" in _page_text(at)
    labels = [metric.label for metric in at.metric]
    assert "mAP@0.5" not in labels
    assert "Precision" not in labels


def test_developer_page_displays_recorded_metrics_verbatim(tmp_path, monkeypatch):
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
    registry_path = _write_single_model_registry(
        tmp_path, weights, metrics_file=str(metrics_path)
    )
    monkeypatch.setenv(config.ENV_REGISTRY_PATH, str(registry_path))

    at = _run_page(tmp_path, "dev")
    assert not at.exception, at.exception
    values = {metric.label: metric.value for metric in at.metric}
    assert values["mAP@0.5"] == "0.8340"
    assert values["Precision"] == "0.8100"
    assert values["Recall"] == "0.7900"


def test_developer_page_flags_an_invalid_metrics_record(tmp_path, monkeypatch):
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"stub")
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"model_id": "fixture-model", "metrics": {"mAP50": 91.4}}), encoding="utf-8"
    )
    registry_path = _write_single_model_registry(
        tmp_path, weights, metrics_file=str(metrics_path)
    )
    monkeypatch.setenv(config.ENV_REGISTRY_PATH, str(registry_path))

    at = _run_page(tmp_path, "dev")
    assert "metrics record is invalid" in _texts(at.error).lower()


def test_developer_page_summarises_session_activity(tmp_path):
    at = _run_page(tmp_path, "dev")
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
# No academic details anywhere
# --------------------------------------------------------------------------
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

    for page in ("home", "detect", "camera", "help", "dev"):
        at = _run_page(tmp_path, page)
        page_rendered = _page_text(at) + _texts(at.sidebar.markdown)
        assert academic_detail not in page_rendered, f"{academic_detail} leaked into {page}"
