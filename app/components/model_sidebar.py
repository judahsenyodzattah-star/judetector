"""Model selection, detection settings and the sidebar status block.

Model *controls* render inside the workspace pages (a collapsible settings
panel), not in the navigation rail. The rail carries a read-only status summary
so the connection state is always visible without competing with navigation.

Multi-model by construction: if the registry grows, a selector appears; with one
model, its name is simply displayed.
"""

from __future__ import annotations

import streamlit as st

from app.core import config
from app.core.errors import RegistryError
from app.core.registry import ModelRegistry, ModelSpec
from app.core.runtime import clear_detector_cache, get_registry
from app.ui.components import meta, status_pill
from app.ui.icons import svg

__all__ = [
    "current_model",
    "detection_settings",
    "render_sidebar_status",
    "select_model",
]


def _registry_or_error() -> tuple[ModelRegistry | None, str | None]:
    try:
        return get_registry(), None
    except RegistryError as exc:
        return None, str(exc)


def current_model() -> tuple[ModelSpec | None, str | None]:
    """Resolve the active model without rendering any widget."""
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
    """Render the model selector (only when more than one model is enabled)."""
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
    index = ids.index(default_id) if default_id in ids else 0

    chosen = st.selectbox(
        "Model",
        ids,
        index=index,
        format_func=lambda model_id: by_id[model_id].display_name,
        key="active_model_id",
    )
    return by_id[chosen], None


def detection_settings() -> tuple[ModelSpec | None, float, float, str | None]:
    """Collapsible settings panel: model, confidence and IoU thresholds.

    Returns ``(spec, confidence, iou, error)``.
    """
    confidence = float(config.DEFAULT_CONFIDENCE)
    iou = float(config.DEFAULT_IOU)

    with st.expander("Detection settings", expanded=False):
        spec, error = select_model()
        left, right = st.columns(2)
        confidence = left.slider(
            "Confidence threshold",
            min_value=float(config.CONFIDENCE_RANGE[0]),
            max_value=float(config.CONFIDENCE_RANGE[1]),
            value=float(config.DEFAULT_CONFIDENCE),
            step=0.01,
            help="Lower values surface weaker candidates. This raises the count, not the quality.",
        )
        iou = right.slider(
            "IoU threshold (NMS)",
            min_value=float(config.IOU_RANGE[0]),
            max_value=float(config.IOU_RANGE[1]),
            value=float(config.DEFAULT_IOU),
            step=0.05,
            help="Overlap above which duplicate boxes are suppressed.",
        )
        meta(
            "Thresholds apply to the next analysis. Inference runs once per image "
            "at the values above."
        )
        if st.button("Reload model", help="Pick up replaced weights without restarting"):
            clear_detector_cache()
            st.rerun()

    return spec, confidence, iou, error


def render_sidebar_status() -> None:
    """Read-only model status shown under the navigation rail."""
    spec, error = current_model()

    if error:
        body = (
            '<p class="jd-side__label">Model</p>'
            '<p class="jd-side__name">Configuration error</p>'
            f"{status_pill('Unavailable', 'warn')}"
        )
    elif spec is None:
        body = (
            '<p class="jd-side__label">Model</p>'
            '<p class="jd-side__name">None configured</p>'
            f"{status_pill('Unavailable', 'warn')}"
        )
    else:
        tone, label = (
            ("ok", "Connected") if spec.weights_present else ("warn", "Not connected")
        )
        body = (
            '<p class="jd-side__label">Model</p>'
            f'<p class="jd-side__name">{_safe(spec.display_name)}</p>'
            f"{status_pill(label, tone)}"
            f'<p class="jd-side__hint">{_safe("Weights found" if spec.weights_present else "Weights missing")}'
            f" · {_safe(spec.kind.replace('_', ' '))}</p>"
        )

    with st.sidebar:
        st.markdown(
            f'<div class="jd-side"><div class="jd-side__mark">{svg("scan", 15)}</div>{body}</div>',
            unsafe_allow_html=True,
        )


def _safe(value: str) -> str:
    from html import escape

    return escape(str(value))
