# Connecting a model to JUDEtector

The application is built around a `Detector` interface, so connecting a model is a
**configuration change**, not a code change.

---

## 1. Supply the weights

Copy your trained Ultralytics checkpoint to:

```
models/judah-face-v1/best.pt
```

…or keep it anywhere else and point the app at it:

```bash
export JUDETECTOR_MODEL_PATH=/absolute/path/to/best.pt
```

The override applies to the **default** model in the registry.

## 2. Install the ML stack

Inference needs PyTorch + Ultralytics, which are kept out of the default
`requirements.txt` so the UI and test suite stay lightweight:

```bash
pip install -r requirements-model.txt
```

## 3. Restart and verify

```bash
streamlit run app/main.py
```

The sidebar changes from **⚠️ weights missing** to **✅ weights found**. On the
first detection the model loads once and stays in memory. The class labels shown
in the UI are read **from the model file itself** (`labels_source: model`), not
from configuration — so a model trained with a different class name will display
that name, not a guess.

---

## Registry reference — `config/models.json`

```json
{
  "schema_version": 1,
  "default_model_id": "judah-face-v1",
  "models": [
    {
      "id": "judah-face-v1",
      "display_name": "JUDEtector — judah model (v1)",
      "enabled": true,
      "kind": "subject_specific",
      "is_general_purpose": false,
      "weights": "models/judah-face-v1/best.pt",
      "declared_labels": ["judah"],
      "task": "detect",
      "description": "…",
      "provenance": { "dataset_name": "judy-face-detection", "…": "…" },
      "dataset": {
        "total_images": 711,
        "annotated_images": 675,
        "unannotated_reserved": 36,
        "classes": ["judah"],
        "split": { "train": 368, "val": 203, "test": 140 }
      },
      "metrics_file": "metrics/judah-face-v1.json"
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique identifier used in URLs, metrics filenames and stats |
| `display_name` | no | Human-readable name shown in the UI |
| `weights` | yes | Path to `.pt` (relative to repo root, or absolute) |
| `enabled` | no | `false` hides the model from the selector (default `true`) |
| `kind` | no | `subject_specific` or `general_purpose` |
| `is_general_purpose` | no | `false` marks the model subject-specific in Help and the developer page |
| `declared_labels` | no | Fallback labels, shown as *unverified* until the model loads |
| `dataset` | no | Declared dataset facts, shown on the developer page |
| `provenance` | no | Free-form facts (dataset platform, training status, …) |
| `metrics_file` | no | Evaluation record shown verbatim on the developer page |

Relative paths resolve against the repository root. Override the whole file with
`JUDETECTOR_REGISTRY=/path/to/models.json`.

---

## Swapping in a general-purpose face detector later

The current model is **subject-specific** (single class `judah`). To add a real
face detector:

1. Train or obtain a face model with a single `face` class.
2. Put the weights at `models/general-face-v1/best.pt`.
3. In `config/models.json`, edit the `general-face-v1` entry and set
   `"enabled": true`. Optionally make it the default by changing
   `default_model_id`.
4. Restart. The model selector appears automatically because more than one model
   is enabled, and the scope warning disappears for that model because
   `is_general_purpose` is `true`.

**No view code changes.** The views only ever see `spec.id`, `spec.display_name`,
`spec.declared_labels` and a `Detector`.

### Adding a non-Ultralytics backend

Implement the `Detector` interface in `app/core/detector.py`
(`is_available`, `is_ready`, `load`, `predict`, `labels`, `labels_source`) and
return it from `build_detector()` in `app/core/registry.py`. ONNX Runtime, RT-DETR
or a hosted API would all plug in the same way.

---

## Recording evaluation metrics

See [`metrics/README.md`](../metrics/README.md). Short version: copy the numbers
from your own run into `metrics/judah-face-v1.json` and the developer page (`/developer`)
shows them verbatim. Until then it explicitly reports that no metrics are recorded.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| *weights missing* despite the file existing | relative path resolved elsewhere | use an absolute path or `JUDETECTOR_MODEL_PATH` |
| *The 'ultralytics' package is not installed* | ML stack missing | `pip install -r requirements-model.txt` |
| *Failed to load weights …* | corrupt/incompatible checkpoint | re-export `best.pt`; check the Ultralytics version |
| Sidebar still shows an old model | cached detector | click **Clear cached model** in the sidebar |
| Labels look wrong | model file itself defines them | check `model.names`; the UI reports the true source |
| Metrics record rejected | values outside `[0, 1]` | use ratios, not percentages |
