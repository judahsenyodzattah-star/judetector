"""Problem documents, request ids and response hardening.

Every error leaves the service as `application/problem+json` with a stable
`type`, a human `title`, a `detail` that contains no internals, the HTTP
`status` and the `request_id` an operator can correlate with the server log.
"""

from __future__ import annotations

import logging
import re
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.schemas.errors import PROBLEM_MEDIA_TYPE, Problem

__all__ = [
    "ProblemError",
    "REQUEST_ID_HEADER",
    "install_error_handlers",
    "install_http_middleware",
    "problem_response",
]

logger = logging.getLogger("judetector.api")

REQUEST_ID_HEADER = "X-Request-Id"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class ProblemError(Exception):
    """Raise anywhere in a route to produce a problem document."""

    def __init__(
        self,
        status: int,
        type_: str,
        title: str,
        detail: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(title)
        self.status = status
        self.type = type_
        self.title = title
        self.detail = detail
        self.headers = headers or {}


def request_id_of(request: Request) -> str:
    """The request's id, generating one if the caller did not send a valid id."""
    existing = getattr(request.state, "request_id", None)
    if isinstance(existing, str) and existing:
        return existing
    generated = uuid.uuid4().hex
    request.state.request_id = generated
    return generated


def problem_response(
    request: Request,
    *,
    status: int,
    type_: str,
    title: str,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = request_id_of(request)
    body = Problem(
        type=type_,
        title=title,
        status=status,
        detail=detail,
        request_id=request_id,
    )
    merged = {
        "X-Request-Id": request_id,
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    if headers:
        merged.update(headers)
    return JSONResponse(
        status_code=status,
        content=body.model_dump(),
        media_type=PROBLEM_MEDIA_TYPE,
        headers=merged,
    )


def install_body_size_guard(app: FastAPI) -> None:
    """Reject oversized bodies from `Content-Length`, before they are read.

    The per-upload cap is also enforced while streaming; this guard simply stops a
    large request at the edge of the process instead of buffering it first.
    """
    settings = app.state.settings

    @app.middleware("http")
    async def _body_size_guard(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            raw = request.headers.get("content-length", "")
            if raw.isdigit() and int(raw) > settings.max_request_bytes:
                return problem_response(
                    request,
                    status=413,
                    type_="payload_too_large",
                    title="Request is too large",
                    detail=(
                        f"Requests must be at most {settings.max_upload_mb} MB plus "
                        "multipart overhead."
                    ),
                )
        return await call_next(request)


def install_http_middleware(app: FastAPI) -> None:
    """Assign request ids and harden every response."""

    @app.middleware("http")
    async def _request_context(request: Request, call_next):
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request.state.request_id = (
            incoming if _REQUEST_ID_PATTERN.match(incoming) else uuid.uuid4().hex
        )
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id_of(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem(request: Request, exc: ProblemError) -> JSONResponse:
        return problem_response(
            request,
            status=exc.status,
            type_=exc.type,
            title=exc.title,
            detail=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        titles = {404: "Not found", 405: "Method not allowed", 413: "Payload too large"}
        types = {404: "not_found", 405: "method_not_allowed", 413: "payload_too_large"}
        return problem_response(
            request,
            status=exc.status_code,
            type_=types.get(exc.status_code, "http_error"),
            title=titles.get(exc.status_code, "Request failed"),
            detail=str(exc.detail) if exc.detail else "The request could not be completed.",
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = sorted(
            {".".join(str(part) for part in error.get("loc", ())) for error in exc.errors()}
        )
        where = f" Fields: {', '.join(fields)}." if fields else ""
        return problem_response(
            request,
            status=422,
            type_="invalid_request",
            title="Request parameters are invalid",
            detail=f"One or more request parameters are invalid.{where}",
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error while serving %s", request.url.path)
        return problem_response(
            request,
            status=500,
            type_="internal_error",
            title="The service could not complete the request",
            detail="An unexpected error occurred. Quote the request id when reporting it.",
        )
