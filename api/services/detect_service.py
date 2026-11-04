"""Detection orchestration.

This module is deliberately thin. It validates the upload, calls the **existing**
`analyse_image` pipeline unchanged, and maps the outcome onto the published
contract. No inference logic lives here: if the engine changes, the API changes
with it, and the parity test fails if the two ever diverge.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass

from api.errors import ProblemError
from api.schemas import (
    AnnotatedImage,
    Box,
    DetectionOut,
    DetectResponse,
    ImageInfo,
    ModelRef,
    Thresholds,
    Timing,
)
from api.settings import Settings
from api.validation import ValidatedImage, validate_image
from app.components.pipeline import analyse_image
from app.core.detector import Detection, Detector
from app.core.image_io import to_png_bytes
from app.core.registry import ModelSpec

__all__ = ["DetectionOutcome", "run_detection"]


@dataclass(frozen=True)
class DetectionOutcome:
    """The response plus the values that belong in headers."""

    response: DetectResponse
    server_timing: str | None


def run_detection(
    *,
    data: bytes,
    settings: Settings,
    spec: ModelSpec,
    detector: Detector,
    confidence: float,
    iou: float,
    include_annotated: bool,
    request_id: str,
) -> DetectionOutcome:
    """Validate, analyse and serialise one image."""
    started = time.perf_counter()
    validated = validate_image(data, settings)

    outcome = analyse_image(validated.image, spec, detector, confidence=confidence, iou=iou)

    if not outcome.ok or outcome.result is None:
        # A model that is not ready could not be loaded: the service is
        # unavailable (503). A ready model that still failed broke during
        # inference (500). `is_ready()` is the engine's own signal, so this
        # mapping needs no new fields in the pipeline.
        if outcome.unavailable or not detector.is_ready():
            # Honest unavailability: no detections, no placeholder confidence.
            raise ProblemError(
                status=503,
                type_="model_unavailable",
                title="Analysis is unavailable",
                detail=(
                    "This service cannot run the configured model right now. "
                    "Try again later."
                ),
            )
        raise ProblemError(
            status=500,
            type_="inference_failed",
            title="Analysis failed",
            detail="The model could not complete this request. Try again later.",
        )

    result = outcome.result
    annotated, warnings = _annotated(outcome.processed, settings, include_annotated)
    total_ms = (time.perf_counter() - started) * 1000.0

    response = DetectResponse(
        request_id=request_id,
        model=ModelRef(
            id=spec.id,
            display_name=spec.display_name,
            kind=spec.kind,
            labels=list(result.labels_present),
            labels_source=detector.labels_source,
        ),
        image=_image_info(validated),
        thresholds=Thresholds(confidence=confidence, iou=iou),
        count=result.count,
        detections=[
            _detection_out(detection, validated.image.width, validated.image.height)
            for detection in result.detections
        ],
        timing=Timing(
            inference_ms=result.inference_ms if result.inference_ms > 0 else None,
            total_ms=total_ms if total_ms > 0 else None,
        ),
        annotated=annotated,
        warnings=warnings,
    )
    return DetectionOutcome(response=response, server_timing=_server_timing(response.timing))


def _image_info(validated: ValidatedImage) -> ImageInfo:
    width, height = validated.image.size
    return ImageInfo(
        width=width,
        height=height,
        source_width=validated.source_width,
        source_height=validated.source_height,
        downscaled=validated.downscaled,
        bytes=len(validated.data),
        megapixels=round(width * height / 1_000_000, 3),
    )


def _detection_out(detection: Detection, width: int, height: int) -> DetectionOut:
    x1, y1, x2, y2 = detection.box_xyxy

    def norm(value: float, extent: int) -> float:
        if extent <= 0:
            return 0.0
        return round(min(1.0, max(0.0, value / extent)), 6)

    return DetectionOut(
        label=detection.label,
        confidence=round(float(detection.confidence), 4),
        box=Box(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2)),
        box_norm=Box(
            x1=norm(x1, width),
            y1=norm(y1, height),
            x2=norm(x2, width),
            y2=norm(y2, height),
        ),
    )


def _annotated(
    processed,  # noqa: ANN001 - PIL image from the pipeline, typed by usage
    settings: Settings,
    include_annotated: bool,
) -> tuple[AnnotatedImage | None, list[str]]:
    """Encode the annotated PNG inline, refusing to blow up the response."""
    if not include_annotated or processed is None:
        return None, []

    png = to_png_bytes(processed)
    if len(png) > settings.max_annotated_bytes:
        limit_mb = settings.max_annotated_bytes / (1024 * 1024)
        return None, [
            (
                f"Annotated image omitted: the PNG is {len(png) / (1024 * 1024):.1f} MB, "
                f"above the {limit_mb:.1f} MB response limit. Send "
                "include_annotated=false or a smaller image."
            )
        ]

    return (
        AnnotatedImage(
            width=processed.width,
            height=processed.height,
            bytes=len(png),
            data=base64.b64encode(png).decode("ascii"),
        ),
        [],
    )


def _server_timing(timing: Timing) -> str | None:
    parts: list[str] = []
    if timing.inference_ms is not None:
        parts.append(f"inference;dur={timing.inference_ms:.1f}")
    if timing.total_ms is not None:
        parts.append(f"total;dur={timing.total_ms:.1f}")
    return ", ".join(parts) if parts else None
