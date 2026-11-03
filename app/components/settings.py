"""Model resolution and analysis settings.

End users never choose a model or read registry state: the registered default is
used. The model *selector* and the reload control live on the developer page, so
they are defined here (next to resolution logic) but rendered only there.

Threshold controls stay available to end users, collapsed inside one expander so
they never compete with the primary workflow.
"""

from __future__ import annotations

import streamlit as st

from app.core import config
from app.core.errors import RegistryError
from app.core.registry import ModelRegistry, ModelSpec
from app.core.runtime import clear_detector_cache, get_registry

__all__ = [
    "advanced_settings",
    "current_model",
    "reload_model_button",
    "select_model",
]


def _registry_or_error() -> tuple[ModelRegistry | None, str | None]:
    try:
        return get_registry(), None
    except RegistryError as exc:
        return None, str(exc)


def current_model() -> tuple[ModelSpec | None, str | None]:
    """Resolve the active model without rendering any widget.

    A session override (set from the developer page) wins over the registry
    default, which keeps multi-model registries usable without exposing a
    selector to end users.
    """
    registry, error = _registry_or_error()
    if error or registry is None:
        return None, error

    enabled = registry.enabled()
    if not enabled:
        return None, "No models are configured."

    chosen_id = st.session_state.get("active_model_id")
    if chosen_id:
        for spec in enabled:
            if spec.id == chosen_id:
                return spec, None
    return registry.default(), None


def select_model() -> tuple[ModelSpec | None, str | None]:
    """Model selector — developer page only."""
    registry, error = _registry_or_error()
    if error or registry is None:
        return None, error

    enabled = registry.enabled()
    if not enabled:
        return None, "No models are configured."
    if len(enabled) == 1:
        return enabled[0], None

    ids = [spec.id for spec in enabled]
    by_id = {spec.id: spec for spec in enabled}
    default_id = registry.default().id
    if st.session_state.get("active_model_id") not in ids:
        st.session_state["active_model_id"] = default_id

    chosen = st.selectbox(
        "Active model",
        ids,
        format_func=lambda model_id: by_id[model_id].display_name,
        key="active_model_id",
    )
    return by_id[chosen], None


def advanced_settings() -> tuple[float, float]:
    """Collapsed confidence / IoU controls. Returns ``(confidence, iou)``."""
    with st.expander("Advanced settings", expanded=False):
        confidence = st.slider(
            "Confidence threshold",
            min_value=float(config.CONFIDENCE_RANGE[0]),
            max_value=float(config.CONFIDENCE_RANGE[1]),
            value=float(config.DEFAULT_CONFIDENCE),
            step=0.01,
            help="Lower values surface weaker matches and raise the count, not the quality.",
        )
        iou = st.slider(
            "Overlap threshold (IoU)",
            min_value=float(config.IOU_RANGE[0]),
            max_value=float(config.IOU_RANGE[1]),
            value=float(config.DEFAULT_IOU),
            step=0.05,
            help="How much two boxes may overlap before the weaker one is dropped.",
        )
    return confidence, iou


def reload_model_button() -> None:
    """Developer-page control: pick up replaced weights without a restart."""
    if st.button("Reload model", help="Clear cached detectors"):
        clear_detector_cache()
        st.rerun()
