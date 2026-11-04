"""Cross-origin behaviour for a browser deployment.

The approved production transport sends `POST /v1/detect` straight from the
Vercel-hosted frontend to Cloud Run. That makes three things contractual:

1. a simple multipart POST needs no preflight;
2. every response a browser must *read* — including 413/415/422/429/503 —
   carries the CORS headers, or the error becomes an opaque failure;
3. CORS is a browser rule, not authorisation: it stops other pages reading
   responses, and nothing else.
"""

from __future__ import annotations

import pytest

from tests.api_support import install_fake_model, make_client, png_bytes, post_image

pytestmark = pytest.mark.api

WEB_ORIGIN = "https://judetector.example"
OTHER_ORIGIN = "https://not-allowed.example"


@pytest.fixture(autouse=True)
def _fake_model(monkeypatch):
    install_fake_model(monkeypatch)
    yield


def _client(api_registry, *, weights: bool = True, **settings):
    settings.setdefault("allowed_origins", (WEB_ORIGIN,))
    return make_client(api_registry(weights=weights), **settings)


def test_a_simple_multipart_post_needs_no_preflight(api_registry):
    """FormData only sets a safelisted content type, so the browser sends one request."""
    response = post_image(
        _client(api_registry), png_bytes(), headers={"origin": WEB_ORIGIN}
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == WEB_ORIGIN
    assert "access-control-allow-credentials" not in response.headers


def test_preflight_is_answered_for_the_detect_route(api_registry):
    response = _client(api_registry).options(
        "/v1/detect",
        headers={
            "origin": WEB_ORIGIN,
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == WEB_ORIGIN
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert response.headers["access-control-max-age"] == "600"


def test_preflight_refuses_headers_that_were_not_allowed(api_registry):
    """Adding an auth header later is a deliberate configuration change, not a silent pass."""
    response = _client(api_registry).options(
        "/v1/detect",
        headers={
            "origin": WEB_ORIGIN,
            "access-control-request-method": "POST",
            "access-control-request-headers": "authorization",
        },
    )

    # Starlette answers 400 and advertises only the configured header list, so
    # the browser blocks the request. Adding an auth header later is therefore a
    # deliberate change to `allow_headers`, not something a client can ask for.
    assert response.status_code == 400
    allowed = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" not in allowed


@pytest.mark.parametrize(
    ("name", "build"),
    [
        ("unsupported_media_type", "gif"),
        ("invalid_image", "corrupt"),
        ("payload_too_large", "oversized"),
        ("model_unavailable", "no_weights"),
        ("rate_limited", "limited"),
    ],
)
def test_browsers_can_read_every_error_response(api_registry, name: str, build: str):
    if build == "no_weights":
        client = _client(api_registry, weights=False)
        response = post_image(client, png_bytes(), headers={"origin": WEB_ORIGIN})
    elif build == "limited":
        client = _client(api_registry, rate_limit_per_minute=1)
        first = post_image(client, png_bytes(), headers={"origin": WEB_ORIGIN})
        assert first.status_code == 200
        response = post_image(client, png_bytes(), headers={"origin": WEB_ORIGIN})
    elif build == "gif":
        response = post_image(
            _client(api_registry),
            b"GIF89a" + b"\x00" * 64,
            filename="picture.gif",
            headers={"origin": WEB_ORIGIN},
        )
    elif build == "corrupt":
        response = post_image(
            _client(api_registry), b"not an image", headers={"origin": WEB_ORIGIN}
        )
    else:
        response = _client(api_registry).post(
            "/v1/detect",
            content=b"x",
            headers={
                "origin": WEB_ORIGIN,
                "content-length": "999999999",
                "content-type": "multipart/form-data",
            },
        )

    assert response.status_code in {413, 415, 422, 429, 503}
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["access-control-allow-origin"] == WEB_ORIGIN
    exposed = {
        header.strip().lower()
        for header in response.headers["access-control-expose-headers"].split(",")
    }
    assert {"ratelimit-limit", "ratelimit-remaining", "retry-after"} <= exposed


def test_an_unlisted_origin_is_not_granted_access(api_registry):
    response = post_image(
        _client(api_registry), png_bytes(), headers={"origin": OTHER_ORIGIN}
    )

    assert "access-control-allow-origin" not in response.headers


def test_cors_is_not_authorisation(api_registry):
    """A client that is not a browser is served: CORS never protected the endpoint."""
    response = post_image(_client(api_registry), png_bytes())

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_a_25_mb_upload_fits_the_documented_request_ceiling(api_registry):
    """The size the browser will send must be inside what the API will accept."""
    from api.settings import Settings

    settings = Settings()
    largest_client_request = settings.max_upload_bytes + settings.multipart_overhead_bytes
    assert largest_client_request <= 32 * 1024 * 1024  # Cloud Run HTTP/1 request limit
    assert settings.max_upload_bytes == 25 * 1024 * 1024
