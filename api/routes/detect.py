"""`POST /v1/detect` — one image in, one measured result out."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, Request, Response, UploadFile

from api.errors import ProblemError, request_id_of
from api.schemas import DetectResponse, Problem
from api.services import detector_for, resolve_model
from api.services.detect_service import run_detection
from api.settings import Settings
from api.validation import read_upload

__all__ = ["router"]

router = APIRouter(prefix="/v1", tags=["detection"])

_PROBLEM = {"model": Problem, "content": {"application/problem+json": {}}}

_RESPONSES = {
    413: {**_PROBLEM, "description": "Upload or decoded image is too large."},
    415: {**_PROBLEM, "description": "The detected image format is not supported."},
    422: {**_PROBLEM, "description": "The image could not be decoded."},
    429: {**_PROBLEM, "description": "Per-instance rate limit exceeded."},
    500: {**_PROBLEM, "description": "The model failed during inference."},
    503: {**_PROBLEM, "description": "No usable model is available."},
}


@router.post(
    "/detect",
    response_model=DetectResponse,
    summary="Analyse one image",
    responses=_RESPONSES,
    description=(
        "Run the configured detector over one uploaded image. Inference happens only "
        "for this request: nothing is analysed automatically and nothing is stored. "
        "Returns pixel and normalised boxes, the applied thresholds, measured timings "
        "and, unless omitted for size, the annotated PNG inline."
    ),
)
async def detect(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(description="JPG, PNG, WEBP or BMP")],
    confidence: Annotated[float, Form(ge=0.01, le=0.99)] = 0.25,
    iou: Annotated[float, Form(ge=0.10, le=0.95)] = 0.45,
    include_annotated: Annotated[bool, Form()] = True,
) -> DetectResponse:
    # Rate limiting is applied by `RateLimitMiddleware`, before the upload is
    # parsed, so its headers survive every exit path including errors.
    settings: Settings = request.app.state.settings
    resolved = resolve_model(settings)
    if resolved.spec is None:
        raise ProblemError(
            status=503,
            type_="model_unavailable",
            title="No model is available",
            detail="This service has no usable model configured. Try again later.",
        )

    data = await read_upload(file, settings)
    outcome = run_detection(
        data=data,
        settings=settings,
        spec=resolved.spec,
        detector=detector_for(resolved.spec),
        confidence=float(confidence),
        iou=float(iou),
        include_annotated=bool(include_annotated),
        request_id=request_id_of(request),
    )

    if outcome.server_timing:
        response.headers["Server-Timing"] = outcome.server_timing
    return outcome.response
