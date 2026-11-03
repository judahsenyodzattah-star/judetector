"""About: product information, privacy and model limitations.

No academic or submission details appear here — and none appear anywhere else in
the user-facing application.
"""

from __future__ import annotations

import streamlit as st

from app.components.model_sidebar import current_model
from app.core.runtime import get_detector
from app.ui.components import (
    bullets,
    empty_state,
    kv_row,
    meta,
    note,
    page_header,
    section,
    tiles,
)
from app.ui.theme import inject_theme

__all__ = ["render"]

_CAPABILITY_TILES = [
    (
        "scan",
        "Image and camera detection",
        "Runs the connected model over uploaded images and single-frame camera captures.",
    ),
    (
        "target",
        "Boxes and confidence",
        "Every result carries a bounding box, a class label and the model's confidence score.",
    ),
    (
        "sliders",
        "Adjustable thresholds",
        "Confidence and IoU are configurable per analysis, with the applied values shown.",
    ),
    (
        "chart",
        "Recorded analytics",
        "Evaluation results are displayed as recorded; session activity is summarised separately.",
    ),
]


def render() -> None:
    inject_theme()

    spec, model_error = current_model()
    connected = bool(spec is not None and spec.weights_present)

    page_header(
        "About",
        "What this workspace does, how it handles your images, and where the model's "
        "limits are.",
        eyebrow="Product",
        status=("Model connected", "ok") if connected else ("Model not connected", "warn"),
    )

    section("What it is")
    st.markdown(
        "JUDEtector is a computer-vision workspace for object detection. It runs a "
        "trained Ultralytics YOLO model over an image or a camera snapshot and returns "
        "bounding boxes, a detection count and a confidence score per detection. The "
        "detector sits behind a model-agnostic interface, so a different model can be "
        "registered without changing the interface."
    )

    section("Capabilities")
    tiles(_CAPABILITY_TILES)

    section("Privacy")
    bullets(
        [
            "Images are decoded and analysed in memory for the request only; nothing is written to disk.",
            "Session analytics store filenames, counts and timings — never image content.",
            "No account, upload history or third-party analytics are used.",
            "Only process images of people who know their image is being analysed.",
        ]
    )

    section("Detection is not recognition")
    st.markdown(
        "This system locates objects. It does not identify people, compare faces against "
        "a gallery or build identity profiles, and it must not be used for surveillance "
        "or access-control decisions."
    )

    section("Model limitations")
    if model_error:
        note(model_error, tone="warn", icon="alert-circle")
    elif spec is None:
        empty_state(
            icon="cpu",
            title="No model configured",
            body="Register a detector in config/models.json to enable detection.",
        )
    else:
        limitations = [
            "Subject-specific: the bundled model is trained on a single class, so detections describe that subject only, not faces in general.",
            "Not a validated general-purpose face detector, and not a face-recognition system.",
            "No recorded evaluation metrics yet — performance figures are shown only when a real evaluation run is recorded.",
            "Small training set, so accuracy on unfamiliar subjects, lighting or poses is expected to be weaker.",
            "Camera capture is single-frame; continuous live video is not supported.",
            "CPU inference, so latency is higher than a GPU deployment and very large images are downscaled.",
        ]
        bullets(limitations)
        if spec.is_general_purpose:
            note("This model is registered as general purpose.", tone="ok", icon="check-circle")
        else:
            note(
                "Its declared classes are "
                f"{', '.join(spec.declared_labels) or 'none'}; outputs are limited to those.",
                tone="warn",
                icon="alert-triangle",
            )

    with st.expander("Model details", expanded=False):
        if spec is None:
            meta("No model is configured.")
        else:
            detector = get_detector(spec)
            info = detector.model_info()
            kv_row(
                [
                    ("Model", spec.display_name),
                    ("Task", spec.task),
                    ("Kind", spec.kind.replace("_", " ")),
                    ("Weights", "present" if info["weights_present"] else "missing"),
                ]
            )
            meta(f"Class labels: {', '.join(info['labels']) if info['labels'] else 'unknown'}")
            if spec.dataset:
                dataset = spec.dataset
                split = dataset.get("split") or {}
                meta(
                    f"Dataset: {dataset.get('dataset_name') or (spec.provenance or {}).get('dataset_name', '—')} · "
                    f"{dataset.get('total_images', '—')} images · "
                    f"{dataset.get('annotated_images', '—')} annotated · "
                    f"{split.get('train', '—')}/{split.get('val', '—')}/{split.get('test', '—')} split"
                )
            if spec.provenance.get("training_status"):
                meta(str(spec.provenance["training_status"]))

    section("Technology")
    st.markdown(
        "Python · Streamlit interface · Ultralytics YOLO detection · Pillow rendering · "
        "pandas tables. The model layer is optional at runtime: the application starts "
        "and remains navigable without any weights installed."
    )
