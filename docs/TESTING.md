# Testing

## Running the suite

```bash
pip install -r requirements-dev.txt
python -m pytest              # everything
python -m pytest -m "not ui"  # skip Streamlit interface tests
python -m pytest -q --no-header -p no:cacheprovider
ruff check .                  # lint
```

No GPU, no PyTorch, no weights and no private images are required. The suite runs
in about two seconds.

## Design

| Layer | Approach |
|---|---|
| Core logic | Pure functions and dataclasses, no Streamlit imports |
| Model | A fake duck-typed model injected through `model_loader` — same code path as the real YOLO call |
| Images | Synthetic Pillow images (blank canvases), so no personal data is involved |
| Interface | `streamlit.testing.v1.AppTest`, each page run as a real Streamlit script |
| Repository rules | Executable checks on `.gitignore`, tracked files and weight/dataset presence |

## What is covered

### Detector contract — `tests/test_detector.py`
- Missing weights ⇒ unavailable, and `load()` raises with an actionable message.
- `predict()` before `load()` raises rather than returning empty boxes.
- Labels come from the model file (`labels_source == "model"`) once loaded; declared
  labels are flagged before that.
- Thresholds are forwarded to the model; out-of-range values rejected.
- Boxes without confidence scores are **rejected**, never defaulted to invented values.
- Unknown class indices fall back to a neutral `class_<n>` label.
- The module imports without Ultralytics installed; the missing-package error names
  `requirements-model.txt`.

### Registry — `tests/test_registry.py`
- The committed `config/models.json` loads and describes the `judah` model honestly
  (single class, subject-specific, not general-purpose).
- Declared dataset facts are intact (711 / 675 / 36; 368 / 203 / 140; totals reconcile).
- Duplicate ids, missing `id`, missing `weights`, empty lists and invalid JSON all fail loudly.
- `JUDETECTOR_MODEL_PATH` overrides only the default model.

### Metrics — `tests/test_metrics.py`
- Missing file ⇒ `None`; the dashboard cannot conjure numbers.
- Present file ⇒ values returned **verbatim**.
- Absent metrics stay absent (no defaulting).
- Percentages (`81.2`) rejected; strings, NaN, empty and malformed records rejected.
- Alias normalisation (`mAP50(B)`, `mAP50-95`); unknown numeric metrics preserved.

### Pipeline — `tests/test_pipeline.py`
- Success returns detections plus an annotated image whose pixels actually changed.
- Missing weights ⇒ `unavailable=True`, no result, no processed image.
- Loader and inference failures are reported, not swallowed.
- Zero detections is a success with an unchanged image.
- The detector is loaded once across repeated calls.

### Rendering, image I/O, stats
- Box drawing preserves size/mode, never mutates the input, survives out-of-bounds
  and inverted coordinates, and clamps to the canvas.
- Decoding rejects empty/non-image/unreadable input; RGBA and greyscale convert to RGB;
  downscaling preserves aspect ratio and honours the guard.
- Session statistics deduplicate identical reruns, cap history, weight mean confidence
  by face count, and count empty runs separately.

### Interface — `tests/test_app_smoke.py`
- The entry point opens Home; every page renders without exception.
- Navigation is exactly Home, Detect, Camera, Help, with SVG (non-emoji) icons and
  Home as the single default route; the developer page is hidden from that list and
  routable at `/developer`.
- The landing page holds one headline, one supporting sentence, one primary button
  (*Analyse an image*) plus a camera page link, an illustration labelled
  "Illustration, not a detection result.", a single line describing the flow and a
  footer with the wordmark, privacy line and a Help link. No marketing vocabulary,
  no second CTA pair, no emoji.
- The illustration is asserted to carry no percentages, counts or confidence
  figures, so no invented output can appear on the landing page.
- Clicking *Analyse an image* lands on a page with a file uploader; the camera page
  link is asserted to be present with its own label.
- Detect exposes an uploader; thresholds live in one collapsed *Advanced settings*
  panel; nothing is analysed until *Analyse image* is pressed.
- **End-to-end:** an uploaded image with a fake model produces `Detections = 2`,
  mean confidence `76.5%`, three displayed images (preview, original, annotated),
  a download button, and a recorded session run.
- **Honesty test:** without weights, pressing *Analyse image* shows
  "Image analysis is temporarily unavailable", **zero** metrics, no download, no
  recorded run and no technical vocabulary. The underlying cause is asserted to be
  present in `session_state["last_analysis_error"]` and on the developer page.
- Developer page shows "No evaluation metrics recorded" and no metric widgets when no
  record exists; a fixture record displays `0.8340 / 0.8100 / 0.7900` verbatim;
  an invalid record raises a visible error.
- Help carries the three-step workflow, the privacy statement and the
  detection-is-not-recognition limitation.

### Icons — inside `tests/test_app_smoke.py`
- Icons exist only on the four navigation entries; Material glyphs may appear in
  `nav.py` and nowhere else (`icon\s*=\s*["']:material/` scan).
- No emoji anywhere in the application source, headings or navigation.

### Styles — `tests/test_ui_styles.py`
- Every text/background token pair meets WCAG AA (4.5:1); the uploader border and
  the illustration outline meet the 3:1 non-text threshold.
- Uploader regression guard: the surface is white both in `.streamlit/config.toml`
  (`secondaryBackgroundColor`, the token Streamlit actually paints the dropzone
  with) and in the dropzone rule, and the label, instructions and browse-button
  colours are each asserted against white rather than against the surface as a
  whole.
- Teal is banned from resting surfaces: any rule using `--jd-accent-tint` must be a
  `:hover` or `:focus` rule. Hover, focus-within and disabled states must exist.
- The type scale is exactly eight steps (0.78–2.75 rem), so an off-scale
  `font-size` fails the build.
- No surface token may have green as its dominant channel.
- Every `data-testid` in the stylesheet is asserted against the installed Streamlit
  bundle, so a Streamlit upgrade that renames a hook fails the suite instead of
  silently dropping styles.
- The root cause of the reported green-surface defect is pinned to the installed
  bundle: the dropzone `<section>` uses `theme.colors.secondaryBg` and its
  instructions use the faded grey token. If Streamlit changes either, the test fails
  rather than the fix silently lapsing.
- `.streamlit/config.toml` colours must match the design tokens.
- The landing illustration is drawn from palette tokens and its outline clears the
  3:1 non-text threshold.

### Repository hygiene — `tests/test_repo_hygiene.py`
- `.gitignore` covers `*.pt`, `*.onnx`, `datasets/`, `runs/`, secrets.
- No weights files and no dataset directories exist in the working tree.
- No binary media or weights are tracked by git.
- `ultralytics` is not a hard requirement of the runtime app.

## Current result

```
192 passed
```

Test counts by module are reported in the pull request. UI tests are marked `ui` and
model-dependent tests would be marked `slow` (none currently require a real model).
