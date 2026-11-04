"""FastAPI application factory for the JUDEtector inference service.

Stage 0 exposes the service contract only: `/v1/health` and `/v1/model`.
`/v1/detect` arrives in Stage 1 and reuses `app/components/pipeline.py`
unchanged.

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
from api.errors import install_error_handlers, install_http_middleware
from api.routes import health, model
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

    install_http_middleware(app)
    install_error_handlers(app)

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
    return app


app = create_app()
