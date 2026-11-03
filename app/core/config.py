"""Application configuration and path resolution.

All values are overridable with environment variables so the same code runs
locally, in CI and on a hosted deployment without edits.
"""

from __future__ import annotations

import os
from pathlib import Path

# app/core/config.py -> app/core -> app -> project root
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DEFAULT_CONFIG_DIR: Path = PROJECT_ROOT / "config"
DEFAULT_REGISTRY_PATH: Path = DEFAULT_CONFIG_DIR / "models.json"
DEFAULT_MODELS_DIR: Path = PROJECT_ROOT / "models"
DEFAULT_METRICS_DIR: Path = PROJECT_ROOT / "metrics"

# Detection defaults. These are UI starting points, not claims about model quality.
DEFAULT_CONFIDENCE: float = 0.25
DEFAULT_IOU: float = 0.45
CONFIDENCE_RANGE: tuple[float, float] = (0.01, 0.99)
IOU_RANGE: tuple[float, float] = (0.10, 0.95)

# Upload / decode guards (protect free-tier hosting from memory exhaustion).
MAX_UPLOAD_MB: int = 25
MAX_IMAGE_DIMENSION: int = 4000
SUPPORTED_IMAGE_TYPES: tuple[str, ...] = ("jpg", "jpeg", "png", "webp", "bmp")

# Session statistics cap, so a long session cannot grow session_state without bound.
MAX_RECORDED_RUNS: int = 200

# Environment variable names.
ENV_REGISTRY_PATH = "JUDETECTOR_REGISTRY"
ENV_METRICS_DIR = "JUDETECTOR_METRICS_DIR"
ENV_MODEL_PATH = "JUDETECTOR_MODEL_PATH"


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


def get_registry_path() -> Path:
    """Path to the model registry JSON file."""
    return _env_path(ENV_REGISTRY_PATH) or DEFAULT_REGISTRY_PATH


def get_metrics_dir() -> Path:
    """Directory containing evaluation metrics records."""
    return _env_path(ENV_METRICS_DIR) or DEFAULT_METRICS_DIR


def get_model_path_override() -> Path | None:
    """Optional absolute override for the default model's weights file.

    Lets you point the app at weights stored outside the repository
    (e.g. a Drive sync folder) without editing committed config.
    """
    return _env_path(ENV_MODEL_PATH)


def resolve_path(path: str | Path, *, base: Path | None = None) -> Path:
    """Resolve a possibly-relative path against the project root."""
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (base or PROJECT_ROOT) / candidate
