"""Contract tests for `/v1/health`.

The health contract is where the service's honesty is visible: it must report a
degraded state whenever the model cannot actually run, and it must never leak a
filesystem path while doing so.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.runtime import clear_caches
from api.settings import Settings

pytestmark = pytest.mark.api

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean_caches():
    clear_caches()
    yield
    clear_caches()


def _client(registry_path: Path | None, *, environment: str = "test") -> TestClient:
    settings = Settings(environment=environment, registry_path=registry_path)
    return TestClient(create_app(settings), raise_server_exceptions=False)


def test_health_is_degraded_without_weights(api_registry):
    response = _client(api_registry(weights=False)).get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["model"] == {"id": "stub-model", "available": False, "loaded": False}
    assert body["service"] == "judetector-api"
    assert body["version"]
    assert body["uptime_s"] >= 0


def test_health_is_ok_when_weights_exist(api_registry):
    response = _client(api_registry(weights=True)).get("/v1/health")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["model"]["available"] is True
    # Nothing loads weights during a health check.
    assert body["model"]["loaded"] is False


def test_health_survives_a_missing_registry(tmp_path):
    response = _client(tmp_path / "missing.json").get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["model"] is None


def test_health_never_leaks_paths_or_dependency_names(api_registry, tmp_path):
    registry_path = api_registry(weights=True)
    body = _client(registry_path).get("/v1/health").text
    for leaked in ("tmp", "best.pt", "models.json", str(tmp_path), "torch", "ultralytics"):
        assert leaked not in body.lower(), f"health leaked {leaked!r}"


def test_request_id_is_generated_when_absent(api_registry):
    response = _client(api_registry()).get("/v1/health")
    assert len(response.headers["x-request-id"]) == 32


def test_request_id_is_echoed_when_well_formed(api_registry):
    response = _client(api_registry()).get(
        "/v1/health", headers={"X-Request-Id": "abc12345.test-id"}
    )
    assert response.headers["x-request-id"] == "abc12345.test-id"


def test_malformed_request_id_is_replaced(api_registry):
    response = _client(api_registry()).get("/v1/health", headers={"X-Request-Id": "<script>"})
    assert response.headers["x-request-id"] != "<script>"
    assert len(response.headers["x-request-id"]) == 32


def test_responses_are_never_cached(api_registry):
    response = _client(api_registry()).get("/v1/health")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_the_api_does_not_import_streamlit():
    """The service must not pull Streamlit into its process."""
    code = (
        "import sys; import api.main; "
        "assert 'streamlit' not in sys.modules, sorted(m for m in sys.modules if 'streamlit' in m)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
