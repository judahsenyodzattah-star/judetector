# JUDEtector — AI Face Detection System
## Project Proposal (Pre-Implementation)

**Student:** Senyo-Dzattah Judah Agbemavor
**Student ID:** PUIT/23110016
**Programme:** BSc Information Technology, Pentecost University
**Document status:** Proposal for supervisor/student approval — **no implementation has begun**
**Version:** 1.0 · 2 November 2026

---

## 0. Audit of Existing Work (completed before proposing anything)

You asked me to inspect and preserve prior work rather than assume its status. I audited every place prior work could exist. Results:

| Location checked | What was found | Status |
|---|---|---|
| `judahsenyodzattah-star/judetector` (this repo) | Only a 2-line `README.md` ("face detector"). 1 commit, 1 file, no `.gitignore`. | **Empty scaffold** |
| Branches, stashes, tags, full object history of this repo | Only `main` + this working branch at the same commit. No stashes, no tags, no deleted files in history. | **Nothing hidden** |
| All 9 of your GitHub repositories | Found `data-annotation-first-batch` ("face detection", created 26 Oct 2026) — the only face-related repo. | See below |
| `data-annotation-first-batch` contents | 2 files only: `README.md` (a 4.5 KB essay about what data annotation is) and `AI_ML_Practice_Notebook.ipynb` (a beginner AI/ML study workbook). Full history = 3 commits, largest blob 27 KB. | **Documentation only** |
| Same repo, searched for payload | **No images, no `.txt` labels, no `data.yaml`, no `.mat` annotations, no `best.pt`/`.pt` weights, no `runs/` training output, no LFS objects.** Confirmed across the entire git history, not just the working tree. | **No dataset, no annotations, no model** |
| This workspace filesystem | No `.pt`, no `.yaml`, no dataset directories anywhere. | **Nothing local** |
| GPU availability in this environment | `nvidia-smi` absent — **no GPU**. 2 CPU cores, 3.8 GB RAM, 20 GB disk, no ML packages installed. | **Cannot train here** |

### Verdict

The notebook's face-detection content is **explanatory teaching material, not data work**. Section 10 ("Data annotation and object detection (YOLO/Ultralytics)") contains a *hypothetical* example bounding box labelled `# Example only`, a YOLO label-format description, and a training checklist in which **every checkbox is unchecked** (`- [ ] Upload images and draw accurate bounding boxes`, etc.). The README lists "Expected Deliverables" in the future tense.

Therefore, stated plainly:

> **Dataset: does not exist. Annotations: do not exist. Trained model: does not exist. Training runs: none.**

This is not a setback — the workbook is genuinely useful and I will **reuse it** (§2.6): its YOLO label-format explanation, its train/val/test definitions, and its responsible-AI notes (including the correct and important distinction between *face detection* and *face recognition*) become the basis of the dataset card and the ethics section of your final report. It should stay exactly where it is and be referenced, not overwritten.

**One possibility I cannot check from here:** if the "Ultralytics face detection dataset" you remember was created on **Ultralytics HUB** (hub.ultralytics.com) rather than GitHub, it lives in your cloud account, is invisible to me, and **can be exported** (it produces a `data.yaml` plus an images/labels zip). If that dataset exists there, it changes §2 and §3 materially and should be inspected before any new data work — see Decision D1.

---

## 1. Proposed System Architecture

Two strictly separated halves. The **offline pipeline** produces a model; the **online application** only consumes it. This separation is what makes the dashboard honest (it reports frozen test-set numbers, not live guesses) and keeps the web app light enough to run on free CPU hosting.

```
┌───────────────────────── OFFLINE / TRAINING PLANE ─────────────────────────┐
│                                                                            │
│  1. SOURCE              2. PREPARE               3. TRAIN                  │
│  ┌──────────────┐      ┌──────────────────┐     ┌─────────────────────┐    │
│  │ WIDER FACE   │      │ convert .mat →   │     │ Ultralytics YOLO26n │    │
│  │ (or export)  │─────▶│ YOLO .txt labels │────▶│ transfer learning   │    │
│  │ images+annot │      │ seeded 50/30/20  │     │ (Colab T4 GPU)      │    │
│  └──────────────┘      │ split + manifest │     └──────────┬──────────┘    │
│                        └──────────────────┘                │               │
│                                                            ▼               │
│  6. REGISTRY          5. EVALUATE                4. EXPORT                 │
│  ┌──────────────┐     ┌──────────────────┐     ┌─────────────────────┐     │
│  │ best.pt      │◀────│ test split ONCE  │◀────│ best.pt (PyTorch)   │     │
│  │ metrics.json │     │ mAP50, mAP50-95, │     │ best.onnx (CPU)     │     │
│  │ results.csv  │     │ P, R, F1, FPS,   │     │ PR / F1 / CM plots  │     │
│  │ curves/*.png │     │ size-bucket split│     └─────────────────────┘     │
│  └──────┬───────┘     └──────────────────┘                                 │
└─────────┼──────────────────────────────────────────────────────────────────┘
          │  published as GitHub Release asset (weights) + committed metrics
          ▼
┌───────────────────────── ONLINE / APPLICATION PLANE ───────────────────────┐
│                                                                            │
│  Streamlit app (single process, stateless)                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Presentation  │ Detect · Webcam · Dashboard · About                  │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │ Service       │ DetectorService: lazy-load ONNX once per process,     │  │
│  │               │ predict(image, conf, iou) → List[Detection]          │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │ Rendering     │ draw boxes + labels → PIL / NumPy; original vs        │  │
│  │               │ processed side-by-side; per-face table; download      │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │ Metrics       │ reads frozen metrics.json + curves/*.png (read-only)  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component responsibilities

| # | Component | Responsibility | Key technology |
|---|---|---|---|
| 1 | **Dataset acquisition** | Obtain images + ground-truth boxes; record licence and citation | WIDER FACE (or Ultralytics HUB export) |
| 2 | **Dataset builder** | Convert `.mat`/CSV annotations to YOLO `class cx cy w h`; create the 50/30/20 split; write an auditable `split_manifest.csv`; validate every label | Python, NumPy, SciPy/`h5py` |
| 3 | **Trainer** | Fine-tune YOLO26n with transfer learning; log every run's hyperparameters | Ultralytics, PyTorch, Colab GPU |
| 4 | **Exporter** | Emit `best.pt` for provenance and `best.onnx` for fast CPU inference | Ultralytics `export()` |
| 5 | **Evaluator** | Touch the test split **once**; save metrics JSON + standard plots | Ultralytics `val(split='test')` |
| 6 | **Model registry** | Version weights + metrics together so a dashboard number can always be traced to a weight file | GitHub Releases + committed `metrics.json` |
| 7 | **DetectorService** | The only code that touches the model; returns a stable, testable data contract | `ultralytics`, ONNX Runtime |
| 8 | **UI + Dashboard** | Upload, webcam, results, performance reporting | Streamlit |

### The inference data contract (frozen early, so it can be unit-tested)

```python
Detection = {
    "box_xyxy": [x1: float, y1: float, x2: float, y2: float],  # pixels, original image scale
    "confidence": float,                                       # 0.0–1.0
    "class_name": "face",                                      # single class by design
}
# DetectorService.predict(image, conf=0.25, iou=0.45) -> list[Detection]
```

Everything in the UI — the count, the table, the drawing, the export — is derived from this list alone. That single decision is what makes §6's tests possible without a browser.

---

## 2. Dataset Requirements

### 2.1 The hard problem with your 50/30/20 split

Your required split (train 50% / val 30% / test 20%) is unusual — the norm is 70/20/10 or 80/10/10 — and it must be honoured, but it collides with a fact about the leading dataset that must be designed around:

**WIDER FACE's official test split ships without public annotation.** Annotations are published for train and val only; the test split is scored by the benchmark's evaluation server. If you take WIDER FACE's own three folders at face value, you get a "test set" of 16,097 images and **zero labels** — an unmeasurable split that would quietly break your dashboard.

**Solution (recommended):** build the split **yourself** from the *annotated* pool only.

| Source folder | Images | Public annotations |
|---|---|---|
| `WIDER_train` | 12,880 | Yes |
| `WIDER_val` | 3,226 | Yes |
| `WIDER_test` | 16,097 | **No — excluded from this project** |
| **Annotated pool** | **16,106** | Yes |

Re-split that pool 50/30/20 with a fixed seed:

| Split | Share | Images (full pool) | Images (6,000-image tier) | Purpose |
|---|---|---|---|---|
| Train | 50% | 8,053 | 3,000 | Fit weights |
| Val | 30% | 4,832 | 1,800 | Monitor, tune threshold, early stop |
| Test | 20% | 3,221 | 1,200 | Final evaluation, **once** |

> If you were given a split by your lecturer, that split overrides this section. Tell me and I will adapt.

### 2.2 Dataset requirements checklist

| Requirement | Specification |
|---|---|
| Task | Object **detection** (not recognition, not classification) |
| Classes | Exactly **one**: `names: ['face']` → `nc: 1`, class id `0` |
| Label format | One `.txt` per image, one line per face: `0 x_center y_center width height`, all four normalised 0–1 |
| Label/image pairing | Every image has a label file; an image with zero faces gets an **empty** `.txt` (a valid negative), never a missing one |
| Split | 50 / 30 / 20, image-level, fixed seed (42), no image in two splits |
| Leakage control | **Group-aware split.** WIDER FACE is grouped in 61 event classes with many near-duplicate scenes; the split must be made so near-duplicates land on the same side, otherwise test mAP is inflated |
| Reproducibility | `split_manifest.csv` (filename, split, face count, source folder) committed to Git so anyone can rebuild the exact split |
| Minimum viable size | 2,000 images (1,000/600/400) to prove the pipeline end-to-end before scaling up |
| Recommended size | 6,000 images, expandable to the full 16,106 |
| Integrity validation | Script asserts: all boxes within `[0,1]`, `w>0`, `h>0`, no duplicate lines, class id `0` only, zero orphan labels, zero unreadable images |
| Size diversity | WIDER FACE deliberately includes tiny faces; report metrics per size bucket (small / medium / large) rather than one aggregate that hides small-face failure |
| Licence & citation | See 2.3 — must appear in the app's About page and the report's references |
| Privacy & consent | No identifiable private individuals collected without consent; no image of a person used to *identify* them (see 2.5) |

### 2.3 Candidate sources, with the trade-offs stated honestly

| Option | What it is | Licence | Pros | Cons |
|---|---|---|---|---|
| **A. WIDER FACE** *(recommended)* | 32,203 images / 393,703 faces, 61 event classes, CVPR 2016 benchmark | **CC BY-NC-ND 4.0** — academic/non-commercial; **derived copies may not be redistributed** | The standard academic face-detection benchmark; huge variety of scale, pose, occlusion; strong for a project report | 3.68 GB download; MATLAB `.mat` annotations need conversion; **must not be committed to GitHub** |
| **B. Your Ultralytics HUB export** | Whatever you actually built earlier | Yours / platform ToS | Preserves your real prior work; already YOLO-formatted | **Unverified — I could not see it.** Size, class count and split are unknown until you export it |
| **C. Roboflow Universe face sets** | Community datasets, YOLO-ready | Varies per project (often CC BY 4.0) | Zero conversion work; small and fast to download | Quality and annotation consistency vary; must verify the licence of the specific project |
| **D. Own photographs (supplementary)** | 100–200 consented images from classmates/staff | You hold consent | **Directly addresses the fairness gap in 2.4**; original contribution for the report | Needs written consent forms, ethics approval, and your own annotation time |

**Recommendation: A as the training backbone, plus D as a small fairness-evaluation set.** B if the export turns out to be substantial; C only as a fallback if the WIDER FACE download is a blocker.

### 2.4 A fairness point that matters specifically for this project

WIDER FACE was collected in 2015 from web sources skewed toward East Asian and Western faces. Published face-detection research repeatedly shows detector recall dropping on darker skin tones and on faces under strong directional sunlight — both highly relevant to a detector demonstrated at a Ghanaian university. A detector reported as "mAP50 = 0.94" can still perform visibly worse on the faces in the room at your defence.

**Mitigation:** a small, consented local evaluation set (Option D) evaluated **separately** and reported as a distinct row in the dashboard. This converts a weakness into one of the most defensible parts of your dissertation, and it is cheap: ~150 images, one afternoon.

### 2.5 Ethics boundary — stated explicitly so it cannot drift

This system performs **face detection**: it answers *"is there a face here, and where?"* It does **not** perform face recognition (who is this person), and it will not be extended to do so within this project. That boundary — which your own notebook already articulates correctly — belongs in the report, the app's About page, and the consent form.

### 2.6 Reuse of existing work

From `data-annotation-first-batch`, preserved and cited rather than duplicated: the YOLO label-format explanation (notebook §10) → basis of the dataset card; the train/val/test definitions → §2.1 vocabulary; the "do not assume a dataset is ready merely because images have uploaded" checklist → §6 dataset-integrity tests; the detecting-vs-recognising note → §2.5.

---

## 3. Model Training Strategy

### 3.1 Model choice

Ultralytics' current guidance is to start new projects on **YOLO26** (released January 2026), with **YOLO11** as the mature alternative for stable workloads. For a single-class, CPU-served, free-tier-hosted academic project:

| Candidate | Params (approx.) | Why / why not |
|---|---|---|
| **`yolo26n.pt` — primary** | ~2–3 M | Smallest current model; NMS-free end-to-end inference; Ultralytics reports up to ~43% faster CPU inference than the previous generation, which is exactly the constraint here. |
| `yolo11n.pt` — control | ~2.6 M | Mature, very well documented. Train as a **second run** so the report can compare two architectures rather than assert one. |
| `yolo26s.pt` — stretch | ~9–10 M | Higher ceiling, but slower on CPU and longer to train. Only if the nano model visibly under-detects small faces. |

Do **not** train from scratch. Transfer learning from COCO-pretrained weights converges in tens of epochs instead of hundreds, which is the difference between feasible and infeasible on free compute.

> Parameter counts are indicative; quote the exact figures from `model.info()` in the final report.

### 3.2 Compute reality

This workspace has **no GPU** (2 CPU cores, 3.8 GB RAM). Training a detector here is not viable — a single epoch over thousands of 640 px images would take hours.

| Environment | Role | Notes |
|---|---|---|
| **Google Colab (free T4, 16 GB)** | **Primary training** | Session limits and daily GPU quotas apply; checkpoint every few epochs to Google Drive so a disconnect does not lose the run |
| **Kaggle Notebooks (free P100/T4)** | Backup / longer quota | 30 GPU-hrs/week; useful for the full 16k-image run |
| This Arena workspace | Code authoring, label-conversion logic, unit tests, **CPU inference demo** | Cannot train |

### 3.3 Transfer-learning recipe (starting point, to be tuned)

| Hyperparameter | Value | Rationale |
|---|---|---|
| Base weights | `yolo26n.pt` (COCO-pretrained) | Transfer learning |
| `epochs` | 80 (with `patience=20` early stop) | Face detection converges quickly |
| `imgsz` | 640 | Standard; 960/1280 helps small faces at ~2× cost |
| `batch` | 32 (T4), auto-tune on OOM | Adjust to GPU memory |
| `optimizer` | `auto` (SGD/AdamW selection) | Let Ultralytics choose; record what it picked |
| `lr0` | 0.01 | With pretrained weights |
| `mosaic` | 1.0, disabled for final 10 epochs (`close_mosaic=10`) | Mosaic boosts dense/small-face learning; turning it off at the end sharpens final convergence |
| `fliplr` | 0.5 | Faces are roughly bilaterally symmetric |
| `flipud` | 0.0 | Upside-down faces are not a real use case (and hurt) |
| `degrees` | 10 | Head-tilt tolerance |
| `hsv_h / hsv_s / hsv_v` | 0.015 / 0.7 / 0.4 | Skin-tone and lighting variation |
| `scale` | 0.5 | Face-scale variation |
| `seed` | 42 | Reproducibility |
| `device` | `0` (Colab GPU) | — |

**Augmentation guardrail:** aggressive geometric augmentation with `mosaic=1.0` plus heavy rotation can manufacture implausible faces. Keep `degrees` low and `flipud=0`; if val mAP plateaus while train loss keeps falling, reduce augmentation before adding epochs.

### 3.4 Experiment plan (this is what earns marks — not one lucky run)

| Run | Model | Data | Settings | Question answered |
|---|---|---|---|---|
| R0 | `yolo26n` | `A_2000` | 30 epochs | Does the whole pipeline work end-to-end? |
| R1 | `yolo26n` | `A_6000` | 80 epochs | Baseline quality |
| R2 | `yolo11n` | `A_6000` | 80 epochs | Architecture comparison on identical data |
| R3 | best of R1/R2 | `A_6000` | `imgsz=960` | Does higher input resolution recover small faces? |
| R4 | R2 weights | `A_16106` | 80 epochs | Does more data still help? *(only if compute allows)* |
| R5 | winner | + local consented set | evaluate only | Fairness / domain-shift report |

Every run logs: dataset version, split-manifest hash, seed, hyperparameters, `results.csv`, final metrics, and the weight filename. This table is literally the "Reusable experiment log" idea from your notebook, promoted to `experiments/experiments.csv` in the repo.

### 3.5 Evaluation protocol

- The **test split is evaluated exactly once** per candidate, after model selection on val. Selecting on test is the single easiest way to invalidate a student project, and an examiner will ask.
- Report: **mAP50, mAP50-95, Precision, Recall, F1** at the chosen confidence threshold, plus **inference latency (ms/image) and FPS on CPU**, plus precision/recall **per face-size bucket**.
- `metrics.json` is generated by the evaluator script — never typed by hand — and it is the *only* source the dashboard is allowed to read.
- Wise, asking: report your **chosen operating threshold** and justify it (e.g. "conf = 0.35 maximises F1 while keeping false positives per clean background image below 0.2").

---

## 4. Web Application Architecture

### 4.1 Framework decision: Streamlit (recommended)

| Framework | Verdict |
|---|---|
| **Streamlit** | **Recommended.** Pure Python; `st.file_uploader`, `st.camera_input`, `st.metric`, `st.dataframe`, `st.tabs` cover every required feature with no front-end work; first-class free hosting; built-in test harness (`AppTest`) so the UI is testable. |
| Gradio | Viable, slightly nicer media widgets, weaker multi-page dashboard story |
| Flask/FastAPI + HTML/JS | Most "software engineering" credibility, but 3–5× the effort for a page that mostly shows images. **Not recommended** for the remaining scope. |

Model choice + Streamlit + free hosting means this project is deliverable; a bespoke JS front end + custom training pipeline in one semester is a common failure mode.

### 4.2 Page / feature map

| Page | Contents | Requirement satisfied |
|---|---|---|
| **1. Detect** | Upload (JPG/PNG/WEBP, multi-file); confidence slider; IoU slider; **original vs processed side-by-side**; **face count as a headline metric**; **per-face confidence table**; annotated-image download | Core 1, 2, 3, 4, 5, 6 |
| **2. Webcam** | Browser snapshot capture → same detection pipeline | Core 7 *(scoped — see 4.4)* |
| **3. Dashboard** | Frozen test metrics; training curves; PR curve, F1-vs-confidence curve, confusion matrix; latency/FPS; per-size-bucket table; local-set fairness row; model + dataset version | Core 8 |
| **4. About** | Model card: training data, licence, citation, limitations, ethics boundary, student details | Academic rigour |

### 4.3 Key engineering decisions

| Decision | Choice | Reason |
|---|---|---|
| Model loading | `@st.cache_resource` + **lazy** singleton, ONNX Runtime | Streamlit re-runs the script on every interaction; reloading a model per click would make the app feel broken |
| Weight delivery | GitHub Release asset, downloaded+cached at first run (or committed to HF Spaces) | Keeps Git history small; `best.pt` should never be a normal commit |
| Inference runtime | **ONNX** on CPU | Materially faster than PyTorch CPU for the same weights; `best.pt` retained for provenance |
| Image handling | PIL → NumPy → `predict()` → annotate → PIL | Avoids BGR/RGB colour-swap bugs (the classic Streamlit+OpenCV defect) |
| Drawing | `supervision` annotators *or* `results[0].plot()` | Consistent, legible boxes + confidence labels |
| State | `st.session_state` for last result + history | Keeps a session's images downloadable without global state |
| Failure handling | Explicit guards: corrupt file, huge image (downscale > 4000 px), 0 faces found, model missing | A detector that crashes on a blank image is a failed demo |
| Memory guard | Hard cap on upload size; downscale before inference | Prevents OOM kills on free-tier hosting (an OOM kill looks like a random crash to an examiner) |

### 4.4 Webcam — scoped honestly, per your "where technically supported" wording

This is the most commonly over-promised feature on the list, so it is specified precisely:

| Approach | Behaviour | Works deployed? | Verdict |
|---|---|---|---|
| `st.camera_input()` | Browser opens the camera, user clicks to capture **one snapshot**, which is then detected on | **Yes** — over HTTPS, on any device including a phone | **Primary implementation.** Zero extra dependencies. |
| `streamlit-webrtc` | Continuous live video with boxes drawn per frame | Fragile on free hosting — needs HTTPS **and** reachable STUN/TURN servers; resource-heavy; often blocked on Streamlit Community Cloud | **Optional stretch goal**, only after everything else is complete and only if the demo machine is local |
| `cv2.VideoCapture(0)` | Local OpenCV window | **No** — opens the camera attached to the *server*, not the visitor's browser | **Will not be used** |

So: "webcam detection" is delivered as **snapshot-based capture in the browser**, which is genuinely useful for a live demo, with continuous streaming documented as a limitation. That is a defensible scope — and writing it down *now* prevents an uncomfortable question at the viva.

### 4.5 Performance targets (acceptance criteria)

| Metric | Target |
|---|---|
| Detection latency, CPU, 640 px, nano model | ≤ 500 ms typical; ≤ 1.5 s worst case |
| App cold start | ≤ 60 s (incl. model download on first load) |
| Multi-face image | 100 % of faces boxed at conf ≥ 0.25 on clear frontal photos |
| Stability | No unhandled exception on corrupt/large/blank/huge images |
| Dashboard accuracy | Every figure traceable to `metrics.json` + weight filename |

---

## 5. GitHub Repository Structure

```
judetector/
├── README.md                      # Overview, quickstart, screenshots, student details
├── LICENSE                        # MIT for YOUR code (note: Ultralytics is AGPL-3.0)
├── CITATION.cff                   # Machine-readable citation for the project
├── requirements.txt               # Pinned: streamlit, ultralytics, onnxruntime, opencv-python-headless
├── requirements-dev.txt           # pytest, ruff, streamlit AppTest deps
├── .gitignore                     # datasets/, runs/, *.pt, *.onnx, .streamlit/secrets.toml
├── .streamlit/
│   └── config.toml                # Theme, server limits, upload cap
│
├── app/                           # ONLINE plane — what gets deployed
│   ├── main.py                    # Streamlit entry point, navigation
│   ├── pages/
│   │   ├── 1_Detect.py
│   │   ├── 2_Webcam.py
│   │   ├── 3_Dashboard.py
│   │   └── 4_About.py
│   ├── core/
│   │   ├── detector.py             # DetectorService — the ONLY model-touching code
│   │   ├── render.py               # box drawing, side-by-side, colour helpers
│   │   ├── metrics_loader.py       # reads metrics.json, validates schema
│   │   └── config.py               # thresholds, paths, constants
│   └── components/
│       ├── upload_panel.py
│       ├── results_panel.py        # count metric + confidence table
│       └── charts.py
│
├── training/                      # OFFLINE plane — never deployed
│   ├── prepare_widerface.py        # .mat → YOLO .txt conversion
│   ├── make_split.py               # group-aware 50/30/20 + split_manifest.csv
│   ├── validate_dataset.py         # integrity assertions (also used in CI)
│   ├── train.py                    # Ultralytics training entry point
│   ├── evaluate.py                 # test-split eval → metrics.json
│   ├── export.py                   # best.pt → best.onnx
│   ├── data.yaml                   # nc: 1, names: ['face']
│   └── colab/
│       └── train_colab.ipynb       # Runbook: mount Drive, install, train, save
│
├── models/
│   ├── README.md                   # Which weights, version, metrics, download links
│   └── .gitkeep                    # Actual weights live in Releases, NOT here
│
├── metrics/
│   ├── metrics.json                # Frozen test-set results (generated)
│   ├── experiments.csv             # R0–R5 experiment log
│   └── curves/                     # PR curve, F1 curve, results.png, confusion matrix
│
├── data/
│   └── README.md                   # Dataset card: source, licence, split, counts
│                                   # (datasets themselves are git-ignored)
│
├── docs/
│   ├── PROPOSAL.md                 # This document
│   ├── ARCHITECTURE.md             # Diagrams, data contract, sequence notes
│   ├── MODEL_CARD.md               # Intended use, limitations, fairness notes
│   ├── TEST_PLAN.md                # Test case matrix + results
│   ├── DEPLOYMENT.md               # Step-by-step hosting guide
│   └── ETHICS_AND_CONSENT.md       # Consent form template, privacy position
│
├── tests/
│   ├── conftest.py                 # Tiny synthetic fixtures (no real faces needed)
│   ├── test_prepare_labels.py      # .mat → .txt maths, edge cases
│   ├── test_split.py               # 50/30/20 proportions, no overlap, determinism
│   ├── test_dataset_integrity.py   # Box bounds, orphan labels, empty-label validity
│   ├── test_detector.py            # Contract: returns list[Detection], schema valid
│   ├── test_threshold.py           # conf raising → count non-increasing
│   ├── test_render.py              # Box coords, colour order, no out-of-bounds
│   ├── test_metrics_loader.py      # Schema + "no fabricated numbers" guard
│   └── test_app_smoke.py           # Streamlit AppTest: pages load, no exception
│
└── .github/
    └── workflows/
        └── ci.yml                  # ruff + pytest on push/PR; dataset validator
```

### Repository conventions

| Rule | Reason |
|---|---|
| **No images, no weights, no `runs/` in Git** | Keeps the repo fast and stays compliant with WIDER FACE's no-redistribution (CC BY-NC-ND) and ND terms |
| Weights via **GitHub Releases** (`v1.0-model`), referenced by URL in `models/README.md` | Reproducible, versioned, and small in Git |
| `data.yaml` **is** committed; the dataset is not | Config is your work; the dataset is licensed third-party material |
| Conventional commits (`feat:`, `fix:`, `docs:`, `test:`) + meaningful PRs | Evidence of process for assessment |
| **Branch strategy:** `main` protected; each feature on `feat/…`, merged by PR | Shows version-control discipline; also how this session's branch works |
| Tag each milestone (`v0.1-dataset`, `v0.2-model`, `v1.0-app`) | Reconstructable history for the report |
| `README.md` carries screenshots + a 3-command quickstart | First thing an examiner or marker opens |

---

## 6. Testing Strategy

Four layers, weighted toward what is cheap and automatic on a machine with no GPU.

### 6.1 Layer 1 — Unit tests (`pytest`, fast, no model needed)

| # | Test | Assertion |
|---|---|---|
| U1 | `.mat` → YOLO conversion | A known box (pixels) becomes the correct normalised `cx cy w h`; a hand-computed case must match to 1e-6 |
| U2 | Conversion edge cases | Box touching the border; 1×1 px box; face on the image edge → clamped, never negative or >1 |
| U3 | Split ratios | Exactly 50/30/20 ± 1 image; the three sets are disjoint; the union equals the pool |
| U4 | Split determinism | Same seed ⇒ byte-identical `split_manifest.csv` |
| U5 | Group leakage | No event group appears in two splits |
| U6 | Label integrity | `w>0`, `h>0`, `0 ≤ cx,cy ≤ 1`, one class only, no duplicate lines |
| U7 | Pairing | Every image has a label file; empty labels are valid; orphan labels are flagged |
| U8 | Detection contract | `predict()` returns `list[Detection]` with all keys, correct types, `0 ≤ conf ≤ 1` |
| U9 | Threshold monotonicity | Raising `conf` never increases the face count |
| U10 | Render safety | Boxes drawn for a 0-detection image; coordinates never out of bounds; RGB not BGR (skin-tone assertion on a synthetic patch) |
| U11 | Metrics guard | `metrics_loader` raises on missing keys; the dashboard cannot invent values |

### 6.2 Layer 2 — Integration / model tests (marked `slow`, run on push to `main`)

| # | Test | Assertion |
|---|---|---|
| I1 | Weight loads | `best.onnx` opens; the model reports `nc == 1`, `names == {0: 'face'}` |
| I2 | Golden-image regression | 5 fixed images with known face counts → counts within ±1 and mAP-style IoU ≥ 0.5 vs stored expectations |
| I3 | Latency budget | 640 px CPU inference < 1.5 s (fails loudly if a change makes the app unusable) |
| I4 | Robustness | Grayscale, CMYK, RGBA, 12 MP, 1×1 px, and text-file-disguised-as-JPEG inputs all handled without an unhandled exception |
| I5 | Zero-face image | A landscape photo returns 0 detections and a graceful "no faces detected" message |

### 6.3 Layer 3 — UI tests (`streamlit.testing.v1.AppTest`, no browser)

| # | Test | Assertion |
|---|---|---|
| S1 | Every page loads | `AppTest.from_file("app/main.py")` runs with `run()` → `at.exception` is empty |
| S2 | Widgets exist | Uploader, confidence slider, metric placeholders present |
| S3 | Slider interaction | Changing confidence re-runs without error; the displayed count changes consistently |
| S4 | Dashboard renders | Metrics file present ⇒ tabs/graphs appear; missing file ⇒ friendly error, not a traceback |

### 6.4 Layer 4 — Model evaluation & acceptance (the academic core)

This is not unit testing — it is the evidence for your results chapter.

| Check | Method | Pass criterion |
|---|---|---|
| Test-set performance | `evaluate.py` on the frozen 20% | Report actual values; target **mAP50 ≥ 0.90** (WIDER FACE is genuinely hard at strict IoU) |
| Precision / Recall / F1 | `val()` at the chosen threshold | Prefer **recall ≥ 0.90** — a missed face is the visible failure |
| Small-face behaviour | Metrics per size bucket | Documented, even if weak; that *is* a finding |
| Threshold selection | Sweep conf 0.05→0.95, plot F1 | Chosen operating point justified with the curve, not a guess |
| Cross-dataset honesty | Evaluate on the consented local set (D) | Reported separately, with the gap explained |
| Reproducibility | Re-run R1 from a clean environment | Same metrics ± small tolerance |
| Manual UAT matrix | 8 images × {single, group, backlit, dark, occluded, rotated, tiny, no-face} | Documented pass/fail, screenshots in `docs/TEST_PLAN.md` |

### 6.5 CI (GitHub Actions)

`ruff` lint → `pytest -m "not slow"` → dataset validator (on fixture data) → on tag, collect artifacts. Golden-image and latency tests run on `main` only, so pull requests stay fast. **Note:** no real faces are committed as test fixtures — synthetic shapes plus a handful of licence-clean images only.

---

## 7. Deployment Strategy

### 7.1 Primary: Streamlit Community Cloud (recommended)

| Aspect | Detail |
|---|---|
| How | Point Streamlit Cloud at this repo, branch `main`, entry point `app/main.py` |
| Why | Free, HTTPS by default (required for `st.camera_input`), GitHub-integrated auto-deploy, custom subdomain, zero server administration |
| Weight delivery | `app/core/detector.py` downloads the ONNX from the GitHub Release on first run and caches it; Streamlit secrets hold any tokens |
| Constraints | CPU-only, ~1 GB memory class, sleeps after inactivity (cold start ~30–60 s). Mitigations: ONNX nano model, downscale uploads, lazy load, a "first load may take a moment" notice |
| Cost | £0 |

### 7.2 Alternative: Hugging Face Spaces (Docker)

Preferable if the torch/onnxruntime dependency set proves too heavy for Streamlit Cloud, or if you want the weights co-located with the app. Slightly more setup (Dockerfile), more generous CPU, still free, still HTTPS. Documented as the fallback in `docs/DEPLOYMENT.md`.

### 7.3 Local / offline mode — **not optional**

`streamlit run app/main.py` with a locally cached model must work with **no internet**. Your defence may have unreliable campus Wi-Fi; a demo that needs a cold-starting free-tier app is a demo that can fail in front of an examiner. Include a one-command `run_local.sh`.

### 7.4 Deployment pipeline

```
feature branch → PR → CI (lint + unit + UI tests) → merge to main
      → Streamlit Cloud auto-redeploy → smoke-check live URL
      → tag vX.Y → publish weights + metrics as Release → update models/README.md
```

### 7.5 Operational notes for the report

Environment pinned in `requirements.txt`; model version displayed in the app footer (`model yolo26n-v1 · mAP50 0.9x · test split 2026-02`); a simple `/health`-style "model loaded" badge; basic latency logging to the console. That set of small touches reads as production awareness without over-engineering.

---

## 8. Identified Risks, Assumptions and Missing Resources

### 8.1 Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R1** | **The "existing dataset" does not exist as remembered** — it is not on GitHub or in this workspace | **Confirmed** | High (schedule) | Resolved by this audit: dataset work starts from zero. Check Ultralytics HUB for an export **before** starting (D1) |
| **R2** | No local GPU; free Colab quotas/session limits kill runs | High | High | Train on `A_2000` first for a fast win; checkpoint to Drive every 5 epochs; Kaggle as backup; cap the ambition at 6,000 images |
| **R3** | WIDER FACE **test split has no public annotations** — the naive split is unmeasurable | Certain | High | Build our own 50/30/20 split from the annotated train+val pool (§2.1) |
| **R4** | Licence breach: committing the dataset violates CC BY-NC-ND; **ND** also restricts redistributing derived (converted) versions | Medium | High (academic misconduct) | `datasets/` git-ignored; ship *conversion scripts*, not converted data; licence cited in the About page, the dataset card and the report |
| **R5** | Near-duplicate leakage across splits inflates test mAP | Medium | High (invalid results) | Group-aware split by WIDER event class + a leakage unit test (U5) |
| **R6** | Domain shift / fairness: recall drops on darker skin tones and harsh sunlight relative to the WIDER benchmark | Medium–High | Medium (credibility) | Consented local evaluation set; report the gap honestly; tune the threshold toward recall |
| **R7** | Webcam expectations exceed what free hosting allows (live streaming) | High | Medium | Snapshot-based `st.camera_input` delivered; live WebRTC explicitly documented as out of scope (§4.4) |
| **R8** | Free-tier CPU is slow or OOMs on large phone photos | Medium | Medium | ONNX nano model, downscale > 4000 px, upload size cap, latency test I3 |
| **R9** | Annotation conversion bug silently corrupts boxes | Medium | High | Hand-computed conversion tests (U1, U2), visual overlay spot-check of 20 random labels, dataset validator in CI |
| **R10** | Scope creep (recognition, tracking, live video, mobile app) | High | High | The §4.2 feature map **is** the scope; anything else is post-submission |
| **R11** | Ultralytics is **AGPL-3.0** — relevant if the code is ever used commercially or kept closed | Low (academic) | Low–Medium | Publish under an open licence (consistent with AGPL); note it in the report; option of an Ultralytics Enterprise licence if ever commercialised |
| **R12** | Single-student bus factor / lost work | Medium | High | Everything in Git; weights in Releases; Colab runbook written for a stranger to re-run; regular pushes |

### 8.2 Assumptions

1. You hold (or can create) a **Google account** for Colab and a **GitHub** account for hosting — GitHub is connected.
2. **Streamlit or an equivalent Python framework is acceptable** to your supervisor (your brief allows it).
3. Dataset choice and licence are acceptable for coursework — **supervisor confirmation recommended** (D2).
4. The 50/30/20 split is a hard requirement, not a suggestion.
5. Evaluation is CPU-only, single image, batch size 1 — not a real-time video product.
6. Webcam = browser snapshot capture (§4.4), and "where technically supported" permits this scope.

### 8.3 Missing resources — the concrete blockers

| # | Missing | Blocks | Who resolves |
|---|---|---|---|
| M1 | **A dataset** — none exists, anywhere I can see | Everything downstream | Student (Decision D1/D2) |
| M2 | **GPU compute** + a Colab/Kaggle account | Training | Student |
| M3 | **~4 GB local/Drive space** for the WIDER FACE download (3.68 GB) + converted output | Download & conversion | Student |
| M4 | **Ultralytics HUB dataset export** (if it exists) | Might replace M1 entirely | Student |
| M5 | **Supervisor sign-off on dataset licence & ethics position** | Academic compliance | Supervisor |
| M6 | **Written consent forms** for any locally photographed faces | Local fairness set (D) | Student + supervisor |
| M7 | **Hosting account** (Streamlit Cloud / HF Spaces) | Deployed URL for submission | Student |
| M8 | **Report template / marking rubric** | Structuring the dissertation chapters | Supervisor |
| M9 | **Defence date / submission deadline** | Timeline realism (§9) | Student |

### 8.4 Timeline (indicative — anchors to your deadline)

| Phase | Work | Est. duration |
|---|---|---|
| 0 | Approve this proposal; resolve D1–D5; confirm licence | 2–3 days |
| 1 | Acquire dataset; write converter + split + validator; **dataset card** | 4–6 days |
| 2 | R0 smoke run (2,000 imgs) on Colab; fix the pipeline | 2–3 days |
| 3 | R1/R2 full runs (6,000 imgs); evaluate; pick the winner | 5–7 days |
| 4 | Export ONNX; build `DetectorService` + unit tests | 4–5 days |
| 5 | Streamlit UI (Detect, Webcam) + UI tests | 5–7 days |
| 6 | Dashboard + model card; deploy to Streamlit Cloud | 3–4 days |
| 7 | Optional R3/R4 runs; local fairness set | 3–5 days |
| 8 | UAT matrix, docs, screenshots, report write-up, rehearsal | 5–7 days |
| — | **Total** | **~5–7 weeks part-time** |

---

## 9. Decisions Needed Before Implementation

| ID | Question | Options | My recommendation |
|---|---|---|---|
| **D1** | Can you **export the dataset from Ultralytics HUB** (or otherwise share what you built earlier)? | (a) Yes, here's the export · (b) No, it's gone · (c) Never existed | **(a)** if possible — it preserves real prior work. Otherwise treat the dataset as starting from zero |
| **D2** | Dataset source | (a) WIDER FACE · (b) HUB export · (c) Roboflow YOLO set · (d) Own photos | **(a)** + a small consented local set (d) |
| **D3** | Training scale | (a) 2,000 imgs (fast, safe) · (b) 6,000 (balance) · (c) full 16,106 | **(b)** — start at (a) for R0, then scale to (b) |
| **D4** | Model family | (a) YOLO26n only · (b) YOLO26n **and** YOLO11n for comparison | **(b)** — the comparison is cheap marks |
| **D5** | Webcam scope | (a) Snapshot capture only · (b) Snapshot + attempt live WebRTC | **(a)**, with (b) as a documented stretch goal |
| **D6** | Framework | (a) Streamlit · (b) Gradio · (c) Flask/FastAPI | **(a)** |

---

## 10. Deliverables (what "done" looks like)

1. A reproducible `training/` pipeline: `.mat` → YOLO labels → seeded 50/30/20 split → trained weights → `metrics.json`.
2. A deployed, publicly reachable Streamlit app satisfying features 1–8, with a working local mode.
3. A performance dashboard whose every number traces to a versioned weight file.
4. A test suite (≥ 25 automated tests) plus a documented UAT matrix.
5. A model card, dataset card, ethics/consent note, and experiment log.
6. A Git history that evidences the process: branches, PRs, tags, CI.

---

**Status: awaiting your approval.** No code, dataset, or configuration will be created until you confirm — and until D1–D6 are answered, since D1/D2 change the dataset chapter and D3/D4 change the training plan.
