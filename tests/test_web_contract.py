"""The web app's copied contract must match the API it talks to.

`web/tests/fixtures/*.json` are real responses captured from this API. The web
types are hand-written, so these tests fail if the API grows, renames or drops a
field without the frontend being updated with it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from api.main import create_app
from api.settings import Settings

pytestmark = pytest.mark.api

WEB = Path(__file__).resolve().parents[1] / "web"
FIXTURES = WEB / "tests" / "fixtures"


def _schema() -> dict:
    return create_app().openapi()["components"]["schemas"]


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("fixture_name", "schema_name"),
    [
        ("detect-response.json", "DetectResponse"),
        ("model-card.json", "ModelCard"),
        ("health.json", "HealthResponse"),
    ],
)
def test_fixture_matches_the_published_schema(fixture_name: str, schema_name: str) -> None:
    schema = _schema()[schema_name]
    published = set(schema["properties"])
    required = set(schema.get("required", ()))
    fixture = _fixture(fixture_name)

    assert set(fixture) <= published, f"{fixture_name} has fields the API does not publish"
    assert required <= set(fixture), f"{fixture_name} is missing required fields"


def test_nested_detection_shape_is_what_the_web_renders() -> None:
    body = _fixture("detect-response.json")
    schemas = _schema()

    assert set(body["model"]) == set(schemas["ModelRef"]["properties"])
    assert set(body["image"]) == set(schemas["ImageInfo"]["properties"])
    assert set(body["thresholds"]) == set(schemas["Thresholds"]["properties"])
    assert set(body["timing"]) == set(schemas["Timing"]["properties"])
    for detection in body["detections"]:
        assert set(detection) == set(schemas["DetectionOut"]["properties"])
        assert set(detection["box"]) == set(schemas["Box"]["properties"])
        assert set(detection["box_norm"]) == set(schemas["Box"]["properties"])


def test_fixture_boxes_stay_inside_the_normalised_range() -> None:
    for detection in _fixture("detect-response.json")["detections"]:
        for value in detection["box_norm"].values():
            assert 0.0 <= value <= 1.0


def test_web_upload_cap_matches_the_api_cap() -> None:
    source = (WEB / "lib" / "limits.ts").read_text(encoding="utf-8")
    match = re.search(r"MAX_UPLOAD_BYTES = (\d+) \* 1024 \* 1024", source)
    assert match, "the web upload cap must stay an explicit megabyte figure"

    megabytes = int(match.group(1))
    assert megabytes == Settings().max_upload_mb


def test_web_documents_the_host_limit_instead_of_lowering_the_api() -> None:
    docs = (Path(__file__).resolve().parents[1] / "docs" / "WEB.md").read_text(encoding="utf-8")
    lowered = docs.lower()
    assert "4.5 mb" in lowered
    assert "direct" in lowered
    assert "25 mb" in lowered
