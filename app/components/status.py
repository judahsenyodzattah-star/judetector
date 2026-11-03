"""Model status / honesty banners.

The point of this module: whenever the app shows detections, the user must also
be able to see *which* model produced them and whether it is a validated
general-purpose face detector (it is not, for the current `judah` model).
"""

from __future__ import annotations

import streamlit as st

from app.core.detector import Detector
from app.core.registry import ModelSpec

__all__ = [
    "render_model_caption",
    "render_scope_warning",
    "render_setup_help",
    "render_labels_line",
]


def render_model_caption(spec: ModelSpec, detector: Detector | None = None) -> None:
    """One-line summary of the active model, used at the top of working pages."""
    parts = [f"**Model:** {spec.display_name}"]
    parts.append("weights found" if spec.weights_present else "weights missing")
    if detector is not None and detector.is_ready():
        parts.append(f"{len(detector.labels)} loaded label(s)")
    st.caption(" · ".join(parts))


def render_scope_warning(spec: ModelSpec) -> None:
    """Make the subject-specific caveat impossible to miss."""
    if spec.is_general_purpose:
        return
    labels = ", ".join(spec.declared_labels) if spec.declared_labels else "n/a"
    st.warning(
        "**Scope:** this is a **subject-specific detector**, not a validated "
        f"general-purpose face detector. Its class label(s) are: `{labels}`. "
        "It was trained on a small single-class dataset by the project author, so "
        "its detections describe *that* subject only. Do not read its output as "
        "\u201cany human face detected\u201d.",
        icon="⚠️",
    )


def render_labels_line(labels: tuple[str, ...], source: str) -> None:
    """Show labels exactly as they will appear on boxes, with their provenance."""
    if not labels:
        st.caption("Class labels: unknown (model not loaded and none declared).")
        return
    rendered = ", ".join(f"`{label}`" for label in labels)
    if source == "model":
        st.caption(f"Class labels (from the loaded model file): {rendered}")
    else:
        st.caption(
            f"Class labels (declared in config, not yet verified against the model file): "
            f"{rendered}"
        )


def render_setup_help(spec: ModelSpec) -> None:
    """Actionable instructions for supplying weights."""
    with st.expander("How to connect your trained model", expanded=True):
        st.markdown(
            f"""
JUDEtector does not ship model weights. To enable detection:

1. Export/download your trained Ultralytics weights (`best.pt`).
2. Place the file at:

   ```
   {spec.weights_path}
   ```

   …or point the app at it without moving the file:

   ```bash
   export JUDETECTOR_MODEL_PATH=/absolute/path/to/best.pt
   ```

3. Install the optional ML stack (needed to load PyTorch weights):

   ```bash
   pip install -r requirements-model.txt
   ```

4. Restart the app. The sidebar status will change from *weights missing* to
   *weights found*, and the model's real class labels will be read from the file.

Weights are intentionally **git-ignored** — never commit them.
"""
        )
