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
  (*Analyse an image*) plus a camera page link, the same specimen mounted twice
  (*Original* then *Annotated*) with the caption "Illustration, not an actual
  detection result.", the flow as four stations, and a footer with the wordmark,
  privacy line and a Help link. No marketing vocabulary, no second CTA pair, no emoji.
- The two plates are asserted to be byte-identical once the marking rectangle is
  removed, so the annotated plate shows the same specimen plus one outline and
  nothing else. The artwork is asserted to contain no digits at all, so no invented
  score, count or percentage can appear on the landing page.
- Clicking *Analyse an image* lands on a page with a file uploader; the camera page
  link is asserted to be present with its own label.
- Detect exposes an uploader; thresholds live in one collapsed *Advanced settings*
  panel; nothing is analysed until *Analyse image* is pressed.
- **End-to-end:** an uploaded image with a fake model produces a readout of
  `Detections = 2`, mean confidence `76.5%`, confidence range `62.0% – 91.0%` and the
  applied thresholds, three displayed images (uploaded print, original, annotated),
  a download button, and a recorded session run. The readout is asserted twice: on
  the data (`readout_fields(result)`, exact label/value pairs) and on the page text.
- **Honesty test:** without weights, pressing *Analyse image* shows
  "Image analysis is temporarily unavailable", **no readout at all** (no count, no
  confidence), no download, no recorded run and no technical vocabulary. The underlying cause is asserted to be
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
- The marking colour is never a surface: any rule that sets a background to
  `--jd-mark` must be the primary action or its hover state, and the neutral pieces
  (plate, caption, readout, note, section, flow) are asserted to contain no marking
  colour at all. Hover, focus-within and disabled uploader states must exist.
- The marking colour is asserted to be numerically distant from every colour the
  detector draws with, so a reader cannot confuse the page accent with a box.
- The type scale is exactly the nine declared steps, the spacing scale is the
  declared 4–96 px set, and the only radius in the stylesheet is 2px.
- Effects are banned by test: no gradient, filter, backdrop-filter, text-shadow,
  keyframes, transform or transition, and the only `box-shadow` allowed is the focus
  ring.
- No surface token may carry a colour cast (the reported defect was a green one).
- Every `data-testid` in the stylesheet is asserted against the installed Streamlit
  bundle, so a Streamlit upgrade that renames a hook fails the suite instead of
  silently dropping styles.
- The root cause of the reported green-surface defect is pinned to the installed
  bundle: the dropzone `<section>` uses `theme.colors.secondaryBg` and its
  instructions use the faded grey token. If Streamlit changes either, the test fails
  rather than the fix silently lapsing.
- `.streamlit/config.toml` colours must match the design tokens, including the themed
  graphite rail; the active destination is asserted to be *marked* with ochre rather
  than filled with it.
- Rail text and secondary rail text clear WCAG AA against the rail, and the rail is the
  only dark surface.
- Corners use the two-step radius scale (8px cards, 6px controls) and the type scale is
  exactly seven steps.
- The landing specimen is drawn from palette tokens and its outline clears the 3:1
  non-text threshold.
- Phase 5 UI behaviour is covered by `AppTest`: uploading on Home stages an image and
  runs nothing; changing a threshold never calls the model; *Analyse image* is the only
  path to inference; results render as measured tiles, one row per detection, with
  timings taken from `DetectionResult.inference_ms` and a measured total.
- Home is asserted to have exactly one bordered surface in source, no illustration, no
  image before an analysis exists, and no fixed pixel widths; its columns stack in source
  order so the uploader precedes session information on narrow screens.
- The last-result preview is asserted to show only real data (filename, count, measured
  total, annotated output) and to restore the image bytes and the thresholds that
  produced it when reopened.
- Every `icon=` in the pages must be a well-formed `:material/…:` symbol, so a second icon
  family cannot creep in.

### API contract — `tests/test_api_*.py`
- `/v1/health` reports `degraded` with no weights and `ok` with them, and never
  loads weights to answer.
- `/v1/model` states the model's limitations, reports `labels_source` honestly,
  returns recorded metrics verbatim and withholds invalid ones.
- Problem documents are asserted for 404, 405, 422, 500 and 503: stable `type`,
  `request_id`, no paths, no internals, no stack traces.
- Every response is `no-store` with a request id; `/docs` is never available in
  production; CORS is closed unless origins are allowlisted.
- The API process is asserted (in a subprocess) to import no Streamlit.

### Detection endpoint — `tests/test_api_detect*.py`, `tests/test_api_rate_limit.py`
- **Parity:** the same fixture goes through `POST /v1/detect` and through
  `analyse_image` directly, with independent detectors; label, confidence, box,
  count, thresholds and analysed dimensions must match exactly, including the
  zero-detection case and a downscaled image. `box_norm` is asserted to be the
  pixel box divided by the analysed extent — derived, never a second measurement.
- **Validation:** an 8 MB body is rejected from `Content-Length` before parsing;
  a streamed body over 25 MB is rejected while uploading; HEIC/GIF/TIFF are
  `415` whatever the filename claims; a 50 MP image is `413` before decode;
  truncated and empty files are `422`.
- **Unavailable model:** no weights, or weights that fail to load, produce `503`
  with no detections, no confidences, no paths — and no fake "0 detections".
- **Rate limiting:** the sliding window, per-key isolation, refill after the
  window, `429` problem document with `Retry-After`, and `RateLimit-Scope:
  instance` on success. A documentation test asserts `docs/API.md` describes the
  limit as per instance and names the edge dependency, so the docs cannot drift
  into claiming global protection.
- **No leakage:** responses and errors contain no `best.pt`, `models.json`,
  `torch` or `ultralytics` strings.

### Repository hygiene — `tests/test_repo_hygiene.py`
- `.gitignore` covers `*.pt`, `*.onnx`, `datasets/`, `runs/`, secrets.
- No weights files and no dataset directories exist in the working tree.
- No binary media or weights are tracked by git.
- `ultralytics` is not a hard requirement of the runtime app.

## Current result

```
279 passed
```

Test counts by module are reported in the pull request. UI tests are marked `ui` and
model-dependent tests would be marked `slow` (none currently require a real model).
