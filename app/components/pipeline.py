"""Detection pipeline shared by the Detect and Camera pages.

Deliberately free of Streamlit calls: it takes an image + detector and returns a
plain outcome object. That keeps the error-handling paths unit-testable and
guarantees the UI cannot accidentally render a detection that did not happen.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from app.core.detector import DetectionResult, Detector
from app.core.errors import JudetectorError, ModelUnavailableError
from app.core.registry import ModelSpec
from app.core.rendering import draw_detections

__all__ = ["AnalysisOutcome", "analyse_image"]


@dataclass(frozen=True)
class AnalysisOutcome:
    """Result of one analysis attempt."""

    ok: bool
    result: DetectionResult | None = None
    processed: Image.Image | None = None
    error_title: str | None = None
    error_message: str | None = None
    unavailable: bool = False

    @property
    def count(self) -> int:
        return self.result.count if self.result else 0


def analyse_image(
    image: Image.Image,
    spec: ModelSpec,
    detector: Detector,
    *,
    confidence: float,
    iou: float,
) -> AnalysisOutcome:
    """Load the model if needed, run inference, and draw the boxes.

    Never fabricates output: any failure yields ``ok=False`` with a message that
    explains exactly what is wrong.
    """
    if not detector.is_available():
        return AnalysisOutcome(
            ok=False,
            unavailable=True,
            error_title="Model weights are not available",
            error_message=(
                f"No weights file was found at '{spec.weights_path}'. "
                "JUDEtector will not display detections it cannot produce."
            ),
        )

    try:
        detector.load()
    except ModelUnavailableError as exc:
        return AnalysisOutcome(
            ok=False,
            unavailable=True,
            error_title="Model could not be loaded",
            error_message=str(exc),
        )
    except JudetectorError as exc:
        return AnalysisOutcome(
            ok=False,
            error_title="Model could not be loaded",
            error_message=str(exc),
        )

    try:
        result = detector.predict(image, confidence=confidence, iou=iou)
    except JudetectorError as exc:
        return AnalysisOutcome(
            ok=False,
            error_title="Detection failed",
            error_message=str(exc),
        )
    except Exception as exc:  # noqa: BLE001 - last-resort guard for the UI
        return AnalysisOutcome(
            ok=False,
            error_title="Detection failed unexpectedly",
            error_message=f"{type(exc).__name__}: {exc}",
        )

    processed = draw_detections(image, result.detections)
    return AnalysisOutcome(ok=True, result=result, processed=processed)
