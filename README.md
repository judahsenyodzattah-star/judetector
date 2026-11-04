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

## Inference API

A FastAPI service wraps the same detection engine so a web client — and later a
mobile client — can run identical detection:

```bash
pip install -r requirements-dev.txt
uvicorn api.main:app --reload --port 8000
curl -s localhost:8000/v1/health
```

- `GET /v1/health` — liveness plus honest model state (`ok` only when weights
  exist; `degraded` otherwise).
- `GET /v1/model` — the public model card: kind, labels and their source,
  limitations, and recorded metrics verbatim or `null`.
- `POST /v1/detect` — one image in, detections out: pixel **and** normalised
  boxes, per-detection confidences, thresholds, model info, measured timings and
  the annotated PNG inline as base64. 25 MB upload cap, format and pixel-budget
  validation, RFC 9457 problems, and a per-instance rate limiter.

```bash
curl -s -X POST localhost:8000/v1/detect -F file=@photo.jpg | python -m json.tool
```

The API imports `app/core` and `app/components/pipeline.py` unchanged; it never
re-implements detection and never fabricates output. Parity is enforced by tests
that run the same fixture through the endpoint and through `analyse_image`
directly and compare every number.

**Rate limiting is per instance.** Cloud Run may run several instances, so the
built-in 30 requests/minute is a per-process shield, not a global quota; global
protection needs an edge limiter (Cloud Armor, API Gateway, Cloudflare) or a
shared counter store. [`docs/API.md`](docs/API.md) says so in the contract rather
than implying otherwise, and `RateLimit-Scope` reports what is actually
enforced.

Container:

```bash
docker build -t judetector-api .
docker run -p 8080:8080 -v /path/to/models:/models:ro \
  -e JUDETECTOR_MODEL_PATH=/models/best.pt judetector-api
```

Full contract and error taxonomy: [`docs/API.md`](docs/API.md).

## Web app (Next.js)

`web/` is the React interface for the same engine: App Router, TypeScript, no UI
framework dependency beyond React itself.

```bash
cd web && npm install && npm run dev     # http://localhost:3000
cd web && npm test && npm run build
```

- **Home** — one dominant uploader, a compact session panel, the model's
  limitations and its real availability. Choosing a file stages it; nothing is
  analysed until you ask.
- **Detect** — overlay drawn from the API's own boxes, confidence and IoU
  thresholds, one explicit **Analyse image**, then counts, confidences, measured
  timings, the service's annotated PNG (viewable and downloadable) and the
  detections as JSON.
- **Camera** — an honest empty state: live capture is the next stage, so the
  page shows no simulated viewfinder.
- **Help** — what the app does, what it refuses to do, how to read a result.

**Upload transport — verified, not assumed.** Vercel Functions accept at most
4.5 MB per request and cannot be raised, so a 25 MB image cannot be proxied
through a Next.js Route Handler on Vercel. Cloud Run accepts the full 25 MB
request. The app therefore reads health and the model card server-side and sends
`/v1/detect` **directly** from the browser to the API (CORS) when
`NEXT_PUBLIC_API_BASE_URL` is set; the same-origin proxy is kept for local
development only and refuses an over-limit body explicitly on Vercel instead of
failing opaquely. No upload limit was reduced. CORS is not treated as security:
the endpoint stays public, and the edge-limiter and alerting work that public
exposure still needs is listed in [`docs/WEB.md`](docs/WEB.md#before-this-endpoint-is-exposed-publicly).

Full notes: [`docs/WEB.md`](docs/WEB.md). Deployment plan, costs, abuse
protection, the model-weight blocker, the acceptance checklist and rollback:
[`docs/STAGE3_DEPLOYMENT_READINESS.md`](docs/STAGE3_DEPLOYMENT_READINESS.md) —
prepared, not executed. Plans and prices verified against the vendors' current
pages, the protected-preview route, the recurring-cost floor and the corrected
rollback: [`docs/STAGE3_PREFLIGHT_VERIFICATION.md`](docs/STAGE3_PREFLIGHT_VERIFICATION.md).
The reviewer's browser procedure:
[`docs/ACCEPTANCE_RUNBOOK.md`](docs/ACCEPTANCE_RUNBOOK.md).

## Application sections

The application opens on **Home**, an entry point built around one real control:
choosing a file stages it for Detect. It does not run the model. Analysis only ever
starts from the explicit *Analyse image* action.

| Page | Purpose |
|---|---|
| **Home** (default) | One dominant surface: the native uploader, whose own control is the page's primary action (selecting a file opens Detect with it ready, without analysing it), with the camera link directly beneath it. Beside it, an unboxed session panel: real counts plus the annotated output of your latest analysis, which reopens that exact result on Detect. Below both, the workflow as one understated line |
| **Detect** | Image on the left (upload, preview, file facts, *Analyse image*), results on the right (*Results* / *Details* / *JSON*), thresholds behind one **Params** popover |
| **Camera** | Browser snapshot → the same pipeline and the same two-panel workspace, one still frame per capture (no live video) |
| **Help** | How it works, what the numbers mean, privacy, honest limitations |
| **Developer** (`/developer`, hidden) | Model resolution, weights paths, runtime availability, setup commands, dataset composition, recorded evaluation metrics, session activity |

### Interface

The interface is an **application frame**, not a dashboard: a dark navigation rail
around a light analysis workspace, with work happening in bordered cards.

- `app/ui/theme.py` — design tokens and one stylesheet. Canvas `#F4F2ED`, cards
  `#FFFFFF`, rail `#1E2122`, ink `#16181A`, secondary ink `#52585C`, rules `#D0CBC1`,
  and one marking colour, ochre `#8A5A00`, which may fill a primary action, draw the
  active rule in the rail, draw a focus ring or outline a detection — never a panel,
  badge or tinted section. Radii are two steps (8px cards, 6px controls), spacing is a
  4px scale, type is seven steps from 12px captions to the 24px page title, and effects
  are limited to focus rings. Rail destinations are set in `#CBD0CC` (≈10:1) with a 3px
  ochre rule and a 10% white wash on the active item.
- `app/ui/components.py` — the primitives: page header, card and card header, unboxed
  panel, fact strip, detection list, empty state, note, steps, flow line, bullets and
  readout. Home uses exactly one bordered surface; supporting content is separated by
  rules and space instead of more cards. Monospace is reserved for data (counts,
  confidences, timings, thresholds, coordinates); prose is never set in it.
- `.streamlit/config.toml` — the same tokens where Streamlit can apply them itself
  (colours, radii, 14px base size, the graphite sidebar), so native cards, buttons,
  tabs and inputs inherit the language instead of being repainted.
- `app/ui/nav.py` — Home, plus grouped *Workspace* (Detect, Camera) and *Guidance*
  (Help) destinations via Streamlit's own `st.navigation`.

Icons are one family only — **Material Symbols Rounded**, which `st.Page(icon=...)`,
`st.button(icon=...)` and `st.popover(icon=...)` render natively. There are no
hand-drawn interface glyphs, and no second icon set anywhere.

The rail carries the wordmark, the destinations, genuine model state (read from the
registry; it never loads weights) and one privacy line. There is no account, avatar or
workspace switcher, because the application has none.

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
