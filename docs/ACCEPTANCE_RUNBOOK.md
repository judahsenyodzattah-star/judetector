# Browser acceptance runbook

A reviewer who has never seen this codebase can execute this document and produce
a defensible record of whether the application works. It is written for the two
tiers in `STAGE3_DEPLOYMENT_READINESS.md`: the local tier (today) and the deployed
tier (after approval). Nothing here authorises deployment.

---

## 0. Preconditions

### Environment

| Item | Local tier | Deployed tier |
|---|---|---|
| Web | `npm run dev` in `web/` → `http://localhost:3000` | Vercel branch URL (Vercel Authentication required) |
| API | `uvicorn api.main:app --port 8000` | Cloud Run `run.app` URL |
| `NEXT_PUBLIC_API_BASE_URL` | unset (same-origin, Next proxy) | `https://<api>.run.app` |
| Environment variable `JUDETECTOR_CORS_ORIGINS` | not needed | exactly the branch URL |

### Test data kit

Prepare these six files in one folder; all are needed and none may be skipped.

| ID | File | Purpose |
|---|---|---|
| D1 | `subject.jpg` — a clear photo of the subject | happy path |
| D2 | `not-subject.jpg` — a photo of someone/something else | negative path |
| D3 | `corrupt.txt` renamed to `corrupt.jpg` | non-image handling |
| D4 | any file larger than 25 MB | size-limit handling |
| D5 | a GIF renamed to `.png` | mismatched-extension handling |
| D6 | a 5000×4000 JPEG | large-dimension handling |

Record the exact byte size of each file; every expectation in this runbook depends
on it. Phone photos are fine, but check that D4 really exceeds 25 MB.

### Browsers

Chrome 140+ desktop, Edge 140+ desktop, Firefox 145+ desktop, Safari 26+ desktop,
Safari on iOS 26, Chrome on Android. Run the **full** script on Chrome; run the
**P1–P4 smoke set** on the rest.

### Recording

Keep one folder per run:
`acceptance/<YYYY-MM-DD>-<tier>-<browser>/` with a `screenshots/` subfolder and a
`log.md`. Screenshot names: `<step-id>-<state>.png`, e.g. `P4-preview.png`.
Measure timings with DevTools (Network tab, "Disable cache", cold reload) or a
stopwatch on the visible transition — never estimate, and do not copy numbers from
any document.

---

## 1. Functional script

### P1 — Home page identity

| Step | Action | Expected |
|---|---|---|
| P1.1 | Open `/` | Heading presents the project as a public educational demonstration |
| P1.2 | Confirm the header and navigation | Links to Detect, Camera, Help are present and reachable |
| P1.3 | Check the model state panel | Says whether the model is available; if not, says so explicitly — **no invented accuracy, no placeholder metric** |
| P1.4 | Check the footer / notice | Privacy statement: images are not stored; developer documentation is separated from the end-user pages |

### P2 — Detect: upload, validate, analyse

| Step | Action | Expected |
|---|---|---|
| P2.1 | Open `/detect` and drop D1 onto the drop zone | File accepted; file name and size displayed |
| P2.2 | Repeat with D4 (>25 MB) | Rejected before upload with a message naming the 25 MB limit; **no request is sent** (confirm in the Network tab) |
| P2.3 | Repeat with D3 (corrupt) | Rejected locally; no request |
| P2.4 | Repeat with D5 (GIF as `.png`) | Either accepted and analysed, or rejected with a message naming the accepted formats — record which, consistently across browsers |
| P2.5 | Repeat with D6 (5000×4000) | Accepted; note the upload duration and whether the UI stays responsive |
| P2.6 | With D1 loaded, press Analyse | Progress indication, then result; timings shown are **measured** values from the response `Server-Timing`, or an explicit "not measured" |
| P2.7 | Inspect the annotated image | Boxes drawn; each detection lists a label and a confidence |
| P2.8 | Press Analyse again with the same file | Works; no stale result from the previous run |
| P2.9 | Press Reset / choose another file | State clears completely; previous result no longer visible |
| P2.10 | Press Analyse with D2 | Expected outcome recorded honestly: either a low-confidence/empty result, or the "no detections" state |
| P2.11 | Keyboard-only pass: Tab to the drop zone, open the picker, choose a file, press Analyse | Every control reachable and operable by keyboard; focus visible at each stop |
| P2.12 | Screen-reader pass (VoiceOver or NVDA) on `/detect` | Result announcement includes the detection count; error messages are announced |

### P3 — Unavailable model

| Step | Action | Expected |
|---|---|---|
| P3.1 | With no weights installed (local) or before weights are deployed | `/v1/health` reports `degraded`; `/v1/detect` returns `503 model_unavailable` |
| P3.2 | Attempt an analysis | Friendly explanation that no model is loaded; **no fake detection, no spinner that never ends** |
| P3.3 | Check `/v1/model` | `metrics` is `null`; the UI does not display an accuracy figure |

### P4 — Camera

| Step | Action | Expected |
|---|---|---|
| P4.1 | Open `/camera` and grant permission | Live preview; capture button enabled |
| P4.2 | Deny permission, reload | Clear explanation and a way to continue without the camera; no crash |
| P4.3 | On a device without a camera (or with it disabled) | Explicit unsupported state |
| P4.4 | Capture a frame, then analyse | Same result presentation as P2.7 |
| P4.5 | Confirm the frame is not retained | Leaving the page and returning shows no previous frame; no image appears in a network payload beyond the analysis request |

### P5 — Help and privacy

| Step | Action | Expected |
|---|---|---|
| P5.1 | Open `/help` | Explains what the tool does, its limits, and that it is educational |
| P5.2 | Check the limitations section | Text matches the model card / project statement — no invented capabilities, no promised accuracy |
| P5.3 | Follow every external link | All resolve; none 404 |

### P6 — Transport and headers

| Step | Action | Expected |
|---|---|---|
| P6.1 | In the Network tab, analyse D1 | Request goes to the API origin directly (deployed tier) or to `/api/detect` on the same origin (local tier) — match the tier, not the other one |
| P6.2 | Inspect the response headers | `X-Request-Id`, `Server-Timing`, `RateLimit-*` present and exposed by CORS |
| P6.3 | From a different origin (a scratch HTML page), attempt a cross-origin `POST /v1/detect` | Blocked by CORS — the browser must not receive the response |
| P6.4 | Trigger the rate limit deliberately (repeat quickly) | `429` with `Retry-After`; the UI explains it in plain language rather than showing a raw error |

### P7 — Error presentation

| Step | Action | Expected |
|---|---|---|
| P7.1 | Disconnect the network and analyse | Clear offline/network message; no stack trace |
| P7.2 | Point `NEXT_PUBLIC_API_BASE_URL` at a dead host and rebuild | The UI reports that it cannot reach the service; nothing hangs forever |
| P7.3 | Any error state | Includes the request id when one exists, so a report can be traced in the logs |

---

## 2. Visual script

Run at six widths — **360, 390, 768, 1024, 1280, 1920** — on `/`, `/detect`,
`/camera`, `/help`.

| Check | Pass condition |
|---|---|
| Layout | No horizontal scrollbar, no overlapping elements, no clipped text at any width |
| Touch targets | Interactive elements ≥ 44 × 44 px on the 360 and 390 widths |
| Typography | Body text ≥ 16 px on mobile; no line longer than ~90 characters on desktop |
| Contrast | Body and controls meet WCAG 2.1 AA (4.5:1 text, 3:1 large text and UI boundaries) — verify with the DevTools contrast checker, record the ratio |
| Focus | Visible focus ring on every interactive element; focus order follows reading order |
| Motion | No animation that cannot be paused or reduced; `prefers-reduced-motion` respected |
| Zoom | 200 % browser zoom at 1280 does not lose content or overlap controls |
| Dark/light | If the OS preference is honoured, both are legible; if not, the interface does not claim to support it |
| Images | Annotated results scale without distortion and keep their aspect ratio |
| Empty/loading/error | Every asynchronous area has all three states designed, none shows a blank box or a spinner without text |

Record one screenshot per page per width: 4 pages × 6 widths = **24 screenshots**.

---

## 3. Defect log

Log every deviation with:

```
ID: D-<n>
Step: P4.2
Browser/width: Safari 26 / 390
Expected: <what the runbook says>
Observed: <what happened, with a screenshot name>
Severity: blocking | major | minor | note
Request id: <if the failure reached the API>
```

Severity definitions:

- **blocking** — a page does not load, analysis cannot complete when a model is
  available, an error is unhandled, a privacy claim is false, or the interface
  shows a fabricated metric.
- **major** — a step fails but a workaround exists, or the layout breaks at a
  supported width.
- **minor** — cosmetic or copy issue with no functional impact.
- **note** — observation or suggestion.

---

## 4. Sign-off

Acceptance passes when all of the following hold:

1. Every P1–P7 step has a recorded result, on every browser in the matrix for at
   least the P1–P4 smoke set.
2. No **blocking** defect is open.
3. The 24 visual screenshots exist and the contrast ratios are recorded.
4. No screen displays a metric that is not backed by a measurement or an
   evaluation record.
5. The privacy statement matches observed behaviour: no image is stored server-side
   and no image survives a page reload.

Outputs to commit or attach: `log.md`, `screenshots/`, and a one-page summary
listing passes, defects and the verdict. Nothing in this runbook may be reported as
complete without the recorded evidence — an untested step is "not tested", not
"passed".

---

## 5. What this runbook cannot establish

- It cannot establish that the model is accurate; that requires an evaluation
  record that does not exist yet.
- It cannot establish production load behaviour; `max-instances=3` and the free
  edge rule are not load-tested here.
- It cannot establish that the edge cannot be bypassed; see §1 of
  `STAGE3_PREFLIGHT_VERIFICATION.md`.
