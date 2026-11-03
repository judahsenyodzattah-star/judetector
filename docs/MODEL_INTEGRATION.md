# Connecting a model to JUDEtector

The application is built around a `Detector` interface, so connecting a model is a
**configuration change**, not a code change.

Bash commands are given first in each step; the PowerShell (Windows) equivalent
follows. Both are supported — the application code is platform-independent.

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

PowerShell:

```powershell
$env:JUDETECTOR_MODEL_PATH = "C:\absolute\path\to\best.pt"
```

The override applies to the **default** model in the registry. On Windows, `$env:`
applies to the current terminal window; to persist it, see
[Setting environment variables](#setting-environment-variables).

## 2. Install the ML stack

Inference needs PyTorch + Ultralytics, which are kept out of the default
`requirements.txt` so the UI and test suite stay lightweight:

```bash
pip install -r requirements-model.txt
```

PowerShell:

```powershell
python -m pip install -r requirements-model.txt
```

> PyTorch is a multi-gigabyte download. Allow several minutes and keep a few
> gigabytes of free disk space.

## 3. Restart and verify

```bash
streamlit run app/main.py
```

PowerShell:

```powershell
streamlit run app/main.py
# if 'streamlit' is not recognised:
python -m streamlit run app/main.py
```

The sidebar changes from **⚠️ weights missing** to **✅ weights found**. On the
first detection the model loads once and stays in memory. The class labels shown
in the UI are read **from the model file itself** (`labels_source: model`), not
from configuration — so a model trained with a different class name will display
that name, not a guess.

---

## Windows (PowerShell) walkthrough

A complete first-time setup, from a fresh Windows install to a running app with
detection enabled.

```powershell
# 1. Get the code
git clone https://github.com/judahsenyodzattah-star/judetector.git
Set-Location judetector

# 2. Create and activate a virtual environment
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
# If blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Install the app (no PyTorch yet, so this is small and fast)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4. Confirm the app starts before touching the model
streamlit run app/main.py
#    -> sidebar should read "weights missing". Press Ctrl+C to continue.

# 5. Supply the weights
New-Item -ItemType Directory -Force -Path "models\judah-face-v1" | Out-Null
Copy-Item -Path "C:\path\to\your\best.pt" -Destination "models\judah-face-v1\best.pt"

# 6. Install the optional ML stack
python -m pip install -r requirements-model.txt

# 7. Run again
streamlit run app/main.py
#    -> sidebar should now read "weights found"
```

### Activating the virtual environment

`.\.venv\Scripts\Activate.ps1`

If PowerShell reports that running scripts is disabled, allow them for the current
session only (does not change machine policy):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

To skip activation entirely, call the environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

### Setting environment variables

Session only (current window):

```powershell
$env:JUDETECTOR_MODEL_PATH = "C:\absolute\path\to\best.pt"
$env:JUDETECTOR_REGISTRY   = "C:\absolute\path\to\models.json"
$env:JUDETECTOR_METRICS_DIR = "C:\absolute\path\to\metrics"
```

Verify and remove:

```powershell
$env:JUDETECTOR_MODEL_PATH
Remove-Item Env:JUDETECTOR_MODEL_PATH -ErrorAction SilentlyContinue
```

Persistent (new terminals only — the current window keeps the old environment):

```powershell
setx JUDETECTOR_MODEL_PATH "C:\absolute\path\to\best.pt"
# or, explicit about scope:
[Environment]::SetEnvironmentVariable("JUDETECTOR_MODEL_PATH", "C:\absolute\path\to\best.pt", "User")
# remove it:
[Environment]::SetEnvironmentVariable("JUDETECTOR_MODEL_PATH", $null, "User")
```

### Windows paths in `config/models.json`

JSON treats `\` as an escape character, so a raw Windows path is invalid:

```json
"weights": "C:\models\best.pt"        ← invalid JSON
```

Use forward slashes:

```json
"weights": "C:/models/judah-face-v1/best.pt"
```

…or escape the backslashes:

```json
"weights": "C:\\models\\judah-face-v1\\best.pt"
```

Relative paths (`models/judah-face-v1/best.pt`) resolve against the repository root
and are the simplest option.

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
| `is_general_purpose` | no | Drives the honesty banner; `false` shows the scope warning |
| `declared_labels` | no | Fallback labels, shown as *unverified* until the model loads |
| `dataset` | no | Declared dataset facts for the Dashboard/About pages |
| `provenance` | no | Free-form facts (dataset platform, training status, …) |
| `metrics_file` | no | Evaluation record shown on the Dashboard |

Relative paths resolve against the repository root. Override the whole file with
`JUDETECTOR_REGISTRY=/path/to/models.json`.

On Windows, remember to use `/` or escaped `\\` in any absolute path you add —
see [Windows paths in `config/models.json`](#windows-paths-in-configmodelsjson).

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

```powershell
# the Windows equivalent of step 2
New-Item -ItemType Directory -Force -Path "models\general-face-v1" | Out-Null
Copy-Item -Path "C:\path\to\face-model.pt" -Destination "models\general-face-v1\best.pt"
```

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
from your own run into `metrics/judah-face-v1.json` and the Dashboard shows them
verbatim. Until then it explicitly reports that no metrics are recorded.

Saving result plots alongside the record (Windows):

```powershell
New-Item -ItemType Directory -Force -Path "metrics\curves" | Out-Null
Copy-Item -Path "C:\runs\detect\train\pr_curve.png" -Destination "metrics\curves\pr_curve.png"
```

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

### Windows / PowerShell specific

| Symptom | Cause | Fix |
|---|---|---|
| `Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `python` opens the Microsoft Store or is not recognised | Windows App Execution Alias | use `py -3`, or install Python from python.org and tick **Add python.exe to PATH** |
| `streamlit : The term ... is not recognized` | virtual environment not active | `.\.venv\Scripts\Activate.ps1`, or `python -m streamlit run app/main.py` |
| `Expecting property name enclosed in double quotes` on startup | unescaped `\` in `config/models.json` | use `/` or `\\` in paths |
| `$env:JUDETECTOR_MODEL_PATH` is set but the app ignores it | set with `setx` in the same window | open a new terminal, or set `$env:` for the current one |
| Very long paths fail during install | Windows 260-character path limit | clone to a short path such as `C:\dev\judetector` |
