"""About page: project, student, model, dataset, limitations and ethics."""

from __future__ import annotations

import streamlit as st

from app.components.model_sidebar import select_model
from app.components.status import render_labels_line
from app.core import config
from app.core.runtime import get_detector

__all__ = ["render"]


def render() -> None:
    st.title("About JUDEtector")

    spec, model_error = select_model()
    if model_error:
        st.error(f"Model configuration problem: {model_error}")

    st.subheader("Project")
    st.markdown(
        """
**JUDEtector** is an academic AI object-detection web application developed as part
of a BSc Information Technology programme at Pentecost University.

Its purpose is to demonstrate a complete, reproducible pipeline: a trained
Ultralytics YOLO model served through a modular Python/Streamlit application, with
image upload, browser camera capture, bounding-box visualisation, per-detection
confidence scores, and an honest performance dashboard.
"""
    )

    st.subheader("Student")
    st.markdown(
        """
| | |
|---|---|
| **Name** | Senyo-Dzattah Judah Agbemavor |
| **Student ID** | PUIT/23110016 |
| **Programme** | BSc Information Technology |
| **Institution** | Pentecost University |
"""
    )

    st.subheader("Model information")
    if spec is None:
        st.info("No model is currently configured.")
    else:
        detector = get_detector(spec)
        info = detector.model_info()
        st.markdown(
            f"""
- **Active model:** {spec.display_name} (`{spec.id}`)
- **Task:** {spec.task}
- **Kind:** {spec.kind} · general-purpose face detector: **{'yes' if spec.is_general_purpose else 'no'}**
- **Weights path:** `{spec.weights_path}`
- **Weights present on disk:** {'yes' if info['weights_present'] else 'no'}
- **Labels source:** {info['labels_source']}
"""
        )
        render_labels_line(tuple(info["labels"]), info["labels_source"])
        if spec.description:
            st.caption(spec.description)

    st.subheader("Dataset information")
    if spec is not None and spec.dataset:
        dataset = spec.dataset
        split = dataset.get("split") or {}
        st.markdown(
            f"""
| Property | Value |
|---|---|
| Dataset | {(spec.provenance or {}).get('dataset_name', '—')} |
| Total images | {dataset.get('total_images', '—')} |
| Annotated images | {dataset.get('annotated_images', '—')} |
| Reserved, not yet annotated | {dataset.get('unannotated_reserved', '—')} |
| Classes | {', '.join(dataset.get('classes') or []) or '—'} |
| Train / Val / Test | {split.get('train', '—')} / {split.get('val', '—')} / {split.get('test', '—')} |
"""
        )
        st.caption(
            "These dataset figures are declared by the project author from the Ultralytics "
            "dataset record. The dataset itself is not stored in this repository."
        )
    else:
        st.info("No dataset information is recorded for the active model.")

    st.subheader("Limitations")
    st.markdown(
        """
- **Subject-specific model.** The currently registered model was trained on a single
  class (`judah`) from a small dataset of 711 images. It is **not** a validated
  general-purpose face detector, and its detections should not be interpreted as
  "any human face detected".
- **No published evaluation metrics yet.** The dashboard shows no metrics until a real
  evaluation record is supplied. Absence of numbers is deliberate: nothing is invented.
- **Small dataset.** With 675 annotated images across three splits, generalisation is
  limited, and per-class accuracy on unfamiliar subjects is expected to be poor.
- **Camera is snapshot-based.** Continuous live video is not implemented in this
  milestone; WebRTC streaming needs additional infrastructure and HTTPS/STUN support.
- **CPU-only inference.** Hosted deployments run on CPU, so detection is slower than a
  GPU and very large images are downscaled before inference.
- **Not for identification.** The system detects boxes; it does not recognise or
  identify people, and it is not suitable for surveillance or access-control decisions.
"""
    )

    st.subheader("Ethical considerations")
    st.markdown(
        """
**Detection is not recognition.** JUDEtector only answers *"is something detected
here, and where?"*. It does not perform face recognition, does not build identity
profiles, and does not match faces against any gallery. These are different tasks with
very different privacy consequences.

**Consent and privacy.** Any image of a person should only be processed with that
person's knowledge and consent. Uploaded images in this application are processed in
memory for the duration of the request; the app does not persist uploads to disk or
write them to a database. Session statistics record filenames and counts, not image
content.

**Dataset provenance.** Future training data must respect the licence of its source.
For example, benchmark face datasets are typically released for non-commercial
research use and may prohibit redistribution — which is why this repository ships
configuration and scripts, not datasets or weights.

**Bias and fairness.** Face-detection performance varies with skin tone, lighting,
pose, occlusion and image quality. A model trained on a small, single-subject dataset
will reflect the conditions of that data. Performance claims must be reported against
the data actually used, and re-evaluated before any new demographic or lighting
context.

**Academic honesty.** Every number displayed in this application is either declared
dataset metadata or a recorded evaluation result. Where evidence does not exist, the
interface says so rather than filling the gap.
"""
    )

    st.subheader("Technology")
    st.markdown(
        """
| Layer | Choice |
|---|---|
| Language | Python |
| Web framework | Streamlit |
| Detection | Ultralytics YOLO (loaded lazily, PyTorch weights) |
| Imaging | Pillow, NumPy |
| Tables / charts | pandas, Streamlit primitives |
| Tests | pytest, Streamlit `AppTest` |
| Version control | Git + GitHub |

The application is deliberately framework-thin beyond Streamlit: the model lives
behind a `Detector` interface so a different detector can be registered without
rewriting the interface.
"""
    )

    st.subheader("Configuration")
    st.markdown(
        f"""
| Setting | Value |
|---|---|
| Registry file | `{config.get_registry_path()}` |
| Metrics directory | `{config.get_metrics_dir()}` |
| Default confidence | {config.DEFAULT_CONFIDENCE} |
| Default IoU | {config.DEFAULT_IOU} |
| Max upload size | {config.MAX_UPLOAD_MB} MB |
| Max image dimension | {config.MAX_IMAGE_DIMENSION} px |

Environment overrides: `JUDETECTOR_REGISTRY`, `JUDETECTOR_METRICS_DIR`,
`JUDETECTOR_MODEL_PATH`.
"""
    )

    st.divider()
    st.caption(
        "JUDEtector · Milestone 1 (application foundation) · "
        "Senyo-Dzattah Judah Agbemavor · PUIT/23110016"
    )
