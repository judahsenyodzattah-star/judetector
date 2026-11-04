# JUDEtector inference API

FastAPI service over the **unchanged** detection engine (`app/core`,
`app/components/pipeline.py`). It exists so a web client, and later a mobile
client, can run the same detection the Streamlit prototype runs.

**Stage 1 status:** `GET /v1/health`, `GET /v1/model` and `POST /v1/detect`.
`/v1/detect` runs `analyse_image` untouched, behind upload validation, a
per-instance rate limiter and the same explicit-action rule the prototype uses.

## Run it

```bash
pip install -r requirements-dev.txt      # app + API + tests
pip install -r requirements-model.txt    # torch + ultralytics (only for real inference)
uvicorn api.main:app --reload --port 8000
curl -s localhost:8000/v1/health | python -m json.tool
```

Container:

```bash
docker build -t judetector-api .
docker run --rm -p 8080:8080 \
  -v /path/to/models:/models:ro \
  -e JUDETECTOR_MODEL_PATH=/models/best.pt \
  judetector-api
```

Weights are never baked into the image. Without them the service starts
normally and reports `degraded` — an honest unavailable state, not a crash and
never a fabricated result.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `JUDETECTOR_ENV` | `development` | `production` disables `/docs` |
| `JUDETECTOR_REGISTRY` | `config/models.json` | model registry path |
| `JUDETECTOR_MODEL_PATH` | — | absolute weights override for the default model |
| `JUDETECTOR_CORS_ORIGINS` | *(empty)* | comma-separated origin allowlist; empty means no cross-origin access |
| `JUDETECTOR_MAX_UPLOAD_MB` | `25` | upload cap, enforced while streaming |
| `JUDETECTOR_MAX_IMAGE_DIMENSION` | `4000` | longest side after downscale |
| `JUDETECTOR_MAX_PIXELS` | `40000000` | decoded-pixel budget, checked before decoding |
| `JUDETECTOR_MAX_ANNOTATED_BYTES` | `6291456` | annotated PNG cap (6 MiB) before it is returned |
| `JUDETECTOR_RATE_LIMIT_PER_MINUTE` | `30` | requests per client per minute, per instance |
| `JUDETECTOR_RATE_LIMIT_BACKEND` | `memory` | `memory` or `none` (edge-enforced) |
| `JUDETECTOR_TRUST_PROXY` | `false` | trust `X-Forwarded-For` for the client key |
| `PORT` | `8080` | bind port in the container |

## `GET /v1/health`

Liveness plus honest model state.

```json
{"status":"degraded","service":"judetector-api","version":"0.1.0",
 "uptime_s":0.119,"model":{"id":"judah-face-v1","available":false,"loaded":false}}
```

- `status` is `ok` only when weights exist and the service could analyse an
  image; `degraded` means it is running but inference is unavailable. The HTTP
  status is `200` in both cases, so it works as a liveness probe; orchestrators
  that need readiness should read the body.
- `model` is `null` when no model is configured.
- `available` is *weights on disk*; `loaded` is *in memory and able to predict*.

## `GET /v1/model`

The public model card. It exists so no client can present this detector as
something it is not.

```json
{"id":"judah-face-v1","display_name":"JUDEtector — judah model (v1)",
 "kind":"subject_specific","task":"detect","labels":["judah"],
 "labels_source":"declared","available":false,
 "limitations":"Single-subject detector trained on one person. …",
 "metrics":null}
```

- `kind` distinguishes a subject-specific detector from a general-purpose one.
- `labels_source` is `model` only once labels were read from loaded weights;
  otherwise `declared` (registry) or `unknown`.
- `limitations` is derived from the registry and always states that detection is
  not recognition.
- `metrics` is the recorded evaluation record **verbatim**, or `null`. The
  service never estimates, rounds or back-fills a metric.

`503 model_unavailable` when no model is configured.

## `POST /v1/detect`

`multipart/form-data`, one image, explicit per request — nothing runs in the
background and nothing is inferred from a webcam or a stream.

| Field | Type | Default | Notes |
|---|---|---|---|
| `file` | file | required | JPG, PNG, WEBP or BMP |
| `confidence` | float | `0.25` | `0.01`–`0.99` |
| `iou` | float | `0.45` | `0.10`–`0.95` |
| `include_annotated` | bool | `true` | inline base64 annotated PNG |

```bash
curl -s -X POST localhost:8000/v1/detect \
  -F file=@photo.jpg -F confidence=0.25 -F iou=0.45 \
  | python -m json.tool
```

Response (`200`):

```json
{
  "request_id": "9f2c…",
  "model": {"id":"judah-face-v1","display_name":"…","kind":"subject_specific",
            "labels":["judah"],"labels_source":"declared"},
  "image": {"width":4000,"height":3000,"source_width":6000,"source_height":4500,
            "downscaled":true,"bytes":1843200,"megapixels":12.0},
  "thresholds": {"confidence":0.25,"iou":0.45},
  "count": 2,
  "detections": [
    {"label":"judah","confidence":0.9134,
     "box":{"x1":812.0,"y1":404.5,"x2":1673.2,"y2":1402.9},
     "box_norm":{"x1":0.203,"y1":0.1348,"x2":0.4183,"y2":0.4676}}
  ],
  "timing": {"inference_ms":41.2,"total_ms":268.7},
  "annotated": {"mime":"image/png","encoding":"base64","width":4000,"height":3000,
                "bytes":98213,"data":"iVBORw0KGgo…"},
  "warnings": []
}
```

- **Boxes** are pixels in the *analysed* image (`image.width` × `image.height`,
  after downscale) — never the original. `image.source_*` carries the original
  size so a client can scale back.
- **`box_norm`** is the same box divided by the analysed extent, rounded to six
  decimals and clamped to `[0, 1]`. It is derived, not a second measurement.
- **`confidence`** per detection is the detector's score for that box, rounded
  to four decimals. There is no aggregate "accuracy" anywhere.
- **`count`** equals `len(detections)`; it is never a separate estimate.
- **`timing.inference_ms`** is the figure the pipeline measured around the
  model call. **`timing.total_ms`** is measured by the API around the whole
  request (decode, inference, annotation). Neither is estimated.
- **`annotated`** is the same PNG the prototype draws, returned inline as
  base64. If it would exceed `JUDETECTOR_MAX_ANNOTATED_BYTES`, the field is
  `null` and a warning explains why — detections are never dropped for it.
  Send `include_annotated=false` when only numbers are needed.
- **`warnings`** carries plain-language notes (for example an oversized
  annotation, or a downscaled image). It is empty rather than padded.

### Validation, in order

1. `Content-Length` above the upload cap plus multipart overhead → `413`
   before any parsing.
2. Body streamed in 64 KiB chunks; crossing 25 MB → `413` and the upload is
   abandoned.
3. The detected PIL format must be JPG/PNG/WEBP/BMP → `415`. The filename and
   the client-sent content type are ignored.
4. `width × height` above 40 MP → `413` from the header probe, before pixels
   are decoded.
5. Corrupt, truncated or empty image → `422 invalid_image`.
6. Then decode, downscale to 4000 px on the longest side, and run the pipeline.

`503 model_unavailable` is returned when weights are absent or the model cannot
load, and it contains no detections, confidences or paths — a client must not be
able to mistake "unavailable" for "nothing found".

## Rate limiting

Defaults: 30 requests per minute, per client IP.

**The built-in limiter is per instance.** `InProcessRateLimiter` keeps a sliding
window in this process's memory. Cloud Run may run several instances and may
start new ones at any time, so with more than one instance a client's effective
quota is *N × 30* and counters reset when instances recycle. It is a coarse
shield against a single runaway client, not global protection.

Global protection needs a dependency this service does not provide:

- an **edge** limiter in front of the service — Cloud Armor rate-limiting rules,
  API Gateway quotas, or a CDN/WAF such as Cloudflare; or
- a shared counter store such as Redis or Memorystore, which would be a new
  dependency and a new failure mode.

Set `JUDETECTOR_RATE_LIMIT_BACKEND=none` when the edge already enforces a quota,
so the responses are not throttled twice. The scope is reported honestly on
every response:

```
RateLimit-Limit: 30
RateLimit-Remaining: 28
RateLimit-Reset: 41
RateLimit-Scope: instance      # "none" when the built-in limiter is disabled
```

On `429` the body is a problem document and `Retry-After` gives the seconds
until the window frees. Health and model-card requests are never limited, so
orchestrators and monitors are unaffected.

The client key is the socket peer address. `X-Forwarded-For` is honoured **only**
when `JUDETECTOR_TRUST_PROXY=true`; trusting it by default would let any caller
pick their own key and evade the limit.

## Errors

Every error is `application/problem+json`:

```json
{"type":"invalid_image","title":"Image could not be read",
 "status":422,"detail":"…","request_id":"9f2c…"}
```

| Status | `type` | Meaning |
|---|---|---|
| 404 | `not_found` | no such route |
| 405 | `method_not_allowed` | wrong method |
| 413 | `payload_too_large` | upload above the cap, or above the pixel budget |
| 415 | `unsupported_media_type` | not JPG/PNG/WEBP/BMP |
| 422 | `invalid_request` | invalid parameter |
| 422 | `invalid_image` | file could not be decoded |
| 429 | `rate_limited` | client quota exceeded, with `Retry-After` |
| 500 | `internal_error` | unhandled failure, internals masked |
| 500 | `inference_failed` | model raised during inference, details masked |
| 503 | `model_unavailable` | weights or ML stack missing |

Details never contain filesystem paths, dependency names, registry keys or
stack traces. Correlate with the server log using `request_id`.

## Response headers

Every response carries `X-Request-Id` (echoed when the caller supplies a valid
one), `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`.
`/v1/detect` adds `Server-Timing: inference;dur=41.2, total;dur=268.7` and the
`RateLimit-*` headers above.

## Privacy

Images are decoded, analysed and annotated in memory. Nothing is written to
disk, no request body is logged, and there is no history endpoint. The annotated
PNG is returned inline rather than stored.

## Cross-origin access (CORS)

The web app calls this service directly from the browser for `POST /v1/detect`
(Vercel cannot carry a 25 MB upload through a Function). Cross-origin behaviour
is therefore part of the contract:

- Origins come from `JUDETECTOR_CORS_ORIGINS`, comma-separated and matched
  exactly. Empty — the default — means **no** cross-origin access.
- A `multipart/form-data` POST with no custom headers is CORS-simple: no
  preflight, one request.
- Preflights are answered for `POST` with `content-type` and `x-request-id`
  allowed, `max-age=600`. Any other requested header is refused with `400`, so
  adding an `authorization` header later is an explicit change here.
- `Access-Control-Expose-Headers` lists `X-Request-Id`, `Server-Timing`,
  `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`,
  `RateLimit-Scope` and `Retry-After`, so a browser can read timings, the quota
  and the retry hint — including on `413`, `415`, `422`, `429` and `503`.

**CORS is not authorisation.** It only stops other web pages from reading
responses. This endpoint is public and unauthenticated: any script can call it.
The safeguards that actually apply are the upload caps, the pixel budget, the
format allowlist, the annotated-size cap and the per-instance rate limiter
described above. Global rate limiting belongs at the edge (Cloud Armor, API
Gateway, Cloudflare) or in a shared store. The full pre-exposure checklist is in
[`docs/WEB.md`](WEB.md#before-this-endpoint-is-exposed-publicly).

## Measured on this machine

Stage 0, no ML stack and no weights:

| Metric | Value |
|---|---|
| `import api.main` | 298 ms, 43 MiB peak RSS |
| uvicorn → first `200` on `/v1/health` | 0.43 s |
| `/v1/health` latency | p50 1.25 ms, p95 1.75 ms |
| uvicorn RSS after boot | 48.8 MiB |

Stage 1 service overhead, in-process test client with a stub detector that
reports 0.01 ms of inference — so these numbers are validation, annotation and
HTTP work only:

| Request | p50 | p95 | Response |
|---|---|---|---|
| 320 × 240 PNG, annotated | 11 ms | 12 ms | 4 KiB |
| 4000 × 3000 PNG, annotated | 357 ms | 410 ms | 74 KiB |
| 4000 × 3000 PNG, `include_annotated=false` | 118 ms | 122 ms | 1 KiB |

Model-load time, real inference latency and peak memory **cannot** be measured
until `torch`, `ultralytics` and the author's weights are present. The same stub
records 0.01 ms, which is why the table above is labelled *overhead* and not
*performance*. Real figures will be recorded, never estimated.
