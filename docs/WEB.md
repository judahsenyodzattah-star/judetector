# JUDEtector web app

Next.js (App Router) + React + TypeScript frontend for the JUDEtector inference
API. It replaces the Streamlit interface as the public surface while the
prototype in `app/` stays untouched and runnable.

```
web/
  app/            routes: /, /detect, /camera, /help, /api/detect (proxy)
  components/     uploader, session panel, overlay, results, notices, nav
  lib/            API client, session state, formatting, limits, breakpoints
  tests/          61 Vitest + Testing Library tests, plus captured API fixtures
```

## The upload size question, answered first

The approved contract accepts images up to **25 MB**. Vercel's limits were
checked against that number before any transport was written, on 2026-11-04:

| Platform | Limit | Can it be raised? | Source |
|---|---|---|---|
| Vercel Functions (Node.js) request body | **4.5 MB** | No — infrastructure-level, returns `413 FUNCTION_PAYLOAD_TOO_LARGE` | Vercel, *Functions limits* |
| Cloud Run, HTTP/1 request body | 32 MiB | No (no limit when the container serves HTTP/2) | Google Cloud, *Cloud Run quotas and limits* |
| Next.js dev server (local) | none | — | — |

So a Next.js Route Handler on Vercel **cannot** carry a 25 MB upload. It is not
a configuration problem: the platform refuses the body before the function runs.
Cloud Run, by contrast, admits the full request (25 MB plus ~256 KiB of
multipart framing is well inside 32 MiB).

**Decision (approved 2026-11-04): send the image directly from the browser to
the API for analysis.**

- The UI is still served by Vercel; the read-only endpoints (`/v1/health`,
  `/v1/model`, a few hundred bytes) are fetched server-side, so the page can
  render an honest model state with no client round trip.
- `POST /v1/detect` goes from the browser to the API origin with CORS. A
  `multipart/form-data` POST with no custom headers is a CORS-simple request, so
  there is no preflight — one request, 25 MB, unchanged.
- The API already supports this; a deployment sets `JUDETECTOR_CORS_ORIGINS` to
  the exact web origin(s) — no wildcard. Exposing `RateLimit-*` and `Retry-After`
  in `Access-Control-Expose-Headers` is the only API-side addition, and it
  changes no response field.
- The same-origin proxy at `/api/detect` is kept for **local development only**.
  It is not part of the production path and it is not a fallback.

Nothing in this stage reduces the 25 MB limit. The alternatives were considered
and rejected: a proxy cannot work (above), lowering the limit silently was not
allowed, and object-storage upload would change the API contract and add a
storage dependency the approved design does not have.

`NEXT_PUBLIC_API_BASE_URL` is unset in local development, where the same-origin
proxy at `/api/detect` is used and the 4.5 MB limit does not exist. That proxy
refuses an over-limit body **explicitly** on Vercel (`upload_over_proxy_limit`)
rather than letting the platform fail opaquely.

## CORS: verified, and what it is not

Approved transport, checked against a live server and encoded in
`tests/test_api_cors.py` (11 tests) and `web/tests/transport.test.ts` (6 tests):

| Property | Verified behaviour |
|---|---|
| Simple request | `multipart/form-data` POST with no custom headers is CORS-simple: **no preflight**, one request, 25 MB intact |
| Preflight, if one ever happens | `OPTIONS /v1/detect` answers `200` with the exact origin, `POST` allowed, `content-type` allowed, `max-age=600` |
| Unknown request headers | `400`; the advertised allow-list never names `authorization`, so adding auth later is a deliberate configuration change |
| Error responses | `413`, `415`, `422`, `429` and `503` all carry `Access-Control-Allow-Origin` **and** expose `RateLimit-*` and `Retry-After`, so a browser can read the reason instead of seeing an opaque failure |
| Unlisted origin | No `Access-Control-Allow-Origin` header at all |
| Non-browser client | Served normally — **CORS never protected the endpoint** |

**CORS is not an authorisation mechanism.** It stops *other web pages* from
reading responses from your origin. It does nothing against `curl`, a script, a
scraper or a native app, and it must never be described as access control. The
endpoint is public and unauthenticated by design; the protections that matter
are listed below.

## Before this endpoint is exposed publicly

Present today and unchanged by this stage:

- Upload cap enforced twice — from `Content-Length` before parsing and while
  streaming (25 MB), plus a 40-megapixel budget checked before decode.
- Detected-format allowlist (JPG/PNG/WEBP/BMP); the filename is ignored.
- Annotated PNG size cap, so no response can balloon.
- A per-instance rate limiter (default 30/min) with honest `RateLimit-Scope`.
- No request bodies logged, no storage, no history.

Still required before the endpoint is genuinely public — **none of it is done
yet**, and Stage 3 is where it belongs:

1. **Global rate limiting at the edge** — Cloud Armor rate-limit rules, API
   Gateway quotas or Cloudflare. The in-process limiter is per instance, so with
   N replicas a client gets N times the quota.
2. **Instance and concurrency ceilings** on Cloud Run (max instances, request
   timeout), so a burst cannot fan out without bound.
3. **Alerting** on 5xx rate, 429 rate and request latency.
4. **Budget guardrails** — Cloud Run max instances plus a billing alert.
5. **Ingress restriction** where possible: allow only the edge/proxy path, keep
   the service URL out of client code if a stable custom domain is used.
6. **A decision on authentication** before any non-public use; if one is added,
   `Access-Control-Allow-Headers` must be extended deliberately and the origin
   list kept exact.
7. **Abuse review** of the anonymous endpoint: image uploads are the expensive
   operation, so the cost of a hostile client should be estimated and capped
   before launch.

## Configuration

| Variable | Where | Meaning |
|---|---|---|
| `API_INTERNAL_URL` | server | Base URL used by the Next.js server for health and model card (default `http://127.0.0.1:8000`) |
| `NEXT_PUBLIC_API_BASE_URL` | build + browser | Public API origin. Setting it switches detection to the direct transport |
| `NEXT_PUBLIC_DETECT_TRANSPORT` | build + browser | `direct` or `proxy`; overrides the automatic choice (proxy is for local development) |
| `JUDETECTOR_CORS_ORIGINS` | API deployment | exact web origin(s), comma-separated; empty means no cross-origin access |

## Run it

```bash
# terminal 1 — the API (no weights installed is fine; it reports degraded)
source ../.venv/bin/activate && uvicorn api.main:app --port 8000

# terminal 2 — the web app
cd web && npm install && npm run dev     # http://localhost:3000
```

Scripts: `npm run dev`, `npm run build`, `npm start`, `npm run typecheck`,
`npm test`.

## Design system

One file, `app/globals.css`, with tokens at the top. Dark rail, paper workspace,
one ochre accent; no gradients, no decorative illustration, no stock imagery.

| Pair | Ratio | Use |
|---|---|---|
| `#191C1B` on `#F7F5F0` | 15.8:1 | body text |
| `#565B58` on `#F7F5F0` | 6.4:1 | secondary text |
| `#6F7572` on `#FFFFFF` | 4.7:1 | captions and labels |
| `#CBD0CC` on `#1E2122` | 10.4:1 | rail navigation |
| `#C8963E` on `#1E2122` | 6.1:1 | rail accent, status dot |
| `#FFFDF8` on `#8F6722` | 5.0:1 | primary button label |
| `#6F5215` on `#F7F5F0` | 6.7:1 | links on paper |
| `#9A352C` on `#F7E7E4` | 6.0:1 | error text |
| `#37624A` on `#E6EFE8` | 5.9:1 | success text |

Typography: system sans stack, a seven-step scale (13 → 36 px), tabular numerals
for every measured value. Spacing: 4 px base, 1.5 rem gutter. Icons: one
hand-authored 20 px set in `components/icons.tsx` — no icon dependency.

Focus is always visible (`:focus-visible` ring, 4.7:1 against paper), motion is
removed under `prefers-reduced-motion`, and the uploader input is a real,
labelled file input rather than a click-only div.

## Layout

- **Desktop (≥1024 px)** — fixed rail (248 px) with navigation, model status and
  privacy note; content column capped at 1120 px. Home and Detect are a
  1fr / 320 px split.
- **Tablet (640–1023 px)** — rail becomes a top bar with the same four
  destinations; the split collapses to one column.
- **Mobile (<640 px)** — single column, tighter gutters, detection rows reflow,
  definition lists stack.

The rail/top bar swap is decided by a `matchMedia` hook so each breakpoint gets
exactly one navigation element; the CSS ranges are mutually exclusive and are
asserted in `tests/guardrails.test.ts`.

## What the screens do

**Home** — one dominant uploader, a compact session panel, a single understated
workflow line, the model's limitations and its availability. Choosing a file
stages it and moves to Detect; it does not analyse anything.

**Detect** — the staged image with a client-drawn overlay, confidence and IoU
thresholds, and one explicit **Analyse image** button. After a run: the count,
per-detection confidences and pixel boxes, model inference time, the server's
total, the browser round trip, the service's annotated PNG (view and download),
the detections as JSON, what was analysed (including any downscale) and the
request reference.

**Camera** — a deliberate, honest empty state: live capture is not in this
build, it is the next stage, and the page shows no simulated viewfinder.

**Help** — what the app does and refuses to do, file limits, how to read a
result, what each error means, and the privacy model.

## Errors, as the visitor sees them

| API problem | What the interface says |
|---|---|
| `model_unavailable` | "Analysis is unavailable" — the service is up but the model is not loaded; nothing is invented to fill the gap |
| `rate_limited` | "Too many analyses in a short time", with the seconds from `Retry-After` |
| `payload_too_large` | "That image is too large", with the 25 MB / 40 MP limits |
| `unsupported_media_type` | "That file type is not supported", listing the four accepted formats |
| `invalid_image` | "That image could not be read" and a damaged-file explanation |
| `inference_failed`, `internal_error` | "The analysis failed" and a reference to quote |
| network failure | "The analysis service could not be reached" |

Every error keeps the service's `request_id`, and a failed re-run leaves the
previous successful result on screen rather than blanking it.

## Privacy

Images live in React state and object URLs. There is no browser storage, no
cookie, no server-side session, no database and no analytics. Staging a second
image revokes the previous object URL. Reloading clears everything — by design,
not as a gap. `tests/guardrails.test.ts` fails if `localStorage`,
`sessionStorage` or `indexedDB` ever appears in `app/`, `components/` or `lib/`.

## Tests

```bash
cd web && npm test          # 61 tests, 8 files
npm run typecheck           # tsc --noEmit
npm run build               # production build
```

Covered: image selection and refusals (type, size, empty), drag and drop, the
explicit-only analysis rule, threshold changes not re-running anything, results
(count, confidences, timings, overlay boxes), annotated PNG and JSON downloads,
all seven error states, model-unavailable and status-unknown behaviour,
navigation and active states at three breakpoints, session memory and its
release semantics, no-storage and no-fabrication guards, and the required
breakpoints in the stylesheet.

`web/tests/transport.test.ts` pins the approved transport: with an API origin
configured, detection addresses `…/v1/detect` and never `/api/detect`, adds no
header that could force a preflight, and the proxy stays reachable only when no
origin is set.

`web/tests/fixtures/*.json` are real responses captured from the API; the Python
suite (`tests/test_web_contract.py`) asserts they still match the published
OpenAPI schema and that `web/lib/limits.ts` keeps the API's 25 MB cap.

## Not in this stage

Camera capture, deployment, and any request that leaves the visitor's browser
without an explicit action. Vercel project setup and the CORS origin value are
Stage 3 work; the transport decision above is a prerequisite for it.
