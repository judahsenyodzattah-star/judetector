# JUDEtector

**An AI-powered object-detection web application** — Python, Streamlit and a
modular Ultralytics YOLO detector.

| | |
|---|---|
| **Student** | Senyo-Dzattah Judah Agbemavor |
| **Student ID** | PUIT/23110016 |
| **Programme** | BSc Information Technology |
| **Institution** | Pentecost University |

> **Status — Milestone 1 (application foundation) complete.**
> The full interface, the model-agnostic detection layer and the automated test
> suite are implemented and passing. **A trained model is not yet connected** —
> the repository deliberately ships no weights. See
> [Connecting your model](docs/MODEL_INTEGRATION.md).

---

## What it does

JUDEtector runs a trained YOLO detector over an uploaded image or a browser camera
snapshot and reports:

- bounding boxes drawn on the image, with class label and confidence per box;
- the number of detections and the confidence scores for each one;
- the original and processed images side by side;
- a downloadable annotated PNG;
- an honest performance dashboard and session statistics.

It is **general-purpose by architecture**: the UI talks to a `Detector` interface
and a model registry, never to a specific model, so a different detector can be
registered by editing `config/models.json`.

## What it deliberately does not do

- **No invented results.** With no weights, no model and no evaluation record, the
  app says so and shows nothing. There is no placeholder number, no guessed box and
  no fallback metric anywhere in the codebase — and the test suite enforces that.
- **No general-purpose claims.** The only registered model is trained on a
  single-class (`judah`) dataset. It is subject-specific, and every working page
  carries that warning.
- **No face recognition.** This system detects; it does not identify people.
- **No committed data.** Datasets, private images and model weights are git-ignored.

---

## Quickstart

```bash
git clone https://github.com/judahsenyodzattah-star/judetector.git
cd judetector

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app/main.py
```

Open <http://localhost:8501>. The app starts fully without the ML stack; detection
becomes available once weights and the optional packages are installed.

#### Serving from a tunnel, container or preview domain

Streamlit refuses WebSocket connections whose `Origin` does not match the address
the app is bound to, which shows up as a blank page behind a proxy. Allow your
origin explicitly:

```bash
streamlit run app/main.py --server.corsAllowedOrigins=https://your-app.example.com
```

Only if your proxy rewrites origins and you cannot set the allow-list, fall back to
`--server.enableCORS false`. That accepts a WebSocket from any origin, so use it for
trusted, short-lived preview environments rather than public deployments.

### Enable detection

```bash
pip install -r requirements-model.txt      # ultralytics + torch
mkdir -p models/judah-face-v1
cp /path/to/your/best.pt models/judah-face-v1/best.pt
# ...or leave the file where it is and:
export JUDETECTOR_MODEL_PATH=/absolute/path/to/best.pt

streamlit run app/main.py
```

Full procedure and troubleshooting: [`docs/MODEL_INTEGRATION.md`](docs/MODEL_INTEGRATION.md).

---

## Application sections

The application opens on **Home**, which shows the product's subject rather than a
pitch: the same specimen mounted twice, once as captured and once with the marking the
model draws, captioned as an illustration.

| Page | Purpose |
|---|---|
| **Home** (default) | One headline, one sentence, one primary action (*Analyse an image*) with a secondary camera link, the same specimen mounted twice (*Original* / *Annotated*) and captioned "Illustration, not an actual detection result.", the flow as four stations on one rule, and a privacy footer |
| **Detect** | Upload an image (mounted and captioned with file name, frame and size) → *Analyse image* → a fixed-column readout (count, mean confidence, confidence range, applied thresholds), the original and annotated prints, and the annotated-image download. Thresholds sit in a collapsed **Advanced settings** panel. |
| **Camera** | Browser snapshot → the same pipeline, one still frame per capture (no live video) |
| **Help** | How it works, what the numbers mean, privacy, honest limitations |
| **Developer** (`/developer`, hidden) | Model resolution, weights paths, runtime availability, setup commands, dataset composition, recorded evaluation metrics, session activity |

### Interface

The interface is a **proof sheet**, not a dashboard, and it is one shared stylesheet
rather than per-page styling:

- `app/ui/theme.py` — design tokens and one stylesheet. Sheet `#F4F2ED`, mounts
  `#FFFFFF`, ink `#16181A`, secondary ink `#52585C`, hairlines `#D0CBC1`, and one
  marking colour, ochre `#8A5A00`, which may fill an action, underline the active
  navigation entry, draw a focus ring or outline a detection — never a panel, badge
  or tinted section. Spacing is a 4px scale (`--jd-1` … `--jd-9`, 4–96 px), corners
  are 2px, and effects are limited to focus rings.
- `app/ui/components.py` — the primitives: page head, section, mounted plate,
  caption strip, fixed-column readout, flow rule, note, empty state, steps, bullets
  and footer. Monospace is reserved for facts (file name, frame, size, counts,
  confidences, thresholds); prose is never set in it.
- `.streamlit/config.toml` — the same tokens where Streamlit can apply them itself
  (colours, 2px radii, 15px base size, sans/mono roles), so native widgets inherit
  the language instead of being overridden.
- `app/ui/nav.py` — the four consumer destinations via Streamlit's own
  `st.navigation`.

Icons appear in exactly one place: the four navigation entries, because
`st.Page(icon=...)` accepts only an emoji or `:material/name:` and the drawer is
where a glyph earns its keep. Page content uses type, alignment and hairlines
instead, so there is no icon set to keep consistent. Replacing the native
navigation with hand-written links would cost URL routing, keyboard support and the
mobile drawer.

The interface is split by audience. End users only ever see the workflow: no weights
paths, dependency names, registry vocabulary, dataset statistics or evaluation
configuration appear on Home, Detect, Camera or Help. Those live on the developer page.

That page is **hidden from the navigation, not protected by it** — Streamlit's
`visibility="hidden"` hides a route; it does not authorise one. Open
`/developer` directly, and restrict it at the hosting layer before any public
deployment. Nothing in the interface claims access control.

When inference is unavailable the user sees one plain line ("Image analysis is
temporarily unavailable") while the technical cause is kept for the developer page.

---

## Project structure

```
judetector/
├── app/
│   ├── main.py                  # entry point + navigation
│   ├── views/                   # Home, Detect, Camera, Help, Developer
│   ├── components/              # shared UI: pipeline, workflow, results, settings
│   ├── ui/                      # design system: theme, components, navigation
│   └── core/                    # Streamlit-free logic
│       ├── config.py            # paths, defaults, env overrides
│       ├── detector.py          # Detector interface + UltralyticsDetector
│       ├── registry.py          # model registry (multi-model)
│       ├── metrics.py           # evaluation-record loading (never fabricates)
│       ├── stats.py             # session statistics
│       ├── rendering.py         # bounding boxes, side-by-side
│       ├── image_io.py          # decode, guard, encode
│       ├── errors.py            # domain errors
│       └── runtime.py           # Streamlit-cached wiring
├── assets/                      # brand marks used by the sidebar and favicon
├── config/models.json           # model registry (the swap point)
├── metrics/                     # evaluation records (none yet — by design)
├── models/                      # weights go here (git-ignored)
├── tests/                       # 232 automated tests
└── docs/                        # proposal, integration guide, testing
```

### Design in one paragraph

Views render; `components/pipeline.py` orchestrates; `core/detector.py` performs
inference; `core/registry.py` decides *which* detector. Model loading is lazy and
cached per process, threshold handling is validated at the boundary, and every
failure mode returns a plain outcome object that the UI displays honestly instead
of raising into a stack trace.

---

## Configuration

| Setting | Default | Override |
|---|---|---|
| Model registry | `config/models.json` | `JUDETECTOR_REGISTRY` |
| Active weights | per registry entry | `JUDETECTOR_MODEL_PATH` |
| Metrics directory | `metrics/` | `JUDETECTOR_METRICS_DIR` |
| Confidence threshold | 0.25 | sidebar slider |
| IoU threshold | 0.45 | sidebar slider |
| Max upload | 25 MB | `.streamlit/config.toml` |
| Max image dimension | 4000 px | `app/core/config.py` |

---

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest        # 144 passed
ruff check .            # clean
```

Coverage includes the detector contract, registry validation, metrics honesty rules,
rendering, image guards, session statistics, repository hygiene, and interface tests
driven by Streamlit's `AppTest` — including an end-to-end upload→detection test and
its inverse (no weights ⇒ no detections). Details: [`docs/TESTING.md`](docs/TESTING.md).

---

## Model and data

**Model (`judah-face-v1`)** — a single-class Ultralytics detector for the subject
`judah`, trained by the project author on the `judy-face-detection` dataset. It is
**not** a validated general-purpose face detector. No metrics are recorded in this
repository yet; the developer page reports that fact rather than filling the gap.

**Dataset (`judy-face-detection`, declared by the author)** — 711 images
(675 annotated, 36 reserved for later annotation), one class `judah`, split
368 train / 203 val / 140 test. The dataset itself is not stored here.

Evaluation numbers belong in `metrics/<model-id>.json` — see
[`metrics/README.md`](metrics/README.md).

## Ethics

Detection is not recognition: JUDEtector locates objects, it does not identify
people. Images should only be processed with the knowledge and consent of the
people in them. Uploads are processed in memory and are not written to disk;
session statistics store filenames and counts, not image content. See the Help page
in the running app for the full statement.

## Roadmap

- [x] **Milestone 1** — foundation, interface, modular detector integration, tests
- [ ] **Milestone 2** — connect the trained `judah` model; verify labels and latency
- [ ] **Milestone 3** — record real evaluation metrics; surface them on the developer page
- [ ] **Milestone 4** — register a general-purpose face detector; compare models
- [ ] **Milestone 5** — deployment, demo script and report evidence

## Licence note

This repository contains application code only and intentionally publishes no
dataset, no images and no weights. **Ultralytics YOLO is AGPL-3.0** — keep that in
mind if this code is ever used in a closed-source or commercial context, where an
Ultralytics Enterprise licence would be required. Any dataset used for training must
be cited and used within the terms of its own licence.
