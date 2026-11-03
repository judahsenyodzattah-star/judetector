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

The application opens on **Home**, a short landing page that leads straight into the
workflow.

| Page | Purpose |
|---|---|
| **Home** (default) | Hero with two calls to action (*Start detecting*, *Try camera*), an illustrative original → annotated preview, three steps, and a privacy footer |
| **Detect** | Upload an image → *Analyse image* → count, mean confidence, original and annotated images, annotated-image download. Confidence/overlap thresholds sit in a collapsed **Advanced settings** panel. |
| **Camera** | Browser snapshot → the same pipeline, one still frame per capture (no live video) |
| **Help** | How it works, what the numbers mean, privacy, honest limitations |
| **Developer** (`/developer`, hidden) | Model resolution, weights paths, runtime availability, setup commands, dataset composition, recorded evaluation metrics, session activity |

### Interface

The interface is a small design system rather than per-page styling:

- `app/ui/theme.py` — design tokens and one shared stylesheet (off-white canvas,
  charcoal type, restrained teal accent, consistent radii and hover/active states).
- `app/ui/icons.py` — one inline SVG family (Lucide geometry): 24px grid, 2px
  stroke, round caps and joins, three context sizes (16 / 20 / 24), colour
  inherited from the tokens. No emoji and no second icon style in page content.
- `app/ui/components.py` — reusable primitives: hero, page header, sections, status
  pills, notes, empty states, steps, key/value strips, footer.
- `app/ui/nav.py` — the four consumer destinations via Streamlit's own
  `st.navigation`.

Streamlit's `st.Page(icon=...)` accepts only an emoji or `:material/name:`, so the
navigation uses the closest Material Symbols Rounded glyph. Everything inside the
pages is Lucide. Replacing the native navigation with hand-written links would cost
URL routing, keyboard support and the mobile drawer, which is not a trade worth
making for icon appearance. `tests/test_ui_icons.py` keeps Material confined to
`nav.py` and enforces the icon rules.

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
│   ├── ui/                      # design system: theme, icons, components, navigation
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
