"""Model provenance and limitation messaging.

Kept intentionally quiet: short inline notes and captions rather than large
banners, while still stating plainly that the bundled model is subject-specific
and produces no detections when weights are absent.
"""

from __future__ import annotations

import streamlit as st

from app.core.detector import Detector
from app.core.registry import ModelSpec
from app.ui.components import note

__all__ = [
    "render_labels_line",
    "render_model_caption",
    "render_scope_warning",
    "render_setup_help",
]


def render_model_caption(spec: ModelSpec, detector: Detector | None = None) -> None:
    """Single dim line summarising the active detector."""
    parts = [spec.display_name, f"task {spec.task}"]
    parts.append("weights found" if spec.weights_present else "weights missing")
    if detector is not None and detector.is_ready():
        parts.append(f"{len(detector.labels)} label(s) loaded")
    st.caption(" · ".join(parts))


def render_scope_warning(spec: ModelSpec) -> None:
    """State the model's real scope; skipped for general-purpose models."""
    if spec.is_general_purpose:
        return
    labels = ", ".join(spec.declared_labels) if spec.declared_labels else "none declared"
    note(
        "Subject-specific model. Its classes are "
        f"{labels}; it is not a validated general-purpose face detector, so "
        "detections describe that subject only.",
        tone="warn",
        icon="alert-triangle",
    )


def render_labels_line(labels: tuple[str, ...], source: str) -> None:
    """Show the class labels that will appear on boxes, with provenance."""
    if not labels:
        st.caption("Class labels: unknown — no model loaded and none declared.")
        return
    rendered = ", ".join(f"`{label}`" for label in labels)
    if source == "model":
        st.caption(f"Class labels, read from the model file: {rendered}")
    else:
        st.caption(f"Class labels declared in configuration (unverified): {rendered}")


def render_setup_help(spec: ModelSpec) -> None:
    """Concise, collapsible instructions for connecting weights."""
    with st.expander("Connect a model", expanded=False):
        st.markdown(
            f"""
Place trained Ultralytics weights at `{spec.weights_path}`,
or point the app at an existing file:

```bash
export JUDETECTOR_MODEL_PATH=/absolute/path/to/best.pt
```

Then install the optional runtime and reload:

```bash
pip install -r requirements-model.txt
```

Weights are git-ignored and never shipped with the application. Full details are
in `docs/MODEL_INTEGRATION.md`.
"""
        )
