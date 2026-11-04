"""Contract tests for `/v1/model`.

The model card is the API's honesty surface: it carries the model's limitations
and either the recorded evaluation verbatim or nothing at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.runtime import clear_caches
from api.settings import Settings

pytestmark = pytest.mark.api


@pytest.fixture(autouse=True)
def _clean_caches():
    clear_caches()
    yield
    clear_caches()


def _client(registry_path: Path | None) -> TestClient:
    return TestClient(
        create_app(Settings(environment="test", registry_path=registry_path)),
        raise_server_exceptions=False,
    )


def test_card_states_what_the_model_is_not(api_registry):
    body = _client(api_registry()).get("/v1/model").json()
    assert body["id"] == "stub-model"
    assert body["kind"] == "subject_specific"
    assert body["task"] == "detect"
    assert body["labels"] == ["judah"]
    assert body["limitations"]
    lowered = body["limitations"].lower()
    assert "single-subject" in lowered
    assert "general-purpose face detector" in lowered
    assert "detection is not recognition" in lowered


def test_general_purpose_models_are_described_differently(api_registry):
    path = api_registry(kind="general_purpose", labels=("face",))
    body = _client(path).get("/v1/model").json()
    assert body["kind"] == "general_purpose"
    assert "single-subject" not in body["limitations"].lower()


def test_labels_are_declared_until_the_model_is_loaded(api_registry):
    body = _client(api_registry()).get("/v1/model").json()
    assert body["labels_source"] == "declared"
    assert body["available"] is False


def test_availability_reflects_the_weights_file(api_registry):
    body = _client(api_registry(weights=True)).get("/v1/model").json()
    assert body["available"] is True


def test_metrics_are_null_when_none_are_recorded(api_registry):
    body = _client(api_registry(weights=True)).get("/v1/model").json()
    assert body["metrics"] is None


def test_recorded_metrics_are_returned_verbatim(api_registry):
    metrics = {

        "model_id": "stub-model",
        "split": "test",
        "evaluated_on": "2026-11-01",
        "source": "held-out test split",
        "metrics": {"mAP50": 0.6123, "mAP50-95": 0.4123, "precision": 0.7, "recall": 0.6},
    }
    body = _client(api_registry(metrics=metrics)).get("/v1/model").json()
    assert body["metrics"]["metrics"] == {
        "mAP50": 0.6123,
        "mAP50_95": 0.4123,
        "precision": 0.7,
        "recall": 0.6,
    }
    assert body["metrics"]["split"] == "test"
    assert body["metrics"]["source"] == "held-out test split"


def test_invalid_metrics_are_withheld_rather_than_estimated(api_registry):
    metrics = {"model_id": "stub-model", "metrics": {"mAP50": 1.4}}  # out of range
    body = _client(api_registry(metrics=metrics)).get("/v1/model").json()
    assert body["metrics"] is None


def test_missing_registry_is_a_problem_document(tmp_path):
    response = _client(tmp_path / "missing.json").get("/v1/model")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "model_unavailable"
    assert body["detail"]
    assert body["request_id"]
    for leaked in ("tmp", "missing.json", "models.json", "config/", "torch", "best.pt"):
        assert leaked not in response.text.lower()


def test_card_contains_no_filesystem_paths(api_registry, tmp_path):
    response = _client(api_registry(weights=True)).get("/v1/model")
    for leaked in (str(tmp_path), "best.pt", "models.json"):
        assert leaked not in response.text
