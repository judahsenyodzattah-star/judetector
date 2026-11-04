"""Detection contract.

One request produces exactly one set of measurements. Every field either comes
from `DetectionResult` (produced by the unchanged pipeline) or from a timer
measured around the call; nothing is estimated, defaulted or back-filled.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "AnnotatedImage",
    "Box",
    "DetectResponse",
    "DetectionOut",
    "ImageInfo",
    "ModelRef",
    "Thresholds",
    "Timing",
]


class Box(BaseModel):
    """An axis-aligned box in pixels of the analysed image."""

    x1: float
    y1: float
    x2: float
    y2: float


class DetectionOut(BaseModel):
    """One detection, in the model's order, with both coordinate spaces."""

    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    box: Box = Field(description="Pixel coordinates in the analysed image.")
    box_norm: Box = Field(
        description="The same box normalised to [0, 1], for overlays at any rendered size."
    )


class Thresholds(BaseModel):
    """The thresholds actually applied to this inference pass."""

    confidence: float
    iou: float


class ImageInfo(BaseModel):
    """What was analysed, and what the client sent."""

    width: int = Field(description="Analysed width in pixels.")
    height: int = Field(description="Analysed height in pixels.")
    source_width: int = Field(description="Width as uploaded, before any downscale.")
    source_height: int = Field(description="Height as uploaded, before any downscale.")
    downscaled: bool = Field(description="True when the image was reduced before analysis.")
    bytes: int = Field(description="Upload size in bytes.")
    megapixels: float = Field(description="Analysed megapixels.")


class Timing(BaseModel):
    """Measured durations. `null` means not measured, never zero-as-placeholder."""

    inference_ms: float | None = Field(
        default=None, description="Detector time, measured inside the engine."
    )
    total_ms: float | None = Field(
        default=None,
        description=(
            "Server time for decode, inference and annotation rendering. Excludes upload "
            "transfer and response encoding."
        ),
    )


class ModelRef(BaseModel):
    """Which model produced this result, and what it is."""

    id: str
    display_name: str
    kind: str
    labels: list[str]
    labels_source: str


class AnnotatedImage(BaseModel):
    """The annotated PNG, inline. Nothing is stored server-side."""

    mime: str = "image/png"
    encoding: str = "base64"
    width: int
    height: int
    bytes: int = Field(description="Encoded PNG size in bytes, before base64 expansion.")
    data: str


class DetectResponse(BaseModel):
    """The result of one detection request."""

    request_id: str
    model: ModelRef
    image: ImageInfo
    thresholds: Thresholds
    count: int = Field(description="Number of detections. Equals len(detections).")
    detections: list[DetectionOut]
    timing: Timing
    annotated: AnnotatedImage | None = None
    warnings: list[str] = Field(
        default_factory=list,
        description="Honest notes about this response, e.g. an omitted annotation for size.",
    )
