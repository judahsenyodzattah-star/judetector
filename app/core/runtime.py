"""Streamlit-facing runtime: cached registry and cached detector instances.

Kept separate from `core/` logic so that everything in `detector.py`,
`registry.py`, `metrics.py`, `stats.py` remains testable without Streamlit.

Caching note: the detector object is cached, not the *loaded model state* of an
exception. Failures are never cached -- a missing-weights error is cheap to
re-raise and must not be sticky after the user fixes the path.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.core.detector import Detector
from app.core.registry import ModelRegistry, ModelSpec, build_detector, load_registry

__all__ = ["get_registry", "get_detector", "clear_detector_cache"]


@st.cache_resource(show_spinner=False)
def get_registry() -> ModelRegistry:
    """Load the registry once per server process."""
    return load_registry()


@st.cache_resource(show_spinner=False)
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
    """Return the (cached, not necessarily loaded) detector for a spec."""
    return _cached_detector(
        spec.id,
        str(spec.weights_path),
        spec.display_name,
        spec.declared_labels,
        spec.is_general_purpose,
    )


def clear_detector_cache() -> None:
    """Drop cached detectors (used when weights change on disk)."""
    _cached_detector.clear()
