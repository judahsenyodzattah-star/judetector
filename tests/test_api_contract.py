"""Transport-level contract: OpenAPI, error documents, docs exposure, CORS."""

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


def _client(registry_path: Path | None = None, **settings) -> TestClient:
    settings.setdefault("environment", "test")
    return TestClient(
        create_app(Settings(registry_path=registry_path, **settings)),
        raise_server_exceptions=False,
    )


def test_openapi_publishes_exactly_the_contract(api_registry):
    schema = _client(api_registry()).get("/openapi.json").json()
    assert schema["info"]["title"] == "JUDEtector API"
    assert set(schema["paths"]) == {"/v1/health", "/v1/model"}
    assert {"HealthResponse", "ModelCard", "ModelStatus", "Problem"} <= set(
        schema["components"]["schemas"]
    )


def test_openapi_leaks_no_configuration(api_registry, tmp_path):
    body = _client(api_registry(weights=True)).get("/openapi.json").text
    assert str(tmp_path) not in body
    assert "best.pt" not in body


def test_unknown_route_returns_a_problem_document():
    response = _client().get("/v1/nope")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "not_found"
    assert body["status"] == 404
    assert body["request_id"]


def test_wrong_method_returns_a_problem_document():
    response = _client().post("/v1/health")
    assert response.status_code == 405
    assert response.json()["type"] == "method_not_allowed"


def test_invalid_parameters_return_a_problem_document():
    app = create_app(Settings(environment="test"))

    @app.get("/_test/validation")
    def _needs_an_int(value: int) -> dict[str, int]:
        return {"value": value}

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/validation")
    assert response.status_code == 422
    body = response.json()
    assert body["type"] == "invalid_request"
    assert "value" in body["detail"]


def test_unexpected_failures_are_masked():
    app = create_app(Settings(environment="test"))

    @app.get("/_test/boom")
    def _boom() -> None:
        raise RuntimeError("secret internal detail at /private/path")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/boom")
    assert response.status_code == 500
    body = response.json()
    assert body["type"] == "internal_error"
    assert "secret internal detail" not in response.text
    assert "/private/path" not in response.text
    assert body["request_id"]


def test_docs_are_withheld_in_production(api_registry):
    client = _client(api_registry(), environment="production")
    assert client.get("/docs").status_code == 404
    # The contract itself is always available to clients.
    assert client.get("/openapi.json").status_code == 200


def test_cors_is_closed_unless_origins_are_allowlisted(api_registry):
    closed = _client(api_registry())
    assert "access-control-allow-origin" not in closed.get(
        "/v1/health", headers={"Origin": "https://example.test"}
    ).headers

    open_client = _client(api_registry(), allowed_origins=("https://example.test",))
    response = open_client.get("/v1/health", headers={"Origin": "https://example.test"})
    assert response.headers["access-control-allow-origin"] == "https://example.test"


def test_cors_does_not_allow_arbitrary_origins(api_registry):
    client = _client(api_registry(), allowed_origins=("https://example.test",))
    response = client.get("/v1/health", headers={"Origin": "https://evil.test"})
    assert response.headers.get("access-control-allow-origin") != "https://evil.test"
