"""Process-level caches for the API.

`app/core/runtime.py` caches with `st.cache_resource`, which would drag Streamlit
into the API process. This module is the API-side equivalent: plain `lru_cache`
over the same `load_registry` / `build_detector` factory, so the engine is
imported, never re-implemented.

Failures are not cached: a missing weights file or an unreadable registry is
cheap to re-raise and must not stay sticky after the operator fixes it.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.detector import Detector
from app.core.registry import ModelRegistry, ModelSpec, build_detector, load_registry

__all__ = ["clear_caches", "get_detector", "get_registry"]


@lru_cache(maxsize=4)
def get_registry(registry_path: str | None = None) -> ModelRegistry:
    """Load the registry once per (path, process)."""
    return load_registry(Path(registry_path) if registry_path else None)


@lru_cache(maxsize=8)
def _cached_detector(
    model_id: str,
    weights_path: str,
    display_name: str,
    declared_labels: tuple[str, ...],
    is_general_purpose: bool,
) -> Detector:
    spec = ModelSpec(
        id=model_id,
        display_name=display_name,
        weights_path=Path(weights_path),
        declared_labels=declared_labels,
        is_general_purpose=is_general_purpose,
    )
    return build_detector(spec)


def get_detector(spec: ModelSpec) -> Detector:
    """Return the cached (not necessarily loaded) detector for a spec."""
    return _cached_detector(
        spec.id,
        str(spec.weights_path),
        spec.display_name,
        spec.declared_labels,
        spec.is_general_purpose,
    )


def clear_caches() -> None:
    """Drop cached registries and detectors (used by tests and weight reloads)."""
    get_registry.cache_clear()
    _cached_detector.cache_clear()
