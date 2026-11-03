"""Sidebar model selection and detection settings.

Multi-model by construction: if the registry grows, a dropdown appears; with one
model, the name is simply displayed. Nothing here assumes a face model.
"""

from __future__ import annotations

import streamlit as st

from app.core import config
from app.core.errors import RegistryError
from app.core.registry import ModelSpec
from app.core.runtime import clear_detector_cache, get_registry

__all__ = ["select_model", "render_settings", "render_sidebar_footer"]


def select_model() -> tuple[ModelSpec | None, str | None]:
    """Render the model selector. Returns (spec, error_message)."""
    try:
        registry = get_registry()
    except RegistryError as exc:
        return None, str(exc)

    enabled = registry.enabled()
    if not enabled:
        return None, "No enabled models are registered in config/models.json."

    default = registry.default()
    default_index = next(
        (index for index, spec in enumerate(enabled) if spec.id == default.id), 0
    )

    with st.sidebar:
        st.subheader("Model")
        if len(enabled) == 1:
            spec = enabled[0]
            st.markdown(f"**{spec.display_name}**")
        else:
            options = [spec.id for spec in enabled]
            by_id = {spec.id: spec for spec in enabled}
            chosen = st.selectbox(
                "Active model",
                options,
                index=default_index,
                format_func=lambda model_id: by_id[model_id].display_name,
                key="active_model_id",
            )
            spec = by_id[chosen]

        if spec.weights_present:
            st.caption(f"✅ weights found · `{spec.weights_path.name}`")
        else:
            st.caption("⚠️ weights missing")

        if spec.is_subject_specific:
            st.caption("Subject-specific model")

        if st.button("Clear cached model", help="Reload weights after replacing the file"):
            clear_detector_cache()
            st.rerun()

    return spec, None


def render_settings() -> tuple[float, float]:
    """Confidence / IoU controls. Values are thresholds, never model claims."""
    with st.sidebar:
        st.subheader("Detection settings")
        confidence = st.slider(
            "Confidence threshold",
            min_value=float(config.CONFIDENCE_RANGE[0]),
            max_value=float(config.CONFIDENCE_RANGE[1]),
            value=float(config.DEFAULT_CONFIDENCE),
            step=0.01,
            help="Lower shows more, weaker detections. Raises the count, not the quality.",
        )
        iou = st.slider(
            "IoU threshold (NMS)",
            min_value=float(config.IOU_RANGE[0]),
            max_value=float(config.IOU_RANGE[1]),
            value=float(config.DEFAULT_IOU),
            step=0.05,
            help="Overlap above which duplicate boxes are suppressed.",
        )
    return confidence, iou


def render_sidebar_footer() -> None:
    with st.sidebar:
        st.divider()
        st.caption("JUDEtector · Senyo-Dzattah Judah Agbemavor · PUIT/23110016")
        st.caption("BSc Information Technology · Pentecost University")
