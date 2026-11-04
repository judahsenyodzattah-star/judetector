# Stage 3 — deployment readiness

Status: **prepared for approval. Nothing has been deployed, provisioned or enabled.**
Billing is not enabled, no Vercel project exists, no Cloud Run service exists, and
PR #3 is still open.

This document is the plan a reviewer can approve or amend. Every price and limit
below was read from the vendor's own page on **2026-11-04**; every number that
could not be established from this environment is labelled as such rather than
estimated into a fact.

Sources used for limits and prices:

- Cloud Run pricing — `cloud.google.com/run/pricing`
- Cloud Run quotas and limits — `cloud.google.com/run/quotas`
- Cloud Run maximum instances — `cloud.google.com/run/docs/configuring/max-instances`
- Cloud Run concurrency — `cloud.google.com/run/docs/about-concurrency`
- Cloud Load Balancing pricing — `cloud.google.com/load-balancing/pricing`
- Cloud Armor pricing — `cloud.google.com/armor/pricing`
- Artifact Registry pricing — `cloud.google.com/artifact-registry/pricing`
- Vercel pricing — `vercel.com/pricing`
- Vercel Functions limits — `vercel.com/docs/functions/limitations`

---

## 0. Decisions needed before anything is provisioned

| # | Decision | Recommendation |
|---|---|---|
| D1 | **Merge PR #3 or deploy a branch?** Production deployments read from a production branch. `main` does not contain `web/` yet. | Merge PR #3 after review, then deploy `main`. Branch-only deployment is possible but is not a production procedure. |
| D2 | Vercel plan | **Pro ($20/month per deploying seat, including $20 usage credit)** — Hobby is for personal, non-commercial projects. |
| D3 | Public hostnames | `app.<domain>` on Vercel and `api.<domain>` on Cloud Run (custom domain map). The exact web origin goes into `JUDETECTOR_CORS_ORIGINS`. |
| D4 | Warm start | **Start with `min-instances=0`** (scale to zero, $0 idle). Move to 1 only if measured cold start hurts, at ≈$19.71/month. |
| D5 | Abuse protection tier | **Cloudflare in front of the API** (free plan: 1 rate-limit rule, 10 s window; Pro adds rules and longer windows). Cloud Armor + load balancer is the GCP-native alternative at ≈$24.25/month before request charges. |
| D6 | Model weights source | **The author's `best.pt` only.** No substitute, no retrain, no synthetic model on a public deployment. If weights are unavailable, publish the honest degraded state instead. |
| D7 | Budget ceiling | **$25/month** with alerts at 50 % / 90 % / 100 %, Cloud Run `max-instances=3`, and a documented kill switch. |
| D8 | Bot challenge | Deferred. Turnstile/reCAPTCHA would require a contract addition (a token to verify), so it is a separate approval. |

---

## 1. Current Next.js application and visual readiness

### What exists and is proven

| Area | Evidence |
|---|---|
| Routes | `/`, `/detect`, `/camera`, `/help`, plus `/api/detect` (local-development proxy only) |
| Server rendering | All four pages render `200` server-side with the API up *and* with it down (build succeeds with no API reachable) |
| Design tokens | One stylesheet, `web/app/globals.css`, 913 lines, 12.9 KiB raw |
| Measured contrast | body 15.8:1 · secondary 6.4:1 · captions 4.7:1 · rail 10.4:1 · rail accent 6.1:1 · primary button 5.0:1 · links 6.7:1 · error text 6.0:1 (all computed from the actual token values) |
| Responsive rules | Rail ≥1024 px; top bar 640–1023 px; single column <640 px. The ranges are mutually exclusive and asserted in `tests/guardrails.test.ts` |
| Navigation | One nav element per breakpoint, one `aria-current`, nested routes resolve to their section |
| Assets | 620.9 KiB raw static JS+CSS; **187.4 KiB JS gzipped**; homepage HTML 15,074 B raw, 4,806 B gzipped |
| Accessibility basics | Focus-visible rings on every control, labelled file input, `role="alert"` errors, `aria-pressed` view toggle, reduced-motion support, skip link |

### What has **not** been verified

There is no browser in this environment, and no screenshot has been taken. The
layout is verified through server-rendered HTML, CSS rules and `matchMedia`-driven
component tests — not through a rendered page. **Anything below is a checklist for
your eyes, not a claim.**

### Reviewer checklist at fixed widths

| Width | Check |
|---|---|
| 360 px | Uploader button reaches full width; detection rows reflow so the pixel box occupies its own line; definition list stacks; no horizontal scroll |
| 390 px (iPhone 14) | Same, plus sticky-safe top bar; long filenames wrap rather than overflow |
| 768 px | Top bar with four destinations in one row; single-column split; cards keep 24 px gutters |
| 1024 px | Rail appears; 1fr / 320 px split; rail footer status visible without scrolling |
| 1440 px | Content capped at 1120 px and centred; no stretched cards |
| 1920 px | Same cap, generous margins; nothing floats oddly |

Also worth checking by eye: overlay alignment on a portrait and a landscape image
(boxes must sit on the subject at every width), the annotated-PNG view, both
downloads, keyboard-only traversal of Home → Detect → Analyse, and 200 % browser
zoom.

### Known visual risks (stated up front)

1. `position: sticky` on a `100vh` rail can clip on short laptop viewports with browser chrome — verify at 1280×720.
2. Very long filenames rely on `overflow-wrap: anywhere`; check a 120-character name.
3. With no weights, the preview shows the unavailable state everywhere. The results view cannot be reviewed against a live model yet (see §6).
4. iOS Safari renders `100vh` differently; the rail is hidden at that width, so this should be benign, but confirm.

---

## 2. Exact Vercel configuration

### Project

| Setting | Value |
|---|---|
| Repository | `judahsenyodzattah-star/judetector` |
| **Root Directory** | `web` |
| Framework preset | Next.js (auto-detected) |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Output | Next.js default (`.next`) |
| Node.js version | 22.x |
| Production branch | `main` (see D1) |
| Preview deployments | Enabled for all other branches |
| Region | `iad1` (single region; functions are only used for SSR) |
| Deployment protection | Vercel Authentication **off for production**, on for previews |

No `vercel.json` is required. The one rule that matters — that detection uploads
never traverse a Vercel Function — is enforced in application code
(`lib/api.ts`), not by platform config, and is covered by
`web/tests/transport.test.ts`.

### Environment variables

| Name | Environments | Value | Why |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Production, Preview | `https://api.<domain>` | Switches detection to the direct transport. **Without it the app falls back to the local proxy and 25 MB uploads would fail on Vercel.** |
| `API_INTERNAL_URL` | Production, Preview | `https://api.<domain>` | Server-side health/model-card reads for first paint |
| `NEXT_PUBLIC_DETECT_TRANSPORT` | *unset* | — | Leave unset; the presence of the base URL already selects `direct` |

`NEXT_PUBLIC_*` values are inlined at build time, so changing them requires a
redeploy. `API_INTERNAL_URL` is read at request time.

### Cross-origin consequence

Vercel preview URLs are unique per deployment (`<project>-<hash>.vercel.app`), so
they cannot all be allowlisted in `JUDETECTOR_CORS_ORIGINS` without weakening the
allowlist. Plan: **the production hostname is allowlisted; previews show the
"status unknown"/error path rather than being silently permitted.** If preview
analysis is needed later, it gets its own API origin, not a wildcard.

### Cost posture on Vercel

Hobby: $0, with 1M CDN requests, 100 GB fast data transfer and 1M function
invocations per month included, and Vercel's firewall rate limiting at 1M allowed
requests/month. Pro: **$20/month** including a $20 usage credit, Flat Rate CDN,
and spend management. Traffic here is almost entirely static + SSR on small
payloads; the 25 MB bodies never touch Vercel.

---

## 3. Proposed Google Cloud Run configuration

All sizing values are **starting points to be replaced by measurement** (§6).
Nothing is deployed.

| Setting | Proposed value | Rationale |
|---|---|---|
| Region | `us-central1` | Tier-1 pricing; Vercel `iad1` is close enough for an API call |
| Image | `us-central1-docker.pkg.dev/<project>/judetector/api@sha256:<digest>` | Digest, not tag, so a rollback is unambiguous |
| CPU | 1 vCPU | CPU inference; measure before raising |
| Memory | 2 GiB | Torch CPU runtime + model + image buffers; raise to 4 GiB if OOM |
| Concurrency | 4 (explicit, below the default 80) | Inference is CPU-bound; 4 prevents queueing behind one instance from turning into timeouts |
| Min instances | 0 | Scale to zero; no idle cost |
| Max instances | **3** | Google's own suggested cost safeguard; caps a burst at ≈$0.31/hour saturated |
| Request timeout | 120 s | Comfortably above a 25 MB upload over a slow connection (40 s at 5 Mbps) and model load |
| Startup CPU boost | On | Shortens the cold start that includes loading weights |
| Startup probe | HTTP `GET /v1/health`, `initialDelaySeconds 10`, `periodSeconds 5`, `failureThreshold 24` | Gives model load up to ~2 minutes |
| Liveness | None (avoid restart loops while weights load) | |
| HTTP/2 | Not needed | Largest request is 25 MB + 256 KiB ≈ 25.3 MB, inside the 32 MiB HTTP/1 request limit |
| Service account | `judetector-api@<project>` with `roles/storage.objectViewer` on the weights bucket only | Least privilege |
| Ingress | `all` if Cloudflare proxies; `internal-and-cloud-load-balancing` if Cloud Armor is chosen | Depends on D5 |

### Environment variables on Cloud Run

| Name | Value |
|---|---|
| `JUDETECTOR_ENV` | `production` (disables `/docs`) |
| `JUDETECTOR_MODEL_PATH` | `/models/judah-face-v1/best.pt` |
| `JUDETECTOR_CORS_ORIGINS` | `https://app.<domain>` (exact, no wildcard) |
| `JUDETECTOR_RATE_LIMIT_PER_MINUTE` | `30` |
| `JUDETECTOR_RATE_LIMIT_BACKEND` | `none` **if** Cloudflare/Cloud Armor enforces the quota, otherwise `memory` |
| `JUDETECTOR_TRUST_PROXY` | `true` only when a trusted proxy sets `X-Forwarded-For` (Cloudflare/Cloud Armor); otherwise `false` |
| `PORT` | `8080` |

### Model-weight loading (three options)

| Option | How | Trade-off |
|---|---|---|
| **A. Cloud Storage FUSE mount (recommended)** | `--add-volume name=models,type=cloud-storage,bucket=<bucket>,readonly=true` + `--add-volume-mount volume=models,mount-path=/models` | Weights stay out of the image; new weights need no rebuild. Costs cold-start read time and some instance memory for the FUSE buffer |
| B. Bake into the image | Copy weights at build time | Fastest cold start, but violates the repo rule that weights are never baked in, and makes every weight update a full rebuild |
| C. Download at startup | Fetch from a signed URL into `/tmp` | Same effect as A with more moving parts and a secret to manage |

The image itself must change: the current `Dockerfile` installs
`requirements-api.txt` only, so it starts and reports `degraded` by design. Real
inference needs `requirements-model.txt` (torch CPU wheel is **539.1 MB**,
uploaded to Artifact Registry; image will be ~1.5 GiB+, so first pull on a new
instance takes longer). Proposed: a build argument
`--build-arg INSTALL_MODEL=true` that adds the ML layer, keeping the current fast
CI build for the api-only image.

### Deployment commands (documented, **not run**)

```bash
# 1. Build and push the inference image
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT/judetector/api:$GIT_SHA \
  --substitutions=_INSTALL_MODEL=true

# 2. Deploy with the settings above
gcloud run deploy judetector-api \
  --image us-central1-docker.pkg.dev/$PROJECT/judetector/api:$GIT_SHA \
  --region us-central1 --cpu 1 --memory 2Gi --concurrency 4 \
  --min-instances 0 --max-instances 3 --timeout 120 --cpu-boost \
  --set-env-vars JUDETECTOR_ENV=production,JUDETECTOR_MODEL_PATH=/models/judah-face-v1/best.pt,JUDETECTOR_CORS_ORIGINS=https://app.example.com \
  --add-volume name=models,type=cloud-storage,bucket=$BUCKET,readonly=true \
  --add-volume-mount volume=models,mount-path=/models \
  --service-account judetector-api@$PROJECT.iam.gserviceaccount.com \
  --allow-unauthenticated
```

---

## 4. Expected costs and safeguards

### Unit prices used (us-central1, request-based, verified 2026-11-04)

| Meter | Price |
|---|---|
| CPU, active | $0.000024 / vCPU-second |
| CPU, idle min-instance | $0.0000025 / vCPU-second |
| Memory (active and idle) | $0.0000025 / GiB-second |
| Requests | $0.40 / million |
| Free tier, monthly, request-based | 180,000 vCPU-s · 360,000 GiB-s · 2M requests |

### Modelled monthly cost (1 vCPU, 2 GiB, 3 s of billed time per analysis)

| Volume | vCPU-s | GiB-s | Compute | Requests | Total |
|---|---|---|---|---|---|
| 100 analyses | 300 | 600 | $0.00 | $0.00 | **$0.00** |
| 10,000 analyses | 30,000 | 60,000 | $0.00 | $0.00 | **$0.00** |
| 100,000 analyses | 300,000 | 600,000 | $3.48 | $0.00 | **$3.48** |
| 1,000,000 analyses | 3,000,000 | 6,000,000 | $81.78 | $0.00 | **$81.78** |

### Always-on and supporting costs

| Item | Cost |
|---|---|
| Warm instance (`min-instances=1`, 1 vCPU / 2 GiB, idle rate) | **$19.71 / month** |
| Global external load balancer forwarding rule (if Cloud Armor route) | **$18.25 / month** |
| Cloud Armor Standard (1 policy + 1 rule) | **$6.00 / month** + $0.75/M requests |
| Cloudflare rate limiting | Free plan: $0 (1 rule, 10 s window). Pro: paid plan, verify current price |
| Artifact Registry (≈2.5 GiB image, 0.5 GiB free) | **$0.20 / month** |
| Cloud Storage weights (<1 GiB) | cents; verify with the GCS pricing page |
| Response egress | Volume dominates, not rate: at ~150 KiB per annotated response, 100k analyses ≈ 15 GB. Apply the current Premium-tier egress rate to that volume |
| Vercel | **$0** (Hobby) or **$20** (Pro) |

**Expected total for a reviewed, low-traffic deployment: $0.20–$0.50/month on
Cloud Run plus the Vercel plan**, assuming scale-to-zero and the Cloudflare free
tier. The $3.48 and $81.78 rows exist to show what scaling would cost, not as a
forecast.

### Safeguards against unexpected charges (in the order they bite)

1. **Cloud Run `max-instances=3`** — the hard cost ceiling. Fully saturated for 24 hours it costs $7.52; nothing can multiply beyond 3 instances.
2. **Request timeout 120 s** and **concurrency 4** — a stuck request cannot bill indefinitely, and one instance cannot be over-subscribed.
3. **`min-instances=0`** — no idle charge exists to forget about.
4. **Budgets and alerts** on the billing account at $5 / $20 / $50, with email to the owner. A Pub/Sub-triggered Cloud Function can disable billing automatically; recommend alert-only first so a legitimate spike does not take the site down.
5. **Project-level quota** for Cloud Run container instances (e.g. 5) as a second ceiling outside the service config.
6. **Vercel spend management** (Pro): a hard limit that stops usage rather than billing over it.
7. **Edge rate limiting** (§5) so hostile volume is rejected before it reaches a billable instance.
8. **Log-based alert** on 429 rate and 5xx rate; a sudden 429 spike means the limiter is doing its job, a 5xx spike means something else is wrong.
9. **Kill switch** — `gcloud run services update judetector-api --max-instances=0` stops all serving instantly; Vercel rollback or domain removal covers the frontend.

---

## 5. Public API abuse protection beyond per-instance rate limiting

The built-in limiter is per instance and cannot be global (process memory). With
`max-instances=3`, an attacker effectively gets 3 × 30 requests/minute. That is a
shield, not protection. The layers below are cumulative; D5 picks layer 2.

| Layer | Mechanism | Stops | Cost | Notes |
|---|---|---|---|---|
| 0 (present) | 25 MB cap, 40 MP cap, format allowlist, annotated-size cap, per-instance limiter, 120 s timeout | Accidental floods, oversized payloads, malformed files | $0 | Already in the service |
| 1 (present, tuned) | `max-instances=3`, `concurrency=4` | Cost blow-up from parallel work | $0 | A hard ceiling, not a filter |
| 2a (**recommended**) | **Cloudflare** in front of `api.<domain>` — rate limit rule on IP (free plan: 1 rule, 10 s window, e.g. 5 requests / 10 s, mitigation 10 s), plus Bot Fight Mode | Single-source floods, basic bots | $0 (free) / Pro plan for more rules | Needs a Cloud Run domain mapping and the orange-cloud proxy; Cloudflare then sets `X-Forwarded-For`, so `JUDETECTOR_TRUST_PROXY=true` |
| 2b | **Cloud Armor Standard** + global external Application Load Balancer, per-IP rate limit rule | Same as 2a, inside GCP | ≈$24.25/month + $0.75/M requests | GCP-native logging and tuning; heavier setup; LB becomes the public entry point |
| 3 | Turnstile / reCAPTCHA issued by the web app, verified by the API | Scripted clients without a browser | Free tier available | **Requires a contract addition** (a token field or header) — needs approval, out of scope here |
| 4 | Monitoring and alerting | Slow-burn abuse | $0 | 429/5xx rates, p95 latency, instance count |

Deliberately **not** used: Vercel's firewall. It fronts the Vercel deployment, and
detection requests go straight to Cloud Run — a Vercel rule cannot see them. This
is exactly why the transport decision needed to be explicit.

One further lever if abuse becomes expensive: annotated PNGs dominate egress.
`include_annotated=false` by default for anonymous traffic would cut response size
by roughly an order of magnitude. That changes approved product behaviour, so it
is listed as an option, not applied.

---

## 6. Model-weight blocker and the path to real inference

### Current, verifiable state

| Fact | Evidence |
|---|---|
| `models/judah-face-v1/best.pt` does not exist | `git ls-files models/` → `.gitkeep` only; directory empty |
| `torch` / `ultralytics` are not installed | `requirements-model.txt` is not installed in this environment; the container installs `requirements-api.txt` only |
| `/v1/health` reports `degraded`, `model.available=false` | Measured on the running service |
| `/v1/detect` returns `503 model_unavailable` | Measured; no detections in the body |
| Every "result" in tests is a stub or a captured fixture | `tests/conftest.py` `FakeModel`; `web/tests/fixtures/*.json` captured with it |
| No inference figure has ever been measured | `docs/API.md` states this explicitly |

Consequence: a deployment today is honest but does nothing. It shows the
unavailable state on every page. That is correct behaviour, and it is not a
demonstration of the product.

### Steps to demonstrate real inference

1. **Obtain the weights** from the author — the only legitimate source. Record the file size, SHA-256 and the label list next to the file. Do not substitute another checkpoint.
2. Place it at `models/judah-face-v1/best.pt` locally (git-ignored).
3. Install `requirements-model.txt` (CPU torch). Verify the wheel source and pin versions; a CPU-only wheel avoids ~2 GB of CUDA libraries.
4. Start the API locally and confirm, in order: `/v1/health` → `ok`; `/v1/model` → `available: true`, `labels_source: model`; one real `POST /v1/detect` with a known image.
5. **Add the real-model parity test** (marked `slow`, skipped when weights are absent) that runs the same image through `analyse_image` and through the endpoint and compares every box and confidence. The existing parity tests prove the wiring against a stub; this proves it against the model.
6. **Record measured facts** into `metrics/` and the measured table in `docs/API.md`: cold start, model load time, instance RSS, inference p50/p95, response size. Only then may any number appear in the UI or docs.
7. Build the ML image, push to Artifact Registry, deploy with the weights mount, and re-measure on Cloud Run (cold start through FUSE is the number most likely to surprise).
8. Update `/v1/model`'s `metrics` only if an evaluation record exists. It stays `null` otherwise, and the interface says "not measured" rather than showing a made-up figure.

### Risks to state now

- CPU inference latency is unknown; expect hundreds of milliseconds to a few seconds, and do not promise otherwise.
- Cold start with a 539 MB torch wheel plus weights could be 10–30 s. That is why the startup probe allows ~2 minutes and why `min-instances=1` is on the table at $19.71/month.
- ONNX optimisation remains deferred by decision; it would cut memory and latency but must pass a parity test first.

---

## 7. End-to-end acceptance checklist

Run against the deployed pair (Vercel + Cloud Run with weights), and record the
result of each line. Every row has an observable pass condition.

### Upload

| ID | Check | Pass condition |
|---|---|---|
| U1 | PNG / JPG / WEBP / BMP each accepted | `200`, detections or an honest empty result |
| U2 | 25 MB image | accepted; response reports `image.bytes` and any downscale |
| U3 | 26 MB image | refused before upload by the browser; forced past that, `413 payload_too_large` |
| U4 | >40 MP image | `413`, before decode |
| U5 | File renamed `photo.png` but actually GIF | `415`, format read from bytes |
| U6 | Truncated file | `422 invalid_image` |
| U7 | Empty file | refused in the browser with a reason |
| U8 | Drag and drop (desktop) | same result as the file picker |
| U9 | 25 MB over a 5 Mbps link | completes; ~40 s; no timeout |

### Analysis

| ID | Check | Pass condition |
|---|---|---|
| A1 | Nothing analyses on page load or on staging | no network request until the button is pressed |
| A2 | One press = one request | exactly one `POST /v1/detect` in DevTools |
| A3 | Confidence 0.10 vs 0.90 on a known image | count changes in the expected direction |
| A4 | IoU change | count/boxes reflect the new threshold |
| A5 | `include_annotated` off | `annotated: null`, small response, detections intact |
| A6 | Reload mid-session | session cleared, nothing persisted |

### Results and downloads

| ID | Check | Pass condition |
|---|---|---|
| R1 | Boxes align with the subject | at 360, 768, 1024, 1440 px |
| R2 | `count` equals rows shown and boxes drawn | equal |
| R3 | Confidences match the JSON | to 1 decimal place |
| R4 | Timings | inference, server total, browser round trip all > 0 and plausible; `Server-Timing` agrees |
| R5 | Downscaled image | "scaled down before analysis" shown, `image.source_*` larger |
| R6 | Annotated PNG view | renders the service's PNG |
| R7 | Download annotated PNG | opens in an image viewer; `<name>-annotated.png` |
| R8 | Download JSON | valid JSON; same numbers as the screen |

### Errors and unavailable states

| ID | Check | Pass condition |
|---|---|---|
| E1 | Stop the Cloud Run service | "Analysis is unavailable"; no fabricated result |
| E2 | `max-instances` saturated / low limit | `429` copy with a real retry time |
| E3 | Offline network | "could not be reached"; no crash |
| E4 | Every error | shows a reference that matches the server log |
| E5 | Failed re-run after a success | previous result stays visible |

### Browser compatibility

| Browser | Checks |
|---|---|
| Chrome / Edge (Chromium, current) | full flow, downloads, CORS |
| Firefox (current) | full flow; `File` + `FormData`, object URLs |
| Safari 18+ (macOS) | full flow; downloads land in Downloads |
| iOS Safari (iPhone) | upload from Photos, full flow, PNG download (share sheet), no 100vh artefacts |
| Android Chrome | upload from camera roll, full flow |
| No-JavaScript | honest server-rendered shell; no pretence of function |

### Accessibility and performance

| ID | Check | Pass condition |
|---|---|---|
| P1 | Keyboard only | every control reachable, focus visible, order sensible |
| P2 | 200 % zoom / 320 px | no clipping, no horizontal scroll |
| P3 | Screen reader (VoiceOver / NVDA) | uploader labelled, errors announced, results readable |
| P4 | Contrast | no regression from the measured values in §1 |
| P5 | LCP on Fast 4G | under 2.5 s for the shell (187 KiB gzipped JS) |
| P6 | Privacy | no third-party requests, no storage writes |

### Regression

| ID | Check | Pass condition |
|---|---|---|
| G1 | Streamlit prototype | still runs and analyses identically |
| G2 | Python suite | 298 passed |
| G3 | Web suite | 61 passed |
| G4 | Contract fixtures | still match the published OpenAPI schema |
| G5 | Cache headers | every API response `no-store` |

---

## 8. Rollback procedure

No database, no stored images and no user accounts exist, so rollback is purely a
traffic and artefact operation. Both sides are independent.

### Frontend (Vercel)

1. **Instant rollback**: Project → Deployments → pick the last known-good production deployment → **Rollback** (Promote). Traffic switches in seconds; the previous build is immutable and already cached.
2. **CLI alternative**: `vercel rollback <deployment-url>` (confirm the CLI version supports it; the dashboard path always works).
3. **Code-level**: `git revert <merge-commit>` on the production branch and let CI redeploy. Use this when the fault is in code that must not simply be re-pinned.
4. **Environment fault** (e.g. wrong `NEXT_PUBLIC_API_BASE_URL`): correct the variable and redeploy — a build is required because `NEXT_PUBLIC_*` is inlined.
5. **Total outage switch**: remove the production domain from the project, or roll back to the last deployment that predates the API integration.

### Inference backend (Cloud Run)

1. **Traffic split to the previous revision** — instant, no rebuild:
   `gcloud run services update-traffic judetector-api --region us-central1 --to-revisions=<previous-revision>=100`
2. **Redeploy a pinned digest** if the revision was deleted:
   `gcloud run deploy judetector-api --image .../api@sha256:<known-good> --region us-central1`
3. **Bad weights** (weights load but produce nonsense): roll the FUSE mount's bucket path back to the previous object version, or point `JUDETECTOR_MODEL_PATH` at the previous file and deploy a revision. Model rollback never requires an image change.
4. **Config fault** (CORS, rate limit, proxy trust): change the environment variable on the service and deploy a revision; keep the previous revision available for the split.
5. **Emergency stop**: `gcloud run services update judetector-api --region us-central1 --max-instances=0` — the service immediately stops serving while remaining configured.
6. **Edge**: disable the Cloudflare rate-limit rule (or the Cloud Armor policy) if it is blocking legitimate traffic; both are one toggle and take effect within seconds.
7. **DNS**: Cloudflare/LB records are the last resort — repoint to a maintenance page.

### Verification after any rollback

- `/v1/health` returns the expected `ok`/`degraded`.
- One real analysis end to end from the deployed frontend.
- `access-control-allow-origin` is the production origin, not a preview.
- One 429 and one 503 still render as readable problems.
- CI is green on the branch that production now matches.

### What rollback cannot fix

Weights that are wrong for the subject, or an evaluation record that is inaccurate.
Those need data, not deployment, action.

---

## 9. What this report does not authorise

Nothing in this document has been executed. Explicit approval is still required
for: merging PR #3, creating the Vercel project, enabling GCP billing, creating
buckets or service accounts, building and pushing images, deploying Cloud Run,
purchasing any paid plan, and adding an edge proxy.
