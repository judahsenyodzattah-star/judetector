"""Rate-limit behaviour, and the honesty of what it claims."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.rate_limit import InProcessRateLimiter, NoRateLimit, build_limiter, client_key
from api.runtime import clear_caches
from api.settings import Settings
from tests.api_support import install_fake_model, make_client, png_bytes, post_image

pytestmark = pytest.mark.api

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    clear_caches()
    install_fake_model(monkeypatch)
    yield
    clear_caches()


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_limiter_allows_then_blocks_within_the_window():
    clock = FakeClock()
    limiter = InProcessRateLimiter(limit=2, window_s=60, clock=clock)

    first = limiter.check("1.2.3.4")
    second = limiter.check("1.2.3.4")
    third = limiter.check("1.2.3.4")

    assert first.allowed and first.remaining == 1
    assert second.allowed and second.remaining == 0
    assert not third.allowed
    assert third.reset_after_s == pytest.approx(60.0)


def test_limiter_recovers_after_the_window():
    clock = FakeClock()
    limiter = InProcessRateLimiter(limit=1, window_s=30, clock=clock)
    assert limiter.check("k").allowed
    assert not limiter.check("k").allowed
    clock.advance(31)
    assert limiter.check("k").allowed


def test_limits_are_per_key():
    limiter = InProcessRateLimiter(limit=1, window_s=60, clock=FakeClock())
    assert limiter.check("a").allowed
    assert not limiter.check("a").allowed
    assert limiter.check("b").allowed


def test_backend_none_disables_limiting():
    settings = Settings(rate_limit_backend="none")
    limiter = build_limiter(settings)
    assert isinstance(limiter, NoRateLimit)
    for _ in range(50):
        assert limiter.check("any").allowed


def test_api_returns_429_with_problem_document(api_registry):
    client = make_client(api_registry(weights=True), rate_limit_per_minute=2)
    assert post_image(client, png_bytes()).status_code == 200
    assert post_image(client, png_bytes()).status_code == 200

    response = post_image(client, png_bytes())
    assert response.status_code == 429
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "rate_limited"
    assert body["request_id"]
    assert int(response.headers["retry-after"]) >= 1
    assert response.headers["ratelimit-limit"] == "2"
    assert response.headers["ratelimit-remaining"] == "0"
    assert response.headers["ratelimit-scope"] == "instance"


def test_rate_headers_appear_on_success(api_registry):
    client = make_client(api_registry(weights=True), rate_limit_per_minute=5)
    response = post_image(client, png_bytes())
    assert response.headers["ratelimit-limit"] == "5"
    assert response.headers["ratelimit-remaining"] == "4"
    assert response.headers["ratelimit-scope"] == "instance"


def test_health_is_never_rate_limited(api_registry):
    client = make_client(api_registry(weights=True), rate_limit_per_minute=1)
    for _ in range(5):
        assert client.get("/v1/health").status_code == 200


def test_client_key_ignores_forwarded_header_unless_trusted():
    untrusted = Settings(trust_proxy=False)
    assert client_key(untrusted, "10.0.0.1", "203.0.113.9") == "10.0.0.1"

    trusted = Settings(trust_proxy=True)
    assert client_key(trusted, "10.0.0.1", "203.0.113.9, 10.0.0.2") == "203.0.113.9"
    assert client_key(trusted, "10.0.0.1", None) == "10.0.0.1"


def test_documentation_does_not_claim_global_protection():
    """Per-instance limits must be described as per-instance, with the edge named."""
    docs = (PROJECT_ROOT / "docs" / "API.md").read_text(encoding="utf-8").lower()
    assert "per instance" in docs or "per-instance" in docs
    assert "edge" in docs
    assert "cloud armor" in docs
    assert "redis" in docs


def test_quota_headers_survive_error_paths(api_registry):
    """A 503 or a 413 must still say where the quota stands."""
    client = make_client(api_registry(weights=False), rate_limit_per_minute=10)

    unavailable = post_image(client, png_bytes())
    assert unavailable.status_code == 503
    assert unavailable.headers["ratelimit-limit"] == "10"
    assert unavailable.headers["ratelimit-remaining"] == "9"
    assert unavailable.headers["ratelimit-scope"] == "instance"

    oversized = client.post(
        "/v1/detect",
        content=b"x",
        headers={"content-length": "999999999", "content-type": "multipart/form-data"},
    )
    assert oversized.status_code == 413
    assert oversized.headers["ratelimit-remaining"] == "8"


def test_rejected_requests_are_limited_before_the_body_is_read(api_registry):
    """The 429 wins over parsing, so an over-quota caller cannot upload at all."""
    client = make_client(api_registry(weights=True), rate_limit_per_minute=1)
    assert post_image(client, png_bytes()).status_code == 200

    response = client.post(
        "/v1/detect",
        content=b"y" * 1024,
        headers={"content-length": "999999999", "content-type": "multipart/form-data"},
    )
    assert response.status_code == 429
    assert response.headers["retry-after"]


def test_scope_none_when_the_edge_limits_instead(api_registry):
    client = make_client(api_registry(weights=True), rate_limit_backend="none")
    for _ in range(5):
        response = post_image(client, png_bytes())
        assert response.status_code == 200
        assert response.headers["ratelimit-scope"] == "none"
        assert "ratelimit-limit" not in response.headers
