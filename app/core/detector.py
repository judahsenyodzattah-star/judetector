"""Model-agnostic detection abstraction.

`Detector` is the seam that makes the application general-purpose: every view
talks to this interface, never to Ultralytics directly. Swapping in a different
face-detection model means registering new weights and, at most, adding another
`Detector` implementation -- no UI rewrite.

Design rules enforced here:
  * Nothing is fabricated. If weights are missing, `load()` raises
    `ModelUnavailableError`; if the model is not loaded, `predict()` raises.
    There is no code path that invents boxes.
  * Labels come from the *model itself* once loaded (`labels_source == "model"`).
    Declared labels are a config fallback and are explicitly flagged as such,
    so a subject-specific model is never silently presented as a face detector.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from app.core.errors import ModelLoadError, ModelUnavailableError

__all__ = [
    "Detection",
    "DetectionResult",
    "Detector",
    "UltralyticsDetector",
    "ModelLoader",
]


Box = tuple[float, float, float, float]
ModelLoader = Callable[[str], Any]


@dataclass(frozen=True)
class Detection:
    """A single detected object in pixel coordinates of the original image."""

    box_xyxy: Box
    confidence: float
    label: str

    @property
    def width(self) -> float:
        return max(0.0, self.box_xyxy[2] - self.box_xyxy[0])

    @property
    def height(self) -> float:
        return max(0.0, self.box_xyxy[3] - self.box_xyxy[1])

    def to_record(self) -> dict[str, Any]:
        """Flat record for display/export (confidence kept to 4 d.p.)."""
        x1, y1, x2, y2 = self.box_xyxy
        return {
            "label": self.label,
            "confidence": round(float(self.confidence), 4),
            "x1": round(float(x1), 1),
            "y1": round(float(y1), 1),
            "width": round(self.width, 1),
            "height": round(self.height, 1),
        }


@dataclass(frozen=True)
class DetectionResult:
    """Output of one inference pass. Immutable, so it is safe to cache/compare."""

    detections: tuple[Detection, ...] = ()
    model_id: str = ""
    image_width: int = 0
    image_height: int = 0
    confidence_threshold: float = 0.0
    iou_threshold: float = 0.0
    inference_ms: float = 0.0

    @property
    def count(self) -> int:
        return len(self.detections)

    @property
    def mean_confidence(self) -> float | None:
        if not self.detections:
            return None
        return sum(d.confidence for d in self.detections) / len(self.detections)

    @property
    def min_confidence(self) -> float | None:
        return min((d.confidence for d in self.detections), default=None)

    @property
    def max_confidence(self) -> float | None:
        return max((d.confidence for d in self.detections), default=None)

    @property
    def labels_present(self) -> tuple[str, ...]:
        return tuple(sorted({d.label for d in self.detections}))

    def records(self) -> list[dict[str, Any]]:
        return [d.to_record() for d in self.detections]


class Detector(ABC):
    """Interface every detection backend must satisfy."""

    model_id: str = ""
    display_name: str = ""
    weights_path: Path = Path()
    is_general_purpose: bool = False

    @property
    @abstractmethod
    def labels(self) -> tuple[str, ...]:
        """Class labels this detector will emit."""

    @property
    @abstractmethod
    def labels_source(self) -> str:
        """'model' when read from loaded weights, 'declared' when from config,
        'unknown' when neither is available."""

    @abstractmethod
    def is_available(self) -> bool:
        """True when the weights file exists on disk."""

    @abstractmethod
    def is_ready(self) -> bool:
        """True when the model is loaded into memory and can predict."""

    @abstractmethod
    def load(self) -> None:
        """Load weights. Idempotent. Raises ModelUnavailableError/ModelLoadError."""

    @abstractmethod
    def predict(
        self, image: Image.Image, *, confidence: float, iou: float
    ) -> DetectionResult:
        """Run one inference pass over a PIL image."""

    def model_info(self) -> dict[str, Any]:
        """Facts about this detector, for the Dashboard and About pages."""
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "weights_path": str(self.weights_path),
            "weights_present": self.is_available(),
            "loaded": self.is_ready(),
            "labels": list(self.labels),
            "labels_source": self.labels_source,
            "is_general_purpose": self.is_general_purpose,
        }


class UltralyticsDetector(Detector):
    """Ultralytics YOLO implementation of :class:`Detector`.

    The heavy `ultralytics`/`torch` import happens lazily inside the default
    loader, so importing this module (and running the test suite) does not
    require the ML stack. A `model_loader` can be injected for testing.
    """

    def __init__(
        self,
        model_id: str,
        weights_path: str | Path,
        *,
        display_name: str = "",
        declared_labels: Sequence[str] = (),
        is_general_purpose: bool = False,
        model_loader: ModelLoader | None = None,
    ) -> None:
        self.model_id = model_id
        self.display_name = display_name or model_id
        self.weights_path = Path(weights_path)
        self.is_general_purpose = is_general_purpose
        self._declared_labels: tuple[str, ...] = tuple(declared_labels)
        self._labels: tuple[str, ...] = self._declared_labels
        self._labels_source: str = "declared" if self._declared_labels else "unknown"
        self._model_loader = model_loader
        self._model: Any | None = None

    # -- state -------------------------------------------------------------
    @property
    def labels(self) -> tuple[str, ...]:
        return self._labels

    @property
    def labels_source(self) -> str:
        return self._labels_source

    def is_available(self) -> bool:
        return self.weights_path.is_file()

    def is_ready(self) -> bool:
        return self._model is not None

    # -- lifecycle ---------------------------------------------------------
    def load(self) -> None:
        if self._model is not None:
            return
        if not self.is_available():
            raise ModelUnavailableError(
                f"Model weights not found at '{self.weights_path}'. "
                "Place the trained weights at that path, or set JUDETECTOR_MODEL_PATH "
                "to an existing .pt file. No detections can be produced without weights."
            )

        loader = self._model_loader or _default_ultralytics_loader
        try:
            model = loader(str(self.weights_path))
        except ModelUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI verbatim
            raise ModelLoadError(
                f"Failed to load weights from '{self.weights_path}': {exc}"
            ) from exc

        names = getattr(model, "names", None)
        if isinstance(names, dict) and names:
            try:
                ordered = tuple(str(names[key]) for key in sorted(names))
            except TypeError:
                ordered = tuple(str(value) for value in names.values())
            if ordered:
                self._labels = ordered
                self._labels_source = "model"
        self._model = model

    # -- inference ---------------------------------------------------------
    def predict(
        self, image: Image.Image, *, confidence: float = 0.25, iou: float = 0.45
    ) -> DetectionResult:
        if self._model is None:
            raise ModelUnavailableError(
                "Detector is not loaded. Call load() successfully before predict()."
            )
        if not isinstance(image, Image.Image):
            raise TypeError("image must be a PIL.Image.Image")

        conf = _unit_interval(confidence, "confidence")
        iou_value = _unit_interval(iou, "iou")

        started = time.perf_counter()
        try:
            raw = self._model(image, conf=conf, iou=iou_value, verbose=False)
        except Exception as exc:  # noqa: BLE001
            raise ModelLoadError(f"Inference failed: {exc}") from exc
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        detections = _parse_results(raw, self._labels)
        return DetectionResult(
            detections=detections,
            model_id=self.model_id,
            image_width=image.width,
            image_height=image.height,
            confidence_threshold=conf,
            iou_threshold=iou_value,
            inference_ms=elapsed_ms,
        )


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _default_ultralytics_loader(weights: str) -> Any:
    """Import Ultralytics lazily so the app/tests run without PyTorch."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ModelUnavailableError(
            "The 'ultralytics' package is not installed, so weights cannot be loaded. "
            "Install the optional ML stack with: pip install -r requirements-model.txt"
        ) from exc
    return YOLO(weights)


def _unit_interval(value: float, name: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc
    if not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{name} must be within [0, 1], got {numeric}")
    return numeric


def _to_python(value: Any) -> Any:
    """Convert tensors/arrays to plain Python without importing torch or numpy."""
    if value is None:
        return []
    if hasattr(value, "detach"):
        try:
            value = value.detach()
        except Exception:  # noqa: BLE001 - not a torch tensor
            pass
    if hasattr(value, "cpu") and callable(value.cpu):
        try:
            value = value.cpu()
        except Exception:  # noqa: BLE001
            pass
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return value.tolist()
        except Exception:  # noqa: BLE001
            pass
    return value


def _normalise_rows(value: Any) -> list[list[float]]:
    """Return a list of numeric rows from a tensor/array/list of boxes."""
    data = _to_python(value)
    if data is None or data == []:
        return []
    if isinstance(data, (int, float)):
        return [[float(data)]]
    if isinstance(data, (list, tuple)):
        rows: list[list[float]] = []
        for item in data:
            if isinstance(item, (list, tuple)):
                rows.append([float(v) for v in item])
            else:
                rows.append([float(item)])
        return rows
    return []


def _normalise_flat(value: Any) -> list[float]:
    data = _to_python(value)
    if data is None or data == []:
        return []
    if isinstance(data, (int, float)):
        return [float(data)]
    flat: list[float] = []
    if isinstance(data, (list, tuple)):
        for item in data:
            if isinstance(item, (list, tuple)):
                flat.extend(float(v) for v in item)
            else:
                flat.append(float(item))
    return flat


def _parse_results(raw: Any, labels: Sequence[str]) -> tuple[Detection, ...]:
    """Convert an Ultralytics-style result object into `Detection` objects."""
    if raw is None:
        return ()
    result = raw[0] if isinstance(raw, (list, tuple)) and raw else raw
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return ()

    rows = _normalise_rows(getattr(boxes, "xyxy", []))
    if not rows:
        return ()
    confidences = _normalise_flat(getattr(boxes, "conf", []))
    classes = _normalise_flat(getattr(boxes, "cls", []))

    if not confidences:
        # Refuse to invent a score we were not given.
        raise ModelLoadError(
            "The detector returned boxes without confidence scores; refusing to "
            "fabricate confidence values."
        )

    detections: list[Detection] = []
    for index, row in enumerate(rows):
        if len(row) < 4:
            continue
        confidence = confidences[index] if index < len(confidences) else 0.0
        class_index = int(classes[index]) if index < len(classes) else 0
        if 0 <= class_index < len(labels):
            label = labels[class_index]
        else:
            label = f"class_{class_index}"
        detections.append(
            Detection(
                box_xyxy=(row[0], row[1], row[2], row[3]),
                confidence=float(confidence),
                label=label,
            )
        )
    return tuple(detections)
