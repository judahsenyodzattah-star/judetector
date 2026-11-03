"""Home page: introduction, purpose and navigation."""

from __future__ import annotations

import streamlit as st

from app.components.model_sidebar import select_model
from app.components.status import render_scope_warning
from app.core.errors import RegistryError
from app.core.runtime import get_registry

__all__ = ["render"]


def render() -> None:
    st.title("JUDEtector")
    st.markdown(
        "**An AI-powered object-detection web application** for image and camera "
        "snapshot analysis, built on a trained Ultralytics YOLO model."
    )

    spec, model_error = select_model()

    left, right = st.columns([3, 2])

    with left:
        st.subheader("What this application does")
        st.markdown(
            """
Upload an image or take a camera snapshot, and JUDEtector runs a trained
Ultralytics YOLO detector over it. You get the annotated image, the number of
detections, and the confidence score for every detection.

- **Detect** — upload an image, tune the confidence threshold, inspect boxes and scores.
- **Camera** — capture a browser snapshot and analyse it with the same pipeline.
- **Dashboard** — model details, recorded evaluation metrics and session statistics.
- **About** — project background, dataset details, limitations and ethics.

Nothing is analysed until you provide an image. When weights are unavailable the
app says so and produces **no** detections rather than guessing.
"""
        )

        st.subheader("How detection works here")
        st.markdown(
            """
1. Your image is decoded to RGB and downscaled if it exceeds the size guard.
2. It is passed to the active detector — an Ultralytics YOLO model loaded lazily
   from configurable weights.
3. Boxes, labels and confidence scores come straight from the model's output.
   JUDEtector adds the drawing and the counts; it never adds detections.
"""
        )

    with right:
        st.subheader("Project")
        st.markdown(
            """
**Student:** Senyo-Dzattah Judah Agbemavor
**Student ID:** PUIT/23110016
**Programme:** BSc Information Technology
**Institution:** Pentecost University
"""
        )
        st.subheader("Active model")
        if model_error:
            st.error(model_error)
        elif spec is not None:
            st.markdown(f"**{spec.display_name}**")
            st.caption(f"id `{spec.id}` · task `{spec.task}`")
            if spec.weights_present:
                st.success("Weights found on disk", icon="✅")
            else:
                st.warning("Weights not connected yet", icon="⚠️")
            st.caption(
                "Class label(s): "
                + (", ".join(f"`{label}`" for label in spec.declared_labels) or "unknown")
            )

    if spec is not None:
        st.divider()
        render_scope_warning(spec)

    st.divider()
    st.subheader("Registered models")
    try:
        registry = get_registry()
    except RegistryError as exc:
        st.error(f"Could not read the model registry: {exc}")
        return

    rows = [
        {
            "id": item.id,
            "name": item.display_name,
            "kind": item.kind,
            "general purpose": "yes" if item.is_general_purpose else "no",
            "weights": "found" if item.weights_present else "missing",
            "enabled": "yes" if item.enabled else "no",
        }
        for item in registry.specs
    ]
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption(
        "Adding a model is a configuration change in `config/models.json` — the views "
        "never reference a specific model id."
    )
