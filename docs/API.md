# JUDEtector inference API

FastAPI service over the **unchanged** detection engine (`app/core`,
`app/components/pipeline.py`). It exists so a web client, and later a mobile
client, can run the same detection the Streamlit prototype runs.

**Stage 0 status:** service contract only — `GET /v1/health` and `GET /v1/model`.
`POST /v1/detect` arrives in Stage 1, behind upload validation, rate limiting and
the same explicit-action rule the prototype uses.

## Run it

```bash
pip install -r requirements-dev.txt      # app + API + tests
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
| `JUDETECTOR_MAX_UPLOAD_MB` | `25` | upload cap (enforced from Stage 1) |
| `JUDETECTOR_MAX_IMAGE_DIMENSION` | `4000` | longest side after downscale |
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
| 413 | `payload_too_large` | upload above the cap *(Stage 1)* |
| 415 | `unsupported_media_type` | not JPG/PNG/WEBP/BMP *(Stage 1)* |
| 422 | `invalid_request` | invalid parameter |
| 422 | `invalid_image` | file could not be decoded *(Stage 1)* |
| 429 | `rate_limited` | client quota exceeded *(Stage 1)* |
| 500 | `internal_error` | unhandled failure, internals masked |
| 500 | `inference_failed` | model raised during inference *(Stage 1)* |
| 503 | `model_unavailable` | weights or ML stack missing |

Details never contain filesystem paths, dependency names, registry keys or
stack traces. Correlate with the server log using `request_id`.

## Response headers

Every response carries `X-Request-Id` (echoed when the caller supplies a valid
one), `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`. Stage 1
adds `Server-Timing: inference;dur=…, total;dur=…` on `/v1/detect`.

## Privacy

Images are decoded and analysed in memory. Nothing is written to disk, no
request body is logged, and there is no history endpoint. `/v1/detect` will
return the annotated PNG inline rather than storing it.

## Measured on this machine (no ML stack, no weights)

| Metric | Value |
|---|---|
| `import api.main` | 298 ms, 43 MiB peak RSS |
| uvicorn → first `200` on `/v1/health` | 0.43 s |
| `/v1/health` latency | p50 1.25 ms, p95 1.75 ms |
| uvicorn RSS after boot | 48.8 MiB |

Model-load time, inference latency and peak memory **cannot** be measured until
`torch`, `ultralytics` and the author's weights are present; Stage 1 records them
rather than estimating them.
