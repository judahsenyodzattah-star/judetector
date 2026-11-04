"""FastAPI application factory for the JUDEtector inference service.

Endpoints: `/v1/health`, `/v1/model`, and `/v1/detect` — the last one reuses
`app/components/pipeline.py` unchanged, so the API cannot drift from the
Streamlit prototype.

Run locally:

    uvicorn api.main:app --reload --port 8000

Container entrypoint (Cloud Run sets `PORT`):

    uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
"""

from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import __version__
from api.errors import install_body_size_guard, install_error_handlers, install_http_middleware
from api.rate_limit import RateLimitMiddleware, build_limiter
from api.routes import detect, health, model
from api.settings import Settings

__all__ = ["app", "create_app"]

_DESCRIPTION = """
Inference API for JUDEtector.

The service wraps one trained detector and reports exactly what the model
produces: detection boxes, confidences and measured timings. When weights or the
ML stack are unavailable it says so — it never returns invented results.

Requests are processed in memory and nothing is stored; every response is
`Cache-Control: no-store`.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application. Tests inject explicit settings."""
    resolved_settings = settings or Settings.from_env()

    app = FastAPI(
        title="JUDEtector API",
        description=_DESCRIPTION,
        version=__version__,
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json",
        contact={"name": "JUDEtector"},
        license_info={"name": "Proprietary"},
    )
    app.state.settings = resolved_settings
    app.state.started_at = time.monotonic()
    app.state.rate_limiter = build_limiter(resolved_settings)

    install_http_middleware(app)
    install_body_size_guard(app)
    install_error_handlers(app)
    # Added last of these three so it wraps them: the quota headers and the 429
    # are produced even when the body guard or a route raises.
    app.add_middleware(
        RateLimitMiddleware,
        settings=resolved_settings,
        limiter=app.state.rate_limiter,
    )

    if resolved_settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "X-Request-Id"],
            expose_headers=["X-Request-Id", "Server-Timing"],
            max_age=600,
        )

    app.include_router(health.router)
    app.include_router(model.router)
    app.include_router(detect.router)
    return app


app = create_app()
